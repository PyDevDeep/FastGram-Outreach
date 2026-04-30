import asyncio
from datetime import UTC, datetime, timedelta
from typing import Any

from instagrapi.exceptions import (  # type: ignore[reportMissingTypeStubs]
    ChallengeRequired,
    LoginRequired,
)

from app.config import get_settings
from app.repositories.lead_repository import LeadRepository
from app.services.instagram_client import InstagramClient
from app.services.notification_service import NotificationService
from app.services.pause_manager import PauseManager
from app.services.proxy_rotator import ProxyRotator
from app.services.sheets_client import GoogleSheetsClient
from app.services.warmup_manager import WarmupManager
from app.utils.delay import random_delay, typing_simulation_delay
from app.utils.logger import setup_logger

logger = setup_logger("outreach_engine")


class OutreachEngine:
    def __init__(
        self,
        instagram_client: InstagramClient,
        sheets_client: GoogleSheetsClient,
        lead_repository: LeadRepository,
        warmup_manager: WarmupManager,
        proxy_rotator: ProxyRotator,
        pause_manager: PauseManager,
        notification_service: NotificationService,
    ) -> None:
        self.instagram_client = instagram_client
        self.sheets_client = sheets_client
        self.lead_repository = lead_repository
        self.warmup_manager = warmup_manager
        self.proxy_rotator = proxy_rotator
        self.pause_manager = pause_manager
        self.notification_service = notification_service
        self.settings = get_settings()
        self._state = "idle"
        self.sent_today = 0
        self._current_date = datetime.now(UTC).date()
        # ДОДАНО: Event для правильного очікування замість sleep
        self._resume_event = asyncio.Event()
        self._resume_event.set()

    @property
    def state(self) -> str:
        return self._state

    @state.setter
    def state(self, value: str) -> None:
        valid_states = ["idle", "running", "paused", "blocked", "stopping"]
        if value in valid_states:
            logger.info(f"Engine state changed: {self._state} -> {value}")
            self._state = value
            if value == "paused":
                self._resume_event.clear()
            else:
                self._resume_event.set()
        else:
            logger.error(f"Attempted to set invalid state: {value}")

    async def generate_delay(self, min_sec: int, max_sec: int) -> float:
        return await random_delay(min_sec, max_sec)

    def calculate_batch_estimates(self, requested_batch_size: int | None = None) -> tuple[int, str]:
        limit = requested_batch_size or self.settings.daily_message_limit
        avg_delay = (self.settings.min_delay_seconds + self.settings.max_delay_seconds) / 2
        est_seconds = limit * (avg_delay + 5)  # +5s typing simulation
        est_completion = (datetime.now(UTC) + timedelta(seconds=est_seconds)).isoformat()
        return limit, est_completion

    async def _handle_account_block(
        self, reason: str, row_index: int, timestamp: str, sent_count: int, username: str
    ) -> int:
        self.state = "blocked"
        self.pause_manager.trigger_pause(reason)
        await self.sheets_client.update_contact_status(row_index, "Failed", timestamp)
        await self.notification_service.send_block_alert(reason, sent_count, username)
        return 1

    async def run_batch(
        self, batch_size: int | None = None, dry_run: bool = False
    ) -> dict[str, Any]:
        """Обробка черги повідомлень із затримками, лімітами та обробкою помилок."""
        if self.state != "idle":
            logger.warning(f"Cannot start new batch. Engine is currently in '{self.state}' state.")
            return {"sent": 0, "failed": 0, "remaining": 0, "state": self.state}

        # --- ДОДАНО: Перевірка 24-годинної паузи ---
        if self.pause_manager.is_paused():
            rem_time = self.pause_manager.get_remaining_pause_time()
            logger.warning(
                f"Cannot start batch. System is paused for {rem_time} due to previous block."
            )
            return {
                "sent": 0,
                "failed": 0,
                "remaining": 0,
                "state": "paused",
                "message": f"Paused. Resume in {rem_time}",
            }
        # ------------------------------------------

        self.state = "running"

        # --- ДОДАНО: Завантаження сесії перед будь-якими діями ---
        logger.info("Verifying Instagram session before batch...")
        if not await self.instagram_client.login():
            logger.critical("Failed to load session or login. Halting batch.")
            self.state = "blocked"
            return {"sent": 0, "failed": 0, "remaining": 0, "state": "blocked"}
        # ----------------------------------------------------------

        # 1. PROXY ROTATION CHECK
        if not dry_run and self.proxy_rotator.is_rotation_needed():
            logger.info("Initiating proxy rotation before batch...")
            new_proxy = await self.proxy_rotator.request_new_ip()

            if new_proxy:
                old_proxy = getattr(self.instagram_client, "proxy", "default/unknown")
                success = await self.proxy_rotator.update_instagram_session_proxy(
                    self.instagram_client, new_proxy
                )
                if success:
                    logger.info(f"Proxy IP rotated: {old_proxy} -> {new_proxy}")
                else:
                    logger.warning("Proxy validation failed. Continuing with previous IP.")
            else:
                logger.warning(
                    "Failed to obtain new Proxy IP from provider. Continuing with current IP."
                )
        limit = batch_size or self.settings.daily_message_limit

        pending_contacts = await self.sheets_client.get_pending_contacts()
        logger.info(f"Fetched {len(pending_contacts)} pending contacts. Dry run: {dry_run}")

        sent_count = 0
        failed_count = 0

        for contact in pending_contacts:
            await self._resume_event.wait()

            if self.state in ("blocked", "stopping"):  # type: ignore[reportUnnecessaryContains]
                logger.warning(f"Engine is {self.state.upper()}. Halting batch processing.")
                break
            # 2. Перевірка зміни доби та лімітів
            today = datetime.now(UTC).date()
            if today > self._current_date:
                logger.info("New UTC day detected. Resetting daily sent counter.")
                self.sent_today = 0
                self._current_date = today

            if self.sent_today >= limit:
                logger.warning(f"Daily message limit reached ({limit}). Halting batch.")
                break

            row_index = contact.get("_row_index")
            username = contact.get("Instagram Username")
            user_id = contact.get("Instagram User ID")
            message = contact.get("Message Template")

            if row_index is None or not user_id or not message:
                logger.error(f"Missing critical data for {username}. Skipping.")
                failed_count += 1
                continue

            logger.info(f"Processing contact: {username} (ID: {user_id})")

            # 3. Human-like затримки
            await self.generate_delay(
                self.settings.min_delay_seconds, self.settings.max_delay_seconds
            )
            await typing_simulation_delay(len(str(message)))

            timestamp = datetime.now(UTC).isoformat()

            # 4. Dry Run
            if dry_run:
                logger.info(f"[DRY RUN] Simulating send to {username}")
                await self.sheets_client.update_contact_status(int(row_index), "Sent", timestamp)
                sent_count += 1
                self.sent_today += 1
                continue

            # 5. Реальна відправка та Error Handling
            try:
                success = await self.instagram_client.send_direct_message(
                    str(user_id), str(message)
                )

                if success:
                    await self.sheets_client.update_contact_status(
                        int(row_index), "Sent", timestamp
                    )
                    sent_count += 1
                    self.sent_today += 1
                    self.proxy_rotator.increment_message_count()
                else:
                    await self.sheets_client.update_contact_status(
                        int(row_index), "Failed", timestamp
                    )
                    failed_count += 1

            except ChallengeRequired as e:
                logger.critical(f"Challenge Required triggered by {username}: {e}")
                failed_count += await self._handle_account_block(
                    "ChallengeRequired", int(row_index), timestamp, sent_count, str(username)
                )
                break

            except LoginRequired as e:
                logger.warning(f"Session expired/invalidated: {e}. Attempting re-login...")
                if await self.instagram_client.login():
                    logger.info(
                        "Re-login successful. State remains running. Moving to next contact."
                    )
                    await self.sheets_client.update_contact_status(
                        int(row_index), "Failed", timestamp
                    )
                    failed_count += 1
                else:
                    logger.critical("Re-login failed. Blocking engine.")
                    failed_count += await self._handle_account_block(
                        "LoginRequired (Re-login failed)",
                        int(row_index),
                        timestamp,
                        sent_count,
                        str(username),
                    )
                    break

            except Exception as e:
                error_msg = str(e).lower()

                # --- ЖОРСТКИЙ ПАРСИНГ ТЕКСТУ ПОМИЛКИ ---
                if (
                    "login required" in error_msg
                    or "challenge required" in error_msg
                    or "blocked" in error_msg
                    or "checkpoint_required" in error_msg
                ):
                    logger.critical(
                        f"Critical error hidden in generic Exception for {username}: {e}"
                    )
                    failed_count += await self._handle_account_block(
                        f"HiddenAuthError: {e}",
                        int(row_index),
                        timestamp,
                        sent_count,
                        str(username),
                    )
                    break
                # ----------------------------------------

                logger.error(f"Unexpected error sending to {username}: {e}")
                await self.sheets_client.update_contact_status(int(row_index), "Failed", timestamp)
                failed_count += 1

        # Повертаємо state в idle тільки якщо він не був примусово заблокований
        if self.state == "running":
            self.state = "idle"

        remaining = len(pending_contacts) - (sent_count + failed_count)

        return {
            "sent": sent_count,
            "failed": failed_count,
            "remaining": max(0, remaining),
            "state": self.state,
        }
