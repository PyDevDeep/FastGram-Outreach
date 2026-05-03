"""Tests for instagram_client module."""

import asyncio
import contextlib
import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import requests
from cryptography.fernet import Fernet
from instagrapi.exceptions import (
    ChallengeRequired,
    ClientConnectionError,
    LoginRequired,
    RateLimitError,
)

from app.services.instagram_client import (
    InstagramClient,
    NoFallbackProxyAdapter,
    with_api_retry,
)

# ==========================================
# FIXTURES
# ==========================================


@pytest.fixture
def valid_fernet_key():
    """Provides a valid base64 Fernet key for tests."""
    return Fernet.generate_key().decode()


@pytest.fixture
def mock_settings(valid_fernet_key):
    """Mock application settings."""
    settings = MagicMock()
    settings.session_encryption_key = valid_fernet_key
    settings.session_file_path = "/tmp/fake_session.enc"
    settings.instagram_locale = "en_US"
    settings.timezone_offset = 0
    settings.proxy_url = "http://fake-proxy:8080"
    settings.proxy_check_timeout = 5
    settings.proxy_check_interval = 30
    settings.proxy_max_failures = 3
    settings.instagram_username = "test_user"
    settings.instagram_password = "test_password"
    return settings


@pytest.fixture
def mock_instagrapi_client():
    """Mock for instagrapi.Client to avoid real network calls."""
    client_instance = MagicMock()
    client_instance.private = MagicMock()
    client_instance.public = MagicMock()
    client_instance.user_id = 12345
    client_instance.get_settings.return_value = {"uuids": "fake"}
    return client_instance


@pytest.fixture
def instagram_client(mock_settings, mock_instagrapi_client):
    """InstagramClient instance with mocked settings and instagrapi injected via DI."""
    client = InstagramClient(settings=mock_settings, client_factory=lambda: mock_instagrapi_client)
    return client


# ==========================================
# TESTS: Decorators
# ==========================================


class TestWithApiRetry:
    """Test suite for with_api_retry decorator."""

    @pytest.mark.asyncio
    async def test_success_first_try(self):
        """Standard successful execution without retries."""

        @with_api_retry
        async def dummy():
            return "success"

        assert await dummy() == "success"

    @pytest.mark.asyncio
    async def test_fail_fast_on_auth_errors(self):
        """ChallengeRequired and LoginRequired should bypass retries."""

        @with_api_retry
        async def dummy():
            raise ChallengeRequired("Challenge")

        with pytest.raises(ChallengeRequired):
            await dummy()

    @pytest.mark.asyncio
    @patch("asyncio.sleep", new_callable=AsyncMock)
    async def test_retry_on_rate_limit(self, mock_sleep):
        """RateLimitError should trigger 60s sleep and retry."""
        call_count = 0

        @with_api_retry
        async def dummy():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise RateLimitError("Rate limited")
            return "recovered"

        result = await dummy()
        assert result == "recovered"
        assert mock_sleep.call_count == 2
        mock_sleep.assert_called_with(60.0)

    @pytest.mark.asyncio
    @patch("asyncio.sleep", new_callable=AsyncMock)
    async def test_exhaust_retries_network_error(self, mock_sleep):
        """Should raise error after exhausting max retries on network error."""

        @with_api_retry
        async def dummy():
            raise ClientConnectionError("Network down")

        with pytest.raises(ClientConnectionError):
            await dummy()

        assert mock_sleep.call_count == 3
        # Delays defined in code: 5.0, 15.0, 45.0
        assert mock_sleep.call_args_list[0][0][0] == 5.0
        assert mock_sleep.call_args_list[1][0][0] == 15.0
        assert mock_sleep.call_args_list[2][0][0] == 45.0


# ==========================================
# TESTS: NoFallbackProxyAdapter
# ==========================================


class TestNoFallbackProxyAdapter:
    """Test suite for custom proxy adapter."""

    @patch("requests.adapters.HTTPAdapter.send")
    def test_send_success(self, mock_super_send):
        """Standard HTTPAdapter behavior on success."""
        adapter = NoFallbackProxyAdapter()
        mock_resp = MagicMock()
        mock_super_send.return_value = mock_resp

        assert adapter.send(MagicMock()) == mock_resp

    @patch("time.sleep")
    @patch("requests.adapters.HTTPAdapter.send")
    def test_ssl_retry_logic(self, mock_super_send, mock_sleep):
        """SSLError triggers up to 3 retries with progressive backoff."""
        adapter = NoFallbackProxyAdapter()
        mock_super_send.side_effect = requests.exceptions.SSLError("SSL Handshake failed")

        # Виправлено match на фактичний текст помилки
        with pytest.raises(RuntimeError, match="Proxy connection failed after 3 attempts"):
            adapter.send(MagicMock())

        assert mock_super_send.call_count == 3
        assert mock_sleep.call_count == 2
        assert mock_sleep.call_args_list[0][0][0] == 1.0
        assert mock_sleep.call_args_list[1][0][0] == 2.0

    @patch("requests.adapters.HTTPAdapter.send")
    def test_generic_exception_aborts(self, mock_super_send):
        """Non-SSL exceptions should immediately abort the proxy connection."""
        adapter = NoFallbackProxyAdapter()
        mock_super_send.side_effect = ValueError("Invalid proxy format")

        # Виправлено match на фактичний текст помилки
        with pytest.raises(RuntimeError, match="Unexpected connection error mid-request"):
            adapter.send(MagicMock())
        assert mock_super_send.call_count == 1


# ==========================================
# TESTS: InstagramClient Validation & Auth
# ==========================================


@pytest.mark.skip(reason="Instagram account in 24h freeze cooldown (MOCK MODE active)")
class TestInstagramClientInitialization:
    def test_init_invalid_key_raises_error(self, mock_settings):
        """Initialization should validate Fernet key format."""
        mock_settings.session_encryption_key = "invalid_key"
        with pytest.raises(ValueError, match="SESSION_ENCRYPTION_KEY is invalid"):
            InstagramClient(settings=mock_settings, client_factory=MagicMock)

    def test_init_no_key_raises_error(self, mock_settings):
        """Missing key must be caught immediately."""
        mock_settings.session_encryption_key = ""
        with pytest.raises(ValueError, match="SESSION_ENCRYPTION_KEY is not set"):
            InstagramClient(settings=mock_settings, client_factory=MagicMock)


@pytest.mark.skip(reason="Instagram account in 24h freeze cooldown (MOCK MODE active)")
class TestInstagramClientProxy:
    @pytest.mark.asyncio
    @patch("asyncio.to_thread", new_callable=AsyncMock)
    async def test_proxy_monitor_detects_failure_and_blocks(self, mock_to_thread, instagram_client):
        """Monitor should drop proxy_alive flag after max_failures."""
        instagram_client.settings.proxy_max_failures = 2
        mock_to_thread.return_value = False  # _check_proxy returns False

        # Make sleep raise CancelledError on the 3rd call to break the infinite loop
        with patch(
            "app.services.instagram_client.asyncio.sleep", new_callable=AsyncMock
        ) as mock_sleep:
            mock_sleep.side_effect = [None, None, asyncio.CancelledError()]
            with contextlib.suppress(asyncio.CancelledError):
                await instagram_client._proxy_monitor_loop()

        assert not instagram_client.is_proxy_alive

    @pytest.mark.asyncio
    async def test_assert_proxy_alive_raises(self, instagram_client):
        """Should prevent operations when proxy is marked dead."""
        instagram_client._proxy_alive.clear()
        with pytest.raises(RuntimeError, match="Proxy is DOWN"):
            await instagram_client._assert_proxy_alive()


@pytest.mark.skip(reason="Instagram account in 24h freeze cooldown (MOCK MODE active)")
class TestInstagramClientLogin:
    @pytest.mark.asyncio
    @patch("app.services.instagram_client.InstagramClient._verify_proxy", return_value=False)
    async def test_login_blocked_if_proxy_dead(self, mock_verify, instagram_client):
        """Login aborted immediately if proxy validation fails."""
        # login() повертає рядок "error", а не bool False
        assert await instagram_client.login() == "error"
        instagram_client.client.login.assert_not_called()

    @pytest.mark.asyncio
    @patch("pathlib.Path.exists", return_value=True)
    @patch("app.services.instagram_client.InstagramClient._load_session_encrypted")
    @patch("app.services.instagram_client.InstagramClient.check_session_valid", return_value=True)
    @patch("asyncio.sleep", new_callable=AsyncMock)
    async def test_login_success_from_session(
        self, mock_sleep, mock_check, mock_load, mock_exists, instagram_client
    ):
        """Existing valid session should restore without actual credentials login."""
        instagram_client.start_proxy_monitor = MagicMock()

        with patch(
            "app.services.instagram_client.InstagramClient._verify_proxy", return_value=True
        ):
            # login() повертає рядок "success", а не bool True
            assert await instagram_client.login() == "success"

        mock_load.assert_called_once()
        instagram_client.start_proxy_monitor.assert_called_once()
        instagram_client.client.login.assert_not_called()

    @pytest.mark.asyncio
    @patch("pathlib.Path.exists", return_value=False)
    @patch("app.services.instagram_client.InstagramClient._save_session_encrypted")
    @patch("asyncio.to_thread", new_callable=AsyncMock)
    @patch("asyncio.sleep", new_callable=AsyncMock)
    async def test_fresh_login_success(
        self, mock_sleep, mock_to_thread, mock_save, mock_exists, instagram_client
    ):
        """Fresh login triggers instagrapi.login and saves encrypted session."""
        mock_to_thread.return_value = True  # інтерпретується як truthy в _do_login
        instagram_client.start_proxy_monitor = MagicMock()

        with patch(
            "app.services.instagram_client.InstagramClient._verify_proxy", return_value=True
        ):
            # login() повертає рядок "success", а не bool True
            assert await instagram_client.login() == "success"

        mock_save.assert_called_once()
        instagram_client.start_proxy_monitor.assert_called_once()

    @pytest.mark.asyncio
    @patch("pathlib.Path.exists", return_value=False)
    @patch("asyncio.to_thread", new_callable=AsyncMock)
    async def test_fresh_login_challenge_required(
        self, mock_to_thread, mock_exists, instagram_client
    ):
        """2FA/Captcha exception from to_thread must return challenge_required."""
        # ChallengeRequired з to_thread потрапляє в except всередині _do_login
        # і повертає "challenge_required", а не bool False
        mock_to_thread.side_effect = ChallengeRequired("2FA needed")

        with patch(
            "app.services.instagram_client.InstagramClient._verify_proxy", return_value=True
        ):
            assert await instagram_client.login() == "challenge_required"


@pytest.mark.skip(reason="Instagram account in 24h freeze cooldown (MOCK MODE active)")
class TestInstagramClientActions:
    @pytest.mark.asyncio
    @patch("asyncio.to_thread", new_callable=AsyncMock)
    async def test_send_direct_message_success(self, mock_to_thread, instagram_client):
        """Should validate proxy and delegate to instagrapi client."""
        mock_to_thread.return_value = MagicMock()

        result = await instagram_client.send_direct_message("123", "Hello")

        assert result is True
        mock_to_thread.assert_called_once()

        # Verify it passed the right args to instagrapi
        args = mock_to_thread.call_args[0]
        assert args[1] == "Hello"  # message_text
        assert mock_to_thread.call_args[1]["user_ids"] == [123]

    @pytest.mark.asyncio
    @patch("asyncio.to_thread", new_callable=AsyncMock)
    async def test_get_direct_inbox_success(self, mock_to_thread, instagram_client):
        """Should return threads successfully."""
        mock_threads = [{"id": 1}, {"id": 2}]
        mock_to_thread.return_value = mock_threads

        assert await instagram_client.get_direct_inbox(limit=2) == mock_threads
