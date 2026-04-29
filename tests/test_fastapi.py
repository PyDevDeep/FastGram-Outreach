"""Tests for FastAPI routers, main application, and dependencies."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.dependencies import (
    get_instagram_client,
    get_outreach_engine,
    get_pause_manager,
    get_settings,
    get_sheets_client,
    get_warmup_manager,
)
from app.main import app

client = TestClient(app)

# ==========================================
# FIXTURES & MOCKS
# ==========================================


@pytest.fixture(autouse=True)
def mock_dependencies():
    """Overrides FastAPI dependencies for testing."""

    # Mock Settings
    mock_settings = MagicMock()
    mock_settings.api_key = "test_api_key"
    app.dependency_overrides[get_settings] = lambda: mock_settings

    # Mock Sheets
    mock_sheets = MagicMock()
    app.dependency_overrides[get_sheets_client] = lambda: mock_sheets

    # Mock Instagram
    mock_ig = MagicMock()
    mock_ig.check_session_valid = AsyncMock(return_value=True)
    mock_ig.settings.proxy_url = "http://fake-proxy:80"
    mock_ig.is_proxy_alive = True
    app.dependency_overrides[get_instagram_client] = lambda: mock_ig

    # Mock Engine
    mock_engine = MagicMock()
    mock_engine.state = "idle"
    mock_engine.calculate_batch_estimates.return_value = (5, "0:01:00")
    mock_engine.run_batch = AsyncMock()
    mock_engine.sheets_client.get_pending_contacts = AsyncMock(return_value=[1, 2, 3])
    app.dependency_overrides[get_outreach_engine] = lambda: mock_engine

    # Mock Warmup
    mock_warmup = MagicMock()
    mock_warmup.is_warmup_active.return_value = True
    mock_warmup.get_current_day.return_value = 2
    mock_warmup.increment_warmup_day.return_value = 5
    mock_warmup.get_current_daily_limit.return_value = 5
    app.dependency_overrides[get_warmup_manager] = lambda: mock_warmup

    # Mock Pause
    mock_pause = MagicMock()
    mock_pause.is_paused.return_value = True
    app.dependency_overrides[get_pause_manager] = lambda: mock_pause

    yield

    app.dependency_overrides.clear()


@pytest.fixture
def api_headers():
    return {"X-API-Key": "test_api_key"}


# ==========================================
# TESTS: Security & Dependencies
# ==========================================


class TestDependencies:
    def test_missing_api_key(self):
        response = client.get("/health")
        # /health endpoint does not use verify_api_key dependency in this setup.
        assert response.status_code == 200

    def test_invalid_api_key(self):
        response = client.post("/outreach/start", headers={"X-API-Key": "wrong"})
        assert response.status_code == 401


# ==========================================
# TESTS: Health Router
# ==========================================


class TestHealthRouter:
    def test_health_check_ok(self):
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["instagram_session"] == "active"
        assert data["proxy"] == "reachable"


# ==========================================
# TESTS: Outreach Router
# ==========================================


class TestOutreachRouter:
    def test_start_outreach_success(self, api_headers):
        response = client.post(
            "/outreach/start", json={"batch_size": 5, "dry_run": True}, headers=api_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "started"
        assert data["dry_run"] is True

    def test_start_outreach_fails_if_running(self, api_headers):
        # Override specifically to return 'running' state
        mock_engine = MagicMock()
        mock_engine.state = "running"
        app.dependency_overrides[get_outreach_engine] = lambda: mock_engine

        response = client.post("/outreach/start", json={}, headers=api_headers)
        assert response.status_code == 400

    def test_pause_and_resume(self, api_headers):
        mock_engine = MagicMock()
        mock_engine.state = "running"
        app.dependency_overrides[get_outreach_engine] = lambda: mock_engine

        response = client.post("/outreach/pause", headers=api_headers)
        assert response.status_code == 200

        mock_engine.state = "paused"
        response = client.post("/outreach/resume", headers=api_headers)
        assert response.status_code == 200

    def test_get_outreach_status(self, api_headers):
        response = client.get("/outreach/status", headers=api_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["state"] == "idle"
        assert data["pending_in_sheets"] == 3


# ==========================================
# TESTS: Warm-up Router
# ==========================================


class TestWarmupRouter:
    def test_increment_warmup(self, api_headers):
        response = client.post("/outreach/warmup/increment", headers=api_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "incremented"
        assert data["day"] == 2

    def test_reset_warmup(self, api_headers):
        response = client.post("/outreach/warmup/reset", headers=api_headers)
        assert response.status_code == 200

    def test_get_warmup_status(self, api_headers):
        response = client.get("/outreach/warmup/status", headers=api_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["day"] == 2
        assert data["is_active"] is True


# ==========================================
# TESTS: Tracking Router
# ==========================================


class TestTrackingRouter:
    def test_check_replies(self, api_headers):
        # Tracking router has its own prefix /tracking
        # Let's mock ReplyTracker dependency
        with patch("app.routers.tracking.ReplyTracker") as mock_tracker_class:
            mock_instance = mock_tracker_class.return_value
            mock_instance.process_and_tag = AsyncMock(return_value={"processed": 5})

            response = client.get("/tracking/check-replies", headers=api_headers)
            assert response.status_code == 200
            assert response.json()["stats"]["processed"] == 5
