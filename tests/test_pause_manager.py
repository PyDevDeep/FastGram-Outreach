"""Tests for pause_manager module."""

import json
import os
from datetime import UTC, datetime, timedelta
from unittest.mock import patch

import pytest

from app.services.pause_manager import PauseManager


@pytest.fixture
def temp_state_file(tmp_path):
    return str(tmp_path / "test_pause_state.json")


@pytest.fixture
def pause_manager(temp_state_file):
    return PauseManager(state_file_path=temp_state_file)


class TestPauseManager:
    def test_initialization_creates_default_state(self, temp_state_file):
        assert not os.path.exists(temp_state_file)
        manager = PauseManager(state_file_path=temp_state_file)
        assert os.path.exists(temp_state_file)
        assert manager.is_paused() is False

    def test_load_state_handles_corrupted_json(self, temp_state_file):
        with open(temp_state_file, "w") as f:
            f.write("{invalid_json: true")
        manager = PauseManager(state_file_path=temp_state_file)
        assert manager.is_paused() is False

    def test_trigger_pause(self, pause_manager):
        assert pause_manager.is_paused() is False

        pause_manager.trigger_pause(reason="Action Blocked")

        assert pause_manager.is_paused() is True
        assert pause_manager._state["reason"] == "Action Blocked"

        # Check if the timestamp is saved and is in the future
        resume_time = datetime.fromisoformat(pause_manager._state["resume_timestamp"])
        assert resume_time > datetime.now(UTC)

    def test_is_paused_expires(self, pause_manager):
        # Set pause to expire 1 hour ago
        past_time = datetime.now(UTC) - timedelta(hours=1)
        pause_manager._state = {
            "is_paused": True,
            "resume_timestamp": past_time.isoformat(),
            "reason": "Test",
        }
        pause_manager._save_state(pause_manager._state)

        assert pause_manager.is_paused() is False
        assert pause_manager._state["is_paused"] is False

    def test_manual_resume(self, pause_manager):
        pause_manager.trigger_pause(reason="Test")
        assert pause_manager.is_paused() is True

        pause_manager.manual_resume()
        assert pause_manager.is_paused() is False
        assert pause_manager._state["resume_timestamp"] is None
        assert pause_manager._state["reason"] is None

    def test_get_remaining_pause_time(self, pause_manager):
        assert pause_manager.get_remaining_pause_time() is None

        pause_manager.trigger_pause()
        remaining = pause_manager.get_remaining_pause_time()
        assert remaining is not None
        assert ":" in remaining  # e.g. "23:59:59"
