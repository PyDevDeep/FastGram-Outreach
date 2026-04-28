import json
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger("warmup_manager")


class WarmupManager:
    def __init__(self, state_file_path: str = "app/state/warmup_state.json"):
        self.state_file = Path(state_file_path)
        self.default_state = {"day": 1, "daily_limit": 5, "is_active": True}
        self._state = self._load_state()

    def _load_state(self) -> dict[str, Any]:
        """Завантажує стан з файлу або створює новий."""
        if not self.state_file.exists():
            self._save_state(self.default_state)
            return self.default_state.copy()

        try:
            with open(self.state_file, encoding="utf-8") as f:
                return json.load(f)
        except (OSError, json.JSONDecodeError) as e:
            logger.error(
                f"Помилка зчитування warmup_state.json: {e}. Скидання до початкових значень."
            )
            return self.default_state.copy()

    def _save_state(self, state: dict[str, Any]) -> None:
        """Зберігає стан у JSON файл."""
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.state_file, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=4)

    def calculate_gradient_limit(self, current_day: int) -> int:
        """Розраховує ліміт за градієнтом з роадмапу."""
        if current_day <= 3:
            return 5
        elif current_day <= 6:
            return 10
        elif current_day <= 9:
            return 15
        elif current_day <= 12:
            return 25
        elif current_day <= 14:
            return 35
        else:
            # День 15+: Warm-up завершено
            if self._state["is_active"]:
                self._state["is_active"] = False
                logger.info("Warm-up режим завершено. Ліміт встановлено на 50 повідомлень.")
            return 50

    def get_current_day(self) -> int:
        """Повертає поточний день прогріву."""
        return self._state.get("day", 1)

    def get_current_daily_limit(self) -> int:
        """Повертає поточний денний ліміт."""
        return self._state.get("daily_limit", 5)

    def is_warmup_active(self) -> bool:
        """Перевіряє чи активний режим прогріву."""
        return bool(self._state.get("is_active", True))

    def increment_warmup_day(self) -> int:
        """Збільшує день та перераховує ліміт."""
        self._state["day"] += 1
        new_limit = self.calculate_gradient_limit(self._state["day"])
        self._state["daily_limit"] = new_limit

        self._save_state(self._state)
        logger.info(f"Warm-up: День {self._state['day']}. Новий ліміт: {new_limit}")
        return new_limit

    def reset_warmup(self) -> None:
        """Повне скидання стану прогріву."""
        self._state = self.default_state.copy()
        self._save_state(self._state)
        logger.warning("Warm-up режим скинуто до початкових значень (День 1).")
