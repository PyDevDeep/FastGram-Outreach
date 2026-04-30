import asyncio
import contextlib
import json
import secrets
from collections.abc import Callable, Coroutine, Mapping
from functools import wraps
from pathlib import Path
from typing import Any, cast

import requests.exceptions
from cryptography.fernet import Fernet, InvalidToken
from instagrapi import Client  # type: ignore[reportMissingTypeStubs]
from instagrapi.exceptions import (  # type: ignore[reportMissingTypeStubs]
    BadPassword,
    ChallengeRequired,
    ClientConnectionError,
    LoginRequired,
    RateLimitError,
)
from requests.adapters import HTTPAdapter
from requests.models import PreparedRequest, Response

from app.config import Settings
from app.utils.logger import setup_logger

logger = setup_logger("instagram_client")


def with_api_retry[T](
    func: Callable[..., Coroutine[Any, Any, T]],
) -> Callable[..., Coroutine[Any, Any, T]]:
    """Декоратор для автоматичного retry Instagram API запитів."""

    @wraps(func)
    async def wrapper(*args: Any, **kwargs: Any) -> T:
        max_retries = 3
        backoff_delays = [5.0, 15.0, 45.0]

        for attempt in range(max_retries + 1):
            try:
                return await func(*args, **kwargs)
            except (ChallengeRequired, LoginRequired):
                # Критичні помилки авторизації — fail fast
                raise
            except RateLimitError as e:
                if attempt == max_retries:
                    logger.error(
                        f"[Retry {attempt}/{max_retries}] Rate Limit exhausted in {func.__name__}"
                    )
                    raise
                logger.warning(
                    f"Rate Limit in {func.__name__}: {e}. Waiting 60s... (Attempt {attempt + 1}/{max_retries})"
                )
                await asyncio.sleep(60.0)
            except (ClientConnectionError, requests.exceptions.RequestException, TimeoutError) as e:
                if attempt == max_retries:
                    logger.error(
                        f"[Retry {attempt}/{max_retries}] Network error exhausted in {func.__name__}"
                    )
                    raise
                delay = backoff_delays[attempt]
                logger.warning(
                    f"Network error in {func.__name__}: {e}. Waiting {delay}s... (Attempt {attempt + 1}/{max_retries})"
                )
                await asyncio.sleep(delay)

        # Гарантуємо Pylance, що функція не поверне None
        raise RuntimeError(f"Retry loop exhausted without returning or raising in {func.__name__}")

    return wrapper


class NoFallbackProxyAdapter(HTTPAdapter):
    """Забороняє fallback на локальний IP, але дозволяє retry на SSL помилки."""

    MAX_SSL_RETRIES = 3

    def send(
        self,
        request: PreparedRequest,
        stream: bool = False,
        timeout: Any = None,
        verify: bool | str = True,
        cert: Any = None,
        proxies: Mapping[str, str] | None = None,
    ) -> Response:
        last_error: Exception | None = None

        for attempt in range(1, self.MAX_SSL_RETRIES + 1):
            try:
                return super().send(
                    request,
                    stream=stream,
                    timeout=timeout,
                    verify=verify,
                    cert=cert,
                    proxies=proxies,
                )
            except requests.exceptions.SSLError as e:
                last_error = e
                logger.warning(f"SSL error on attempt {attempt}/{self.MAX_SSL_RETRIES}: {e}")
                if attempt == self.MAX_SSL_RETRIES:
                    raise RuntimeError(
                        f"Proxy SSL failed after {self.MAX_SSL_RETRIES} attempts: {e}"
                    ) from e

                import time

                time.sleep(1.0 * attempt)

            except Exception as e:
                raise RuntimeError(f"Proxy connection failed mid-request: {e}") from e

        raise RuntimeError(f"Proxy SSL failed: {last_error}")


class InstagramClient:
    def __init__(self, settings: Settings, client_factory: Callable[[], Client]) -> None:
        self.settings = settings
        self.client = client_factory()
        self.session_path = Path(self.settings.session_file_path)
        self.client.delay_range = [5, 15]
        self._session_lock = asyncio.Lock()

        # --- ЖОРСТКЕ ПЕРЕХОПЛЕННЯ CHALLENGE ---
        # Забороняємо бібліотеці просити код у консолі. Вона має просто падати з помилкою.
        def _challenge_handler(username: str, choice: Any | None = None) -> str:
            return self._force_challenge_fail()

        self.client.challenge_code_handler = _challenge_handler
        # --------------------------------------

        self._validate_encryption_key()
        self.client.set_locale(self.settings.instagram_locale)
        self.client.set_timezone_offset(self.settings.timezone_offset)

        self._proxy_alive = asyncio.Event()
        self._proxy_alive.set()
        self._monitor_task: asyncio.Task[Any] | None = None

        if self.settings.proxy_url:
            self.client.set_proxy(self.settings.proxy_url)
            adapter = NoFallbackProxyAdapter()
            self.client.private.mount("http://", adapter)
            self.client.private.mount("https://", adapter)
            self.client.public.mount("http://", adapter)
            self.client.public.mount("https://", adapter)
            logger.info(f"Proxy configured with no-fallback adapter: {self.settings.proxy_url}")
        else:
            logger.warning("No proxy configured. High risk of account ban.")

    def _force_challenge_fail(self) -> str:
        raise ChallengeRequired(
            "Challenge required (2FA/Email). Cannot resolve automatically in background."
        )

    @property
    def is_proxy_alive(self) -> bool:
        """Returns True if the proxy is currently alive or if no proxy is configured."""
        return self._proxy_alive.is_set()

    def _get_fernet(self) -> Fernet:
        return Fernet(self.settings.session_encryption_key.encode())

    def _validate_encryption_key(self) -> None:
        key = self.settings.session_encryption_key
        if not key:
            raise ValueError("SESSION_ENCRYPTION_KEY is not set.")
        try:
            Fernet(key.encode())
        except Exception as e:
            raise ValueError(f"SESSION_ENCRYPTION_KEY is invalid: {e}.") from e

    def _check_proxy(self) -> bool:
        if not self.settings.proxy_url:
            return True
        try:
            response = self.client.private.get(
                "http://gstatic.com/generate_204",
                timeout=self.settings.proxy_check_timeout,
            )
            return response.status_code == 204
        except Exception:
            return False

    async def _verify_proxy(self) -> bool:
        if not self.settings.proxy_url:
            return True
        result = await asyncio.to_thread(self._check_proxy)
        if result:
            logger.info("Proxy verified successfully")
        else:
            logger.critical("Proxy unreachable. Blocking login to prevent IP leak.")
        return result

    async def _proxy_monitor_loop(self) -> None:
        if not self.settings.proxy_url:
            return
        failures = 0
        logger.info(f"Proxy monitor started (interval: {self.settings.proxy_check_interval}s)")
        while True:
            await asyncio.sleep(self.settings.proxy_check_interval)
            alive = await asyncio.to_thread(self._check_proxy)

            if alive:
                if not self._proxy_alive.is_set():
                    self._proxy_alive.set()
                    logger.info("Proxy recovered — resuming operations")
                failures = 0
            else:
                failures += 1
                logger.warning(
                    f"Proxy check failed ({failures}/{self.settings.proxy_max_failures})"
                )

                if failures >= self.settings.proxy_max_failures and self._proxy_alive.is_set():
                    self._proxy_alive.clear()
                    logger.critical(
                        f"Proxy is DOWN after {failures} consecutive failures. "
                        "All Instagram operations blocked."
                    )

    def start_proxy_monitor(self) -> None:
        if self.settings.proxy_url and self._monitor_task is None:
            self._monitor_task = asyncio.create_task(self._proxy_monitor_loop())
            logger.info("Proxy monitor task created")

    async def stop_proxy_monitor(self) -> None:
        if self._monitor_task:
            self._monitor_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._monitor_task
            self._monitor_task = None
            logger.info("Proxy monitor stopped")

    async def _assert_proxy_alive(self) -> None:
        if self.settings.proxy_url and not self._proxy_alive.is_set():
            raise RuntimeError("Proxy is DOWN. Operation blocked to prevent IP leak.")

    async def _save_session_encrypted(self) -> None:
        f = self._get_fernet()
        settings_dict = cast(
            dict[str, Any],
            await asyncio.to_thread(self.client.get_settings),  # type: ignore[reportUnknownArgumentType, reportUnknownMemberType]
        )
        raw = json.dumps(settings_dict).encode("utf-8")
        self.session_path.parent.mkdir(parents=True, exist_ok=True)
        async with self._session_lock:
            await asyncio.to_thread(self.session_path.write_bytes, f.encrypt(raw))
        logger.info(f"Session encrypted and saved to {self.session_path}")

    async def _load_session_encrypted(self) -> None:
        f = self._get_fernet()
        try:
            async with self._session_lock:
                encrypted = await asyncio.to_thread(self.session_path.read_bytes)
            raw = f.decrypt(encrypted)
        except InvalidToken as e:
            raise ValueError("Session decryption failed: wrong key or corrupted file") from e

        settings_dict = cast(dict[str, Any], json.loads(raw.decode("utf-8")))
        await asyncio.to_thread(self.client.set_settings, settings_dict)  # type: ignore[reportUnknownArgumentType, reportUnknownMemberType]
        logger.info("Session decrypted and loaded into client (in-memory)")

    async def check_session_valid(self) -> bool:
        try:
            user_id = self.client.user_id
            if not user_id:
                return False
            await asyncio.to_thread(self.client.user_info, str(user_id))
            return True
        except Exception:
            return False

    async def login(self, verification_code: str | None = None) -> str:
        """Повертає: 'success', 'challenge_required', 'error'"""
        if not await self._verify_proxy():
            return "error"

        # Якщо є збережена сесія і ми не намагаємося передати код 2FA
        if self.session_path.exists() and not verification_code:
            try:
                logger.info(f"Loading session from {self.session_path}")
                await self._load_session_encrypted()

                if await self.check_session_valid():
                    logger.info("Session restored and validated successfully")
                    self.start_proxy_monitor()
                    delay = 1.5 + secrets.randbelow(2501) / 1000.0
                    await asyncio.sleep(delay)
                    return "success"
            except Exception as e:
                logger.error(f"Failed to load or validate session: {e}")
                await asyncio.sleep(2.0 + secrets.randbelow(3001) / 1000.0)

        try:
            logger.info("Attempting fresh login...")
            # Використовуємо or "", щоб замінити None на порожній рядок
            result = await asyncio.to_thread(
                self.client.login,
                self.settings.instagram_username,
                self.settings.instagram_password,
                verification_code=verification_code or "",
            )

            if result:
                await self._save_session_encrypted()
                logger.info("Login successful, session saved")
                self.start_proxy_monitor()
                delay = 3.0 + secrets.randbelow(5001) / 1000.0
                await asyncio.sleep(delay)
                return "success"

        except ChallengeRequired as e:
            logger.warning(f"Challenge Required (2FA/Captcha): {e}")
            return "challenge_required"
        except LoginRequired as e:
            logger.error(f"Login failed (credentials rejected): {e}")
            return "error"
        except BadPassword as e:
            logger.error(f"Auth Block / Bad Password: {e}")
            return "error"
        except Exception as e:
            logger.error(f"Unexpected login error: {e}")
            return "error"

        return "error"

    @with_api_retry
    async def send_direct_message(self, user_id: str, message_text: str) -> bool:
        """Відправка DM з автоматичним retry для мережевих помилок."""
        await self._assert_proxy_alive()
        logger.info(f"Sending DM to user_id: {user_id}")
        result = await asyncio.to_thread(
            self.client.direct_send,  # type: ignore[reportUnknownArgumentType, reportUnknownMemberType]
            message_text,
            user_ids=[int(user_id)],
        )
        return bool(result)

    @with_api_retry
    async def get_direct_inbox(self, limit: int = 20) -> list[Any]:
        """Отримання списку inbox threads з автоматичним retry."""
        await self._assert_proxy_alive()
        logger.info(f"Fetching direct inbox (limit={limit})")
        return await asyncio.to_thread(
            self.client.direct_threads,  # type: ignore[reportUnknownArgumentType, reportUnknownMemberType]
            amount=limit,
        )
