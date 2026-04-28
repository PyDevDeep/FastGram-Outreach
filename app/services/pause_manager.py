import json
import logging
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, cast

logger = logging.getLogger("pause_manager")


class PauseManager:
    def __init__(self, state_file_path: str = "app/state/pause_state.json"):
        self.state_file = Path(state_file_path)
        self.default_state: dict[str, Any] = {
            "is_paused": False,
            "paused_at": None,
            "resume_at": None,
            "reason": None,
        }
        # Явно вказуємо тип для словника стану
        self._state: dict[str, Any] = self._load_state()

    def _load_state(self) -> dict[str, Any]:
        """Завантажує стан з файлу або створює дефолтний."""
        if not self.state_file.exists():
            self._save_state(self.default_state)
            return self.default_state.copy()

        try:
            with open(self.state_file, encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    # Використовуємо cast для повного визначення типів вмісту словника
                    return cast(dict[str, Any], data)
                return self.default_state.copy()
        except (OSError, json.JSONDecodeError) as e:
            logger.error(f"Помилка зчитування pause_state.json: {e}. Скидання стану.")
            return self.default_state.copy()

    def _save_state(self, state: dict[str, Any]) -> None:
        """Зберігає поточний стан у JSON."""
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.state_file, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=4)

    def trigger_pause(self, reason: str) -> datetime:
        """Активує паузу на 24 години."""
        now = datetime.now(UTC)
        resume_time = now + timedelta(hours=24)

        self._state["is_paused"] = True
        self._state["paused_at"] = now.isoformat()
        self._state["resume_at"] = resume_time.isoformat()
        self._state["reason"] = reason

        self._save_state(self._state)
        logger.warning(
            f"Outreach paused for 24h due to [{reason}]. Resume at {resume_time.isoformat()}"
        )
        return resume_time

    def auto_resume(self) -> bool:
        """Знімає паузу, якщо час вийшов."""
        if not self._state.get("is_paused"):
            return False

        resume_str = self._state.get("resume_at")
        if not resume_str:
            return False

        resume_at = datetime.fromisoformat(resume_str)
        if datetime.now(UTC) >= resume_at:
            self._state = self.default_state.copy()
            self._save_state(self._state)
            logger.info("Outreach auto-resumed after 24h pause.")
            return True

        return False

    def is_paused(self) -> bool:
        """Повертає True, якщо система на паузі. Включає ліниву перевірку авто-зняття."""
        # Спочатку перевіряємо, чи не час зняти паузу
        if self.auto_resume():
            return False
        return self._state.get("is_paused", False)

    def get_remaining_pause_time(self) -> timedelta | None:
        """Повертає залишковий час."""
        if not self.is_paused():
            return None

        resume_str = self._state.get("resume_at")
        if not resume_str:
            return None

        resume_at = datetime.fromisoformat(resume_str)
        return resume_at - datetime.now(UTC)

    def manual_resume(self) -> None:
        """Примусове зняття паузи адміном."""
        self._state = self.default_state.copy()
        self._save_state(self._state)
        logger.info("Outreach manually resumed by admin before 24h.")
