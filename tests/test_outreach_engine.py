"""Tests for outreach_engine module."""

import asyncio
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from instagrapi.exceptions import ChallengeRequired, LoginRequired

from app.services.outreach_engine import OutreachEngine

# ==========================================
# FIXTURES
# ==========================================


@pytest.fixture
def mock_instagram_client():
    client = MagicMock()
    client.proxy = "http://current-proxy:8080"
    client.send_direct_message = AsyncMock(return_value=True)
    client.login = AsyncMock(return_value=True)
    return client


@pytest.fixture
def mock_sheets_client():
    client = MagicMock()
    # Mocking basic list of contacts
    client.get_pending_contacts = AsyncMock(
        return_value=[
            {
                "_row_index": 2,
                "Instagram Username": "user_1",
                "Instagram User ID": "123",
                "Message Template": "Hello 1",
            },
            {
                "_row_index": 3,
                "Instagram Username": "user_2",
                "Instagram User ID": "456",
                "Message Template": "Hello 2",
            },
        ]
    )
    client.update_contact_status = AsyncMock()
    return client


@pytest.fixture
def mock_warmup_manager():
    return MagicMock()


@pytest.fixture
def mock_proxy_rotator():
    rotator = MagicMock()
    rotator.is_rotation_needed.return_value = False
    rotator.request_new_ip = AsyncMock(return_value="http://new-proxy:8080")
    rotator.update_instagram_session_proxy = AsyncMock(return_value=True)
    rotator.increment_message_count = MagicMock()
    return rotator


@pytest.fixture
def mock_pause_manager():
    manager = MagicMock()
    manager.is_paused.return_value = False
    manager.get_remaining_pause_time.return_value = "0:00:00"
    manager.trigger_pause = MagicMock()
    return manager


@pytest.fixture
def mock_notification_service():
    service = MagicMock()
    service.send_block_alert = AsyncMock()
    return service


@pytest.fixture
def outreach_engine(
    mock_instagram_client,
    mock_sheets_client,
    mock_warmup_manager,
    mock_proxy_rotator,
    mock_pause_manager,
    mock_notification_service,
):
    with patch("app.services.outreach_engine.get_settings") as mock_get_settings:
        settings = MagicMock()
        settings.daily_message_limit = 10
        settings.min_delay_seconds = 1
        settings.max_delay_seconds = 2
        mock_get_settings.return_value = settings

        engine = OutreachEngine(
            instagram_client=mock_instagram_client,
            sheets_client=mock_sheets_client,
            warmup_manager=mock_warmup_manager,
            proxy_rotator=mock_proxy_rotator,
            pause_manager=mock_pause_manager,
            notification_service=mock_notification_service,
        )
        yield engine


# ==========================================
# TESTS: OutreachEngine State
# ==========================================


class TestOutreachEngineState:
    def test_state_transitions(self, outreach_engine):
        """Test valid state transitions and event triggers."""
        assert outreach_engine.state == "idle"
        assert outreach_engine._resume_event.is_set()

        outreach_engine.state = "paused"
        assert outreach_engine.state == "paused"
        assert not outreach_engine._resume_event.is_set()

        outreach_engine.state = "running"
        assert outreach_engine.state == "running"
        assert outreach_engine._resume_event.is_set()

    def test_invalid_state_rejected(self, outreach_engine):
        """Test invalid state strings are ignored."""
        outreach_engine.state = "invalid_state"
        assert outreach_engine.state == "idle"  # Should remain unchanged


# ==========================================
# TESTS: Helpers
# ==========================================


class TestOutreachEngineHelpers:
    @pytest.mark.asyncio
    @patch("app.utils.delay.asyncio.sleep", new_callable=AsyncMock)
    async def test_generate_delay(self, mock_sleep, outreach_engine):
        delay = await outreach_engine.generate_delay(1, 2)
        assert 1.0 <= delay <= 2.0
        mock_sleep.assert_called_once()

    def test_calculate_batch_estimates(self, outreach_engine):
        limit, est_time = outreach_engine.calculate_batch_estimates(5)
        assert limit == 5
        # 5 items * (1.5 avg delay + 5 typing) = 32.5 seconds
        assert est_time is not None

    @pytest.mark.asyncio
    async def test_handle_account_block(self, outreach_engine):
        """Test that account blocks trigger pause and notifications."""
        await outreach_engine._handle_account_block(
            "Spam", 2, "2023-10-01T12:00:00Z", 5, "test_user"
        )

        assert outreach_engine.state == "blocked"
        outreach_engine.pause_manager.trigger_pause.assert_called_with("Spam")
        outreach_engine.sheets_client.update_contact_status.assert_called_with(
            2, "Failed", "2023-10-01T12:00:00Z"
        )
        outreach_engine.notification_service.send_block_alert.assert_called_with(
            "Spam", 5, "test_user"
        )


# ==========================================
# TESTS: Batch Execution
# ==========================================


class TestOutreachEngineRunBatch:
    @pytest.mark.asyncio
    async def test_run_batch_paused_system_returns_early(self, outreach_engine):
        """If PauseManager says system is paused, batch should abort."""
        outreach_engine.pause_manager.is_paused.return_value = True
        outreach_engine.pause_manager.get_remaining_pause_time.return_value = "1:00:00"

        result = await outreach_engine.run_batch()

        assert result["sent"] == 0
        assert result["state"] == "paused"
        outreach_engine.sheets_client.get_pending_contacts.assert_not_called()

    @pytest.mark.asyncio
    async def test_run_batch_engine_not_idle_returns_early(self, outreach_engine):
        """Engine cannot start a batch if it's already running/blocked."""
        outreach_engine.state = "running"
        result = await outreach_engine.run_batch()
        assert result["sent"] == 0
        outreach_engine.sheets_client.get_pending_contacts.assert_not_called()

    @pytest.mark.asyncio
    @patch("app.services.outreach_engine.random_delay", new_callable=AsyncMock)
    @patch("app.services.outreach_engine.typing_simulation_delay", new_callable=AsyncMock)
    async def test_run_batch_success(self, mock_typing, mock_delay, outreach_engine):
        """Standard happy path: process contacts successfully."""
        result = await outreach_engine.run_batch(batch_size=10)

        assert result["sent"] == 2
        assert result["failed"] == 0
        assert result["remaining"] == 0
        assert outreach_engine.state == "idle"

        assert outreach_engine.sheets_client.update_contact_status.call_count == 2
        assert outreach_engine.instagram_client.send_direct_message.call_count == 2
        assert outreach_engine.proxy_rotator.increment_message_count.call_count == 2

    @pytest.mark.asyncio
    @patch("app.services.outreach_engine.random_delay", new_callable=AsyncMock)
    @patch("app.services.outreach_engine.typing_simulation_delay", new_callable=AsyncMock)
    async def test_run_batch_dry_run(self, mock_typing, mock_delay, outreach_engine):
        """Dry run should mark sent without actually calling instagram."""
        result = await outreach_engine.run_batch(dry_run=True)

        assert result["sent"] == 2
        assert outreach_engine.instagram_client.send_direct_message.call_count == 0
        assert outreach_engine.sheets_client.update_contact_status.call_count == 2

    @pytest.mark.asyncio
    @patch("app.services.outreach_engine.random_delay", new_callable=AsyncMock)
    @patch("app.services.outreach_engine.typing_simulation_delay", new_callable=AsyncMock)
    async def test_run_batch_proxy_rotation(self, mock_typing, mock_delay, outreach_engine):
        """Should rotate proxy if rotator suggests it."""
        outreach_engine.proxy_rotator.is_rotation_needed.return_value = True

        await outreach_engine.run_batch()

        outreach_engine.proxy_rotator.request_new_ip.assert_called_once()
        outreach_engine.proxy_rotator.update_instagram_session_proxy.assert_called_once()

    @pytest.mark.asyncio
    @patch("app.services.outreach_engine.random_delay", new_callable=AsyncMock)
    @patch("app.services.outreach_engine.typing_simulation_delay", new_callable=AsyncMock)
    async def test_run_batch_handles_challenge_required(
        self, mock_typing, mock_delay, outreach_engine
    ):
        """ChallengeRequired should halt the batch immediately."""
        outreach_engine.instagram_client.send_direct_message.side_effect = ChallengeRequired("2FA")

        result = await outreach_engine.run_batch()

        assert result["failed"] == 1
        assert outreach_engine.state == "blocked"
        outreach_engine.pause_manager.trigger_pause.assert_called_with("ChallengeRequired")

    @pytest.mark.asyncio
    @patch("app.services.outreach_engine.random_delay", new_callable=AsyncMock)
    @patch("app.services.outreach_engine.typing_simulation_delay", new_callable=AsyncMock)
    async def test_run_batch_handles_login_required_success(
        self, mock_typing, mock_delay, outreach_engine
    ):
        """LoginRequired should attempt re-login and continue if successful."""
        # 1. Start batch (login succeeds)
        # 2. First message throws LoginRequired
        # 3. Engine calls login again (succeeds)
        # 4. Second message succeeds
        outreach_engine.instagram_client.send_direct_message.side_effect = [
            LoginRequired("Token expired"),
            True,
        ]
        outreach_engine.instagram_client.login.return_value = True

        result = await outreach_engine.run_batch()

        # Login is called twice: once at the very beginning of the batch,
        # and once during the recovery process.
        assert outreach_engine.instagram_client.login.call_count == 2
        assert result["failed"] == 1  # The one that triggered LoginRequired failed
        assert result["sent"] == 1  # The second one succeeded
        assert outreach_engine.state == "idle"

    @pytest.mark.asyncio
    @patch("app.services.outreach_engine.random_delay", new_callable=AsyncMock)
    @patch("app.services.outreach_engine.typing_simulation_delay", new_callable=AsyncMock)
    async def test_run_batch_handles_login_required_failure(
        self, mock_typing, mock_delay, outreach_engine
    ):
        """LoginRequired should block engine if re-login fails."""
        # We want the initial login check to pass, so the engine starts sending.
        # But when the first message throws LoginRequired, the RE-LOGIN attempt should fail.
        outreach_engine.instagram_client.login.side_effect = [True, False]
        outreach_engine.instagram_client.send_direct_message.side_effect = LoginRequired(
            "Token expired"
        )

        result = await outreach_engine.run_batch()

        assert outreach_engine.instagram_client.login.call_count == 2
        assert result["failed"] == 1
        assert outreach_engine.state == "blocked"
        outreach_engine.pause_manager.trigger_pause.assert_called_once()
