import asyncio
import contextlib
import json
import secrets
from collections.abc import Mapping
from pathlib import Path
from typing import Any, cast

from cryptography.fernet import Fernet, InvalidToken
from instagrapi import Client  # type: ignore[reportMissingTypeStubs]
from instagrapi.exceptions import (  # type: ignore[reportMissingTypeStubs]
    ChallengeRequired,
    LoginRequired,
)
from requests.adapters import HTTPAdapter
from requests.models import PreparedRequest, Response

from app.config import get_settings
from app.utils.logger import setup_logger

logger = setup_logger("instagram_client")


class NoFallbackProxyAdapter(HTTPAdapter):
    """Транспортний адаптер що забороняє будь-який fallback при помилці проксі."""

    def send(
        self,
        request: PreparedRequest,
        stream: bool = False,
        timeout: Any = None,
        verify: bool | str = True,
        cert: Any = None,
        proxies: Mapping[str, str] | None = None,
    ) -> Response:
        try:
            return super().send(
                request,
                stream=stream,
                timeout=timeout,
                verify=verify,
                cert=cert,
                proxies=proxies,
            )
        except Exception as e:
            raise RuntimeError(f"Proxy connection failed mid-request: {e}") from e


class InstagramClient:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.client = Client()
        self.session_path = Path(self.settings.session_file_path)
        self.client.delay_range = [5, 15]
        # Fail-Fast: валідація ключа при старті, не при першому використанні
        self._validate_encryption_key()
        # Локаль має відповідати географії проксі
        # Ukrainian proxy → uk-UA, Italian proxy → it-IT
        self.client.set_locale(self.settings.instagram_locale)  # наприклад "uk_UA"
        self.client.set_timezone_offset(self.settings.timezone_offset)  # наприклад 10800 для UTC+3

        # Proxy monitor state
        self._proxy_alive = asyncio.Event()
        self._proxy_alive.set()

        # Додано явний тип Task[Any]
        self._monitor_task: asyncio.Task[Any] | None = None

        if self.settings.proxy_url:
            self.client.set_proxy(self.settings.proxy_url)

            # Забороняємо requests робити fallback на локальний IP при падінні проксі
            adapter = NoFallbackProxyAdapter()
            self.client.private.mount("http://", adapter)
            self.client.private.mount("https://", adapter)
            # Додати після верифікації імені:
            self.client.public.mount("http://", adapter)
            self.client.public.mount("https://", adapter)
            logger.info(f"Proxy configured with no-fallback adapter: {self.settings.proxy_url}")
        else:
            logger.warning("No proxy configured. High risk of account ban.")

    # ------------------------------------------------------------------ #
    #  Internal helpers                                                    #
    # ------------------------------------------------------------------ #

    def _get_fernet(self) -> Fernet:
        return Fernet(self.settings.session_encryption_key.encode())

    def _validate_encryption_key(self) -> None:
        """Перевіряє що ключ шифрування валідний Fernet ключ.

        Fernet вимагає URL-safe base64 рядок довжиною 32 байти (44 символи в base64).
        Краще впасти при старті з чітким повідомленням ніж при збереженні сесії.
        """
        key = self.settings.session_encryption_key
        if not key:
            raise ValueError(
                "SESSION_ENCRYPTION_KEY is not set. "
                'Generate one with: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"'
            )
        try:
            Fernet(key.encode())
        except Exception as e:
            raise ValueError(
                f"SESSION_ENCRYPTION_KEY is invalid: {e}. "
                'Generate a valid key with: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"'
            ) from e

    # ------------------------------------------------------------------ #
    #  Proxy                                                               #
    # ------------------------------------------------------------------ #

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

    # [DEV ONLY] — ЗАКОМЕНТУВАТИ ПЕРЕД PRODUCTION ------------------------------------
    async def run_proxy_leak_check(self) -> None:
        """Діагностика: exit IP, leak headers, DNS resolver."""
        if not self.settings.proxy_url:
            logger.warning("[PROXY CHECK] No proxy set — skipping")
            return

        logger.info("[PROXY CHECK] Starting diagnostic...")

        try:
            # 1. Перевірка вихідного IP
            try:
                ip_resp = await asyncio.to_thread(
                    self.client.private.get,
                    "https://api.ipify.org?format=json",
                    timeout=10,
                )
                logger.info(f"[PROXY CHECK] Exit IP: {ip_resp.json().get('ip')}")
            except Exception as e:
                logger.error(f"[PROXY CHECK] IP check failed: {e}")

            # 2. Перевірка на витік заголовків
            try:
                headers_resp = await asyncio.to_thread(
                    self.client.private.get,
                    "https://httpbin.org/get",
                    timeout=10,
                )
                data = headers_resp.json()
                leak_headers = {
                    k: v
                    for k, v in data.get("headers", {}).items()
                    if k in ("X-Forwarded-For", "Via", "X-Real-Ip", "Forwarded")
                }
                if leak_headers:
                    logger.warning(f"[PROXY CHECK] Leak headers found: {leak_headers}")
                else:
                    logger.info("[PROXY CHECK] Headers clean — Elite proxy confirmed")
            except Exception as e:
                logger.error(f"[PROXY CHECK] Headers check failed: {e}")

            # 3. Перевірка DNS
            try:
                dns_resp = await asyncio.to_thread(
                    self.client.private.get,
                    "https://edns.ip-api.com/json",
                    timeout=10,
                )
                dns = dns_resp.json().get("dns", {})
                logger.info(f"[PROXY CHECK] DNS resolver: {dns.get('ip')} ({dns.get('geo')})")
            except Exception as e:
                logger.error(f"[PROXY CHECK] DNS check failed: {e}")

        except Exception as global_e:
            logger.critical(f"[PROXY CHECK] Unexpected error in diagnostic: {global_e}")

    # [DEV ONLY END] -------------------------------------------------------------
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

            # Виправлено SIM105 (Ruff)
            with contextlib.suppress(asyncio.CancelledError):
                await self._monitor_task

            self._monitor_task = None
            logger.info("Proxy monitor stopped")

    async def _assert_proxy_alive(self) -> None:
        if self.settings.proxy_url and not self._proxy_alive.is_set():
            raise RuntimeError("Proxy is DOWN. Operation blocked to prevent IP leak.")

    # ------------------------------------------------------------------ #
    #  Session                                                             #
    # ------------------------------------------------------------------ #

    async def _save_session_encrypted(self) -> None:
        f = self._get_fernet()

        # Додано cast для Strict Mode
        settings_dict = cast(
            dict[str, Any],
            await asyncio.to_thread(self.client.get_settings),  # type: ignore[reportUnknownArgumentType, reportUnknownMemberType]
        )

        raw = json.dumps(settings_dict).encode("utf-8")
        self.session_path.parent.mkdir(parents=True, exist_ok=True)
        self.session_path.write_bytes(f.encrypt(raw))
        logger.info(f"Session encrypted and saved to {self.session_path}")

    async def _load_session_encrypted(self) -> None:
        f = self._get_fernet()
        try:
            encrypted = self.session_path.read_bytes()
            raw = f.decrypt(encrypted)
        except InvalidToken as e:
            raise ValueError("Session decryption failed: wrong key or corrupted file") from e

        # Додано cast для Strict Mode
        settings_dict = cast(dict[str, Any], json.loads(raw.decode("utf-8")))

        await asyncio.to_thread(self.client.set_settings, settings_dict)  # type: ignore[reportUnknownArgumentType, reportUnknownMemberType]
        logger.info("Session decrypted and loaded into client (in-memory)")

    # ------------------------------------------------------------------ #
    #  Auth                                                                #
    # ------------------------------------------------------------------ #

    async def check_session_valid(self) -> bool:
        try:
            user_id = self.client.user_id
            if not user_id:
                logger.warning("Session validation failed: No user_id found in loaded settings.")
                return False

            # Додано str() для Strict Mode
            await asyncio.to_thread(self.client.user_info, str(user_id))
            return True
        except Exception as e:
            logger.warning(f"Session validation failed: {e}")
            return False

    async def login(self) -> bool:
        if not await self._verify_proxy():
            return False
        # [DEV ONLY] — ЗАКОМЕНТУВАТИ ПЕРЕД PRODUCTION --------------------------------
        if self.settings.debug:
            await self.run_proxy_leak_check()
        # ------------------------------------------------------------------------
        if self.session_path.exists():
            try:
                logger.info(f"Loading session from {self.session_path}")
                await self._load_session_encrypted()

                if await self.check_session_valid():
                    logger.info("Session restored and validated successfully")
                    self.start_proxy_monitor()

                    delay = 1.5 + secrets.randbelow(2501) / 1000.0  # 1.500 – 4.000
                    logger.info(f"Post-restore human delay: {delay:.1f}s")
                    await asyncio.sleep(delay)

                    return True
            except Exception as e:
                logger.error(f"Failed to load or validate session: {e}")
                await asyncio.sleep(2.0 + secrets.randbelow(3001) / 1000.0)

        try:
            logger.info("Attempting fresh login...")
            result = await asyncio.to_thread(
                self.client.login,
                self.settings.instagram_username,
                self.settings.instagram_password,
            )

            if result:
                await self._save_session_encrypted()
                logger.info("Login successful, session saved")
                self.start_proxy_monitor()

                # Людська пауза після логіну перед першою дією
                delay = 3.0 + secrets.randbelow(5001) / 1000.0  # 3.000 – 8.000
                logger.info(f"Post-login human delay: {delay:.1f}s")
                await asyncio.sleep(delay)

                return True

        except ChallengeRequired as e:
            logger.critical(f"Challenge Required (2FA/Captcha). Cannot proceed automatically: {e}")
            return False
        except LoginRequired as e:
            logger.error(f"Login failed (credentials rejected): {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected login error: {e}")
            return False

        return False
