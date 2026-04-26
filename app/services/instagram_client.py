import asyncio
from pathlib import Path

from instagrapi import Client  # type: ignore[reportMissingTypeStubs]
from instagrapi.exceptions import (  # type: ignore[reportMissingTypeStubs]
    ChallengeRequired,
    LoginRequired,
)

from app.config import get_settings
from app.utils.logger import setup_logger

logger = setup_logger("instagram_client")


class InstagramClient:
    def __init__(self):
        self.settings = get_settings()
        self.client = Client()
        self.session_path = Path(self.settings.session_file_path)

        if self.settings.proxy_url:
            self.client.set_proxy(self.settings.proxy_url)
            logger.info(f"Proxy configured: {self.settings.proxy_url}")
        else:
            logger.warning("No proxy configured. High risk of account ban.")

    async def check_session_valid(self) -> bool:
        """Легкий запит для перевірки валідності поточної сесії."""
        try:
            # Використовуємо to_thread для уникнення блокування event loop
            await asyncio.to_thread(self.client.account_info)
            return True
        except Exception as e:
            logger.warning(f"Session validation failed: {e}")
            return False

    async def login(self) -> bool:
        """Авторизація з пріоритетом відновлення сесії."""
        # 1. Спроба відновлення сесії
        if self.session_path.exists():
            try:
                logger.info(f"Loading session from {self.session_path}")
                await asyncio.to_thread(self.client.load_settings, self.session_path)  # type: ignore[reportUnknownArgumentType]

                if await self.check_session_valid():
                    logger.info("Session restored and validated successfully")
                    return True
            except Exception as e:
                logger.error(f"Failed to load or validate session: {e}")

        # 2. Нова авторизація
        try:
            logger.info("Attempting fresh login...")
            result = await asyncio.to_thread(
                self.client.login,
                self.settings.instagram_username,
                self.settings.instagram_password,
            )

            if result:
                self.session_path.parent.mkdir(parents=True, exist_ok=True)
                await asyncio.to_thread(self.client.dump_settings, self.session_path)
                logger.info("Login successful, session saved to file")
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
