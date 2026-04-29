"""Tests for notification_service module."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from app.services.notification_service import NotificationService

# ==========================================
# FIXTURES
# ==========================================


@pytest.fixture
def mock_settings():
    """Mock application settings with configured webhook."""
    settings = MagicMock()
    settings.n8n_webhook_url = "https://webhook.n8n.local/test"
    return settings


@pytest.fixture
def mock_settings_no_webhook():
    """Mock application settings without webhook."""
    settings = MagicMock()
    settings.n8n_webhook_url = None
    return settings


@pytest.fixture
def notification_service(mock_settings):
    """NotificationService instance with configured webhook."""
    return NotificationService(settings=mock_settings)


# ==========================================
# TESTS: NotificationService
# ==========================================


class TestNotificationService:
    """Test suite for NotificationService block alerts."""

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient.post", new_callable=AsyncMock)
    async def test_send_block_alert_success(self, mock_post, notification_service, mock_settings):
        """Should send correct JSON payload to configured webhook URL."""
        mock_post.return_value.status_code = 200

        await notification_service.send_block_alert(
            reason="Rate Limit", sent_count=15, username="test_account"
        )

        mock_post.assert_called_once()

        # Перевірка аргументів виклику
        call_args = mock_post.call_args
        assert call_args[0][0] == mock_settings.n8n_webhook_url

        payload = call_args[1]["json"]
        assert payload["reason"] == "Rate Limit"
        assert payload["sent_count"] == 15
        assert payload["username"] == "test_account"
        assert payload["timestamp"] == datetime.now(UTC).date().isoformat()

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient.post", new_callable=AsyncMock)
    async def test_send_block_alert_no_webhook_url(self, mock_post, mock_settings_no_webhook):
        """Should exit early without sending HTTP request if URL is not set."""
        service = NotificationService(settings=mock_settings_no_webhook)

        await service.send_block_alert("Ban", 10, "user")

        mock_post.assert_not_called()

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient.post", new_callable=AsyncMock)
    async def test_send_block_alert_http_error_handled_gracefully(
        self, mock_post, notification_service
    ):
        """Should catch httpx Exceptions and not crash the application."""
        mock_post.side_effect = httpx.ConnectError("Connection refused")

        # Виклик не повинен викидати exception назовні
        await notification_service.send_block_alert("Error", 5, "user")

        mock_post.assert_called_once()
