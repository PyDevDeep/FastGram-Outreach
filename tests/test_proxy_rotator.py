"""Tests for proxy_rotator module."""

import json
import os
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, mock_open, patch

import httpx
import pytest

from app.services.proxy_rotator import ProxyRotator

# ==========================================
# FIXTURES
# ==========================================


@pytest.fixture
def mock_settings():
    settings = MagicMock()
    settings.proxy_api_url = "https://api.proxyprovider.com/rotate"
    settings.proxy_api_key = "secret_key"
    settings.proxy_url = "http://default-proxy:8080"
    return settings


@pytest.fixture
def temp_state_file(tmp_path):
    """Provides a temporary path for the state file."""
    return str(tmp_path / "test_proxy_state.json")


@pytest.fixture
def proxy_rotator(mock_settings, temp_state_file):
    """ProxyRotator instance with a temporary state file."""
    with patch("app.services.proxy_rotator.get_settings", return_value=mock_settings):
        rotator = ProxyRotator(state_file_path=temp_state_file)
        yield rotator


# ==========================================
# TESTS: State Management
# ==========================================


class TestProxyRotatorState:
    def test_load_state_creates_default_if_not_exists(self, mock_settings, temp_state_file):
        """Should create default state if file doesn't exist."""
        with patch("app.services.proxy_rotator.get_settings", return_value=mock_settings):
            assert not os.path.exists(temp_state_file)
            rotator = ProxyRotator(state_file_path=temp_state_file)

            assert os.path.exists(temp_state_file)
            assert rotator._state["messages_sent_current_ip"] == 0
            assert "last_rotation_timestamp" in rotator._state

    def test_load_state_handles_corrupted_json(self, mock_settings, temp_state_file):
        """Should fallback to default state if JSON is corrupted."""
        with open(temp_state_file, "w") as f:
            f.write("{invalid_json: true")

        with patch("app.services.proxy_rotator.get_settings", return_value=mock_settings):
            rotator = ProxyRotator(state_file_path=temp_state_file)
            assert rotator._state["messages_sent_current_ip"] == 0

    def test_increment_message_count(self, proxy_rotator):
        """Should increment count and save state."""
        assert proxy_rotator._state["messages_sent_current_ip"] == 0

        proxy_rotator.increment_message_count()

        assert proxy_rotator._state["messages_sent_current_ip"] == 1

        # Перевірка що файл зберігся
        with open(proxy_rotator.state_file) as f:
            data = json.load(f)
            assert data["messages_sent_current_ip"] == 1


# ==========================================
# TESTS: Rotation Rules
# ==========================================


class TestProxyRotatorRules:
    def test_is_rotation_needed_message_limit(self, proxy_rotator):
        """Should require rotation if >= 50 messages sent."""
        proxy_rotator._state["messages_sent_current_ip"] = 49
        assert not proxy_rotator.is_rotation_needed()

        proxy_rotator._state["messages_sent_current_ip"] = 50
        assert proxy_rotator.is_rotation_needed()

    def test_is_rotation_needed_time_limit(self, proxy_rotator):
        """Should require rotation if >= 24 hours passed."""
        now = datetime.now(UTC)

        # 23 hours ago - no rotation
        proxy_rotator._state["last_rotation_timestamp"] = (now - timedelta(hours=23)).isoformat()
        assert not proxy_rotator.is_rotation_needed()

        # 25 hours ago - rotation needed
        proxy_rotator._state["last_rotation_timestamp"] = (now - timedelta(hours=25)).isoformat()
        assert proxy_rotator.is_rotation_needed()

    def test_is_rotation_needed_invalid_timestamp(self, proxy_rotator):
        """Should force rotation if timestamp is invalid."""
        proxy_rotator._state["last_rotation_timestamp"] = "invalid_date_string"
        assert proxy_rotator.is_rotation_needed()


# ==========================================
# TESTS: API Requests
# ==========================================


class TestProxyRotatorRequests:
    @pytest.mark.asyncio
    async def test_request_new_ip_mock_fallback(self, mock_settings, temp_state_file):
        """If proxy_api_url is not set, it should return default proxy url."""
        mock_settings.proxy_api_url = None
        with patch("app.services.proxy_rotator.get_settings", return_value=mock_settings):
            rotator = ProxyRotator(state_file_path=temp_state_file)
            ip = await rotator.request_new_ip()
            assert ip == "http://default-proxy:8080"

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient.post", new_callable=AsyncMock)
    async def test_request_new_ip_success(self, mock_post, proxy_rotator):
        """Should return IP on successful API response."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"proxy_url": "http://new-proxy:1234"}
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        ip = await proxy_rotator.request_new_ip()

        assert ip == "http://new-proxy:1234"
        mock_post.assert_called_once()
        assert mock_post.call_args[1]["headers"] == {"Authorization": "Bearer secret_key"}

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient.post", new_callable=AsyncMock)
    @patch("asyncio.sleep", new_callable=AsyncMock)
    async def test_request_new_ip_retries_on_failure(self, mock_sleep, mock_post, proxy_rotator):
        """Should retry 3 times with exponential backoff on HTTP errors."""
        mock_post.side_effect = httpx.ConnectError("Connection refused")

        ip = await proxy_rotator.request_new_ip()

        assert ip is None
        assert mock_post.call_count == 3
        assert mock_sleep.call_count == 2
        # Backoff: 2s, 4s
        assert mock_sleep.call_args_list[0][0][0] == 2
        assert mock_sleep.call_args_list[1][0][0] == 4


# ==========================================
# TESTS: Validation
# ==========================================


class TestProxyRotatorValidation:
    @pytest.mark.asyncio
    @patch("asyncio.to_thread", new_callable=AsyncMock)
    async def test_update_instagram_session_proxy_success(self, mock_to_thread, proxy_rotator):
        """Should set proxy, validate via timeline, and reset state."""
        mock_ig_client = MagicMock()

        # Pre-set state to verify it resets
        proxy_rotator._state["messages_sent_current_ip"] = 55

        success = await proxy_rotator.update_instagram_session_proxy(
            mock_ig_client, "http://new-ip:80"
        )

        assert success is True
        mock_ig_client.client.set_proxy.assert_called_with("http://new-ip:80")
        mock_to_thread.assert_called_once_with(mock_ig_client.client.get_timeline_feed)

        # State should be reset
        assert proxy_rotator._state["messages_sent_current_ip"] == 0

    @pytest.mark.asyncio
    @patch("asyncio.to_thread", new_callable=AsyncMock)
    async def test_update_instagram_session_proxy_validation_fails(
        self, mock_to_thread, proxy_rotator
    ):
        """If validation fails, should return False and not reset state."""
        mock_ig_client = MagicMock()
        mock_to_thread.side_effect = Exception("Block detection")

        proxy_rotator._state["messages_sent_current_ip"] = 55

        success = await proxy_rotator.update_instagram_session_proxy(
            mock_ig_client, "http://bad-ip:80"
        )

        assert success is False
        # State remains unchanged
        assert proxy_rotator._state["messages_sent_current_ip"] == 55
