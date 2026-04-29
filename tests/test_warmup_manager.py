"""Tests for warmup_manager module."""

import json
import os
from unittest.mock import MagicMock, patch

import pytest

from app.services.warmup_manager import WarmupManager


@pytest.fixture
def temp_state_file(tmp_path):
    return str(tmp_path / "test_warmup_state.json")


@pytest.fixture
def warmup_manager(temp_state_file):
    return WarmupManager(state_file_path=temp_state_file)


class TestWarmupManager:
    def test_initialization_creates_default_state(self, temp_state_file):
        assert not os.path.exists(temp_state_file)
        manager = WarmupManager(state_file_path=temp_state_file)
        assert os.path.exists(temp_state_file)
        assert manager.get_current_day() == 1

    def test_load_state_handles_corrupted_json(self, temp_state_file):
        with open(temp_state_file, "w") as f:
            f.write("{invalid_json: true")
        manager = WarmupManager(state_file_path=temp_state_file)
        assert manager.get_current_day() == 1

    def test_increment_warmup_day(self, warmup_manager):
        assert warmup_manager.get_current_day() == 1
        new_limit = warmup_manager.increment_warmup_day()

        # Day 2 still has limit 5
        assert warmup_manager.get_current_day() == 2
        assert new_limit == 5

        # Increment to Day 4 (limit 10)
        warmup_manager.increment_warmup_day()  # day 3
        new_limit = warmup_manager.increment_warmup_day()  # day 4
        assert warmup_manager.get_current_day() == 4
        assert new_limit == 10

    def test_is_warmup_active(self, warmup_manager):
        assert warmup_manager.is_warmup_active() is True

        # Fast forward to day 15
        for _ in range(14):
            warmup_manager.increment_warmup_day()

        assert warmup_manager.get_current_day() == 15
        assert warmup_manager.is_warmup_active() is False

    def test_reset_warmup(self, warmup_manager):
        warmup_manager.increment_warmup_day()
        assert warmup_manager.get_current_day() == 2

        warmup_manager.reset_warmup()
        assert warmup_manager.get_current_day() == 1
