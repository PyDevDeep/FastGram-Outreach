from datetime import UTC, datetime

import httpx

from app.config import Settings, get_settings
from app.utils.logger import setup_logger

logger = setup_logger("notification_service")


class NotificationService:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()

    async def send_block_alert(self, reason: str, sent_count: int, username: str) -> None:
        """Відправляє Push-сповіщення у n8n про блокування акаунта."""
        webhook_url = self.settings.n8n_webhook_url
        if not webhook_url:
            logger.warning("N8N_WEBHOOK_URL не налаштовано. Алерт про блокування проігноровано.")
            return

        payload = {
            "reason": reason,
            "sent_count": sent_count,
            "timestamp": datetime.now(UTC).date().isoformat(),
            "username": username,
        }
        try:
            async with httpx.AsyncClient() as client:
                await client.post(webhook_url, json=payload, timeout=5.0)
                logger.info("Alert sent to n8n webhook successfully.")
        except Exception as e:
            logger.error(f"Failed to send block alert to n8n: {e}")
