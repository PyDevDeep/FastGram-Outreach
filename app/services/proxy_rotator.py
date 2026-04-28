import asyncio
import json
import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import httpx

from app.config import get_settings
from app.services.instagram_client import InstagramClient

logger = logging.getLogger("proxy_rotator")


class ProxyRotator:
    def __init__(self, state_file_path: str = "app/state/proxy_state.json"):
        self.settings = get_settings()
        self.api_url = self.settings.proxy_api_url
        self.api_key = self.settings.proxy_api_key
        self.state_file = Path(state_file_path)

        self.default_state = {
            "messages_sent_current_ip": 0,
            "last_rotation_timestamp": datetime.now(UTC).isoformat(),
        }
        self._state = self._load_state()

    def _load_state(self) -> dict[str, Any]:
        """Завантажує стан ротації (лічильники та таймстемпи)."""
        if not self.state_file.exists():
            self._save_state(self.default_state)
            return self.default_state.copy()
        try:
            with open(self.state_file, encoding="utf-8") as f:
                return json.load(f)
        except (OSError, json.JSONDecodeError) as e:
            logger.error(f"Помилка зчитування proxy_state.json: {e}. Скидання.")
            return self.default_state.copy()

    def _save_state(self, state: dict[str, Any]) -> None:
        """Зберігає стан у JSON."""
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.state_file, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=4)

    def is_rotation_needed(self) -> bool:
        """Перевіряє, чи виконані умови для ротації IP."""
        msgs = self._state.get("messages_sent_current_ip", 0)
        last_rot_str = self._state.get("last_rotation_timestamp")

        if msgs >= 50:
            logger.info("Proxy rotation needed: >= 50 messages sent on current IP.")
            return True

        if last_rot_str:
            try:
                last_rot = datetime.fromisoformat(last_rot_str)
                delta = datetime.now(UTC) - last_rot
                if delta.total_seconds() >= 86400:  # 24 години
                    logger.info("Proxy rotation needed: >= 24 hours since last rotation.")
                    return True
            except ValueError:
                logger.warning("Invalid timestamp in state. Forcing rotation.")
                return True

        return False

    async def request_new_ip(self) -> str | None:
        """Отримує новий IP через REST API провайдера з exponential backoff."""
        if not self.api_url:
            logger.warning("PROXY_API_URL не задано. Симулюю (Mock) ротацію для MVP.")
            # Для розробки: якщо API немає, просто повертаємо поточний проксі як "новий"
            return self.settings.proxy_url

        headers = {"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}

        for attempt in range(1, 4):
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.post(self.api_url, headers=headers, timeout=10.0)
                    response.raise_for_status()
                    data = response.json()

                    # Структура відповіді залежить від провайдера (Webshare, BrightData тощо).
                    # Припускаємо, що API повертає готовий рядок proxy_url.
                    proxy_url = data.get("proxy_url")
                    if proxy_url:
                        logger.info(f"Successfully obtained new proxy IP on attempt {attempt}.")
                        return str(proxy_url)

            except Exception as e:
                logger.warning(f"Failed to request new IP (Attempt {attempt}/3): {e}")
                if attempt < 3:
                    await asyncio.sleep(2**attempt)  # 2s, 4s...

        logger.error("All attempts to request new proxy IP failed.")
        return None

    async def update_instagram_session_proxy(
        self, instagram_client: InstagramClient, new_proxy_url: str
    ) -> bool:
        """Оновлює проксі в інстансі instagrapi та робить тестовий запит."""
        try:
            logger.info("Applying new proxy IP to Instagram Client...")
            instagram_client.client.set_proxy(new_proxy_url)
            instagram_client.settings.proxy_url = new_proxy_url

            # Lightweight API запит для валідації IP (згідно Roadmap)
            logger.info("Validating new IP via Instagram get_timeline_feed...")
            await asyncio.to_thread(
                instagram_client.client.get_timeline_feed  # type: ignore[reportUnknownMemberType]
            )

            # При успіху — скидаємо лічильники
            self._state["messages_sent_current_ip"] = 0
            self._state["last_rotation_timestamp"] = datetime.now(UTC).isoformat()
            self._save_state(self._state)

            logger.info("Successfully validated and saved new proxy state.")
            return True

        except Exception as e:
            logger.error(f"Proxy validation failed: {e}. Account might be blocked on this IP.")
            return False

    def increment_message_count(self) -> None:
        """Метод для виклику після кожного успішного повідомлення (для Engine)."""
        self._state["messages_sent_current_ip"] = self._state.get("messages_sent_current_ip", 0) + 1
        self._save_state(self._state)
