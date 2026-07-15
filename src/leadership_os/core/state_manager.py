"""State manager for Leadership OS.

Responsibilities:
- Persist runtime state to JSON (current state, active task, timer info)
- Load state on startup for recovery
- Validate state transitions
- Handle window position persistence

Design principle: JSON for runtime state, fast startup recovery.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from leadership_os.core.enums import AppState

logger = logging.getLogger(__name__)


class StateManager:
    """Manages application runtime state via JSON file.

    Usage:
        state = StateManager(Path("data/state.json"))
        state.load()
        state.set("app_state", "working")
        state.set("active_task_id", "task-uuid")
        state.save()
    """

    def __init__(self, state_path: Path) -> None:
        self.state_path = state_path
        self._data: dict[str, Any] = {}
        self._loaded = False

    def load(self) -> None:
        """Load state from file, or create defaults if missing."""
        if self.state_path.exists():
            try:
                with open(self.state_path, "r") as f:
                    self._data = json.load(f)
                self._loaded = True
                logger.info("State loaded from %s", self.state_path)
            except (json.JSONDecodeError, OSError) as e:
                logger.warning("Failed to load state from %s: %s", self.state_path, e)
                self._set_defaults()
                self._loaded = True
        else:
            self._set_defaults()
            self._loaded = True
            self.save()
            logger.info("Created default state at %s", self.state_path)

    def save(self) -> None:
        """Save current state to file."""
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.state_path, "w") as f:
            json.dump(self._data, f, indent=2)
        logger.debug("State saved to %s", self.state_path)

    def get(self, key: str, default: Any = None) -> Any:
        """Get a state value."""
        if not self._loaded:
            self.load()
        return self._data.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Set a state value (in memory only — call save() to persist)."""
        if not self._loaded:
            self.load()
        self._data[key] = value

    def get_app_state(self) -> str:
        """Get current application state string."""
        return self.get("app_state", AppState.STARTUP.value)

    def set_app_state(self, state: str) -> None:
        """Set application state and validate transition."""
        current = self.get_app_state()
        try:
            current_enum = AppState(current)
            target_enum = AppState(state)
            if not current_enum.can_transition_to(target_enum):
                logger.warning(
                    "Invalid state transition: %s → %s", current, state
                )
        except ValueError:
            pass  # Unknown state, allow it for forward compatibility
        self.set("app_state", state)
        logger.info("App state: %s → %s", current, state)

    def get_active_task_id(self) -> str | None:
        """Get the currently active task ID."""
        return self.get("active_task_id")

    def set_active_task_id(self, task_id: str | None) -> None:
        """Set the active task ID."""
        self.set("active_task_id", task_id)

    def get_active_break_id(self) -> str | None:
        """Get the currently active break ID."""
        return self.get("active_break_id")

    def set_active_break_id(self, break_id: str | None) -> None:
        """Set the active break ID."""
        self.set("active_break_id", break_id)

    def get_timer_start(self) -> str | None:
        """Get the timer start timestamp."""
        return self.get("timer_start")

    def set_timer_start(self, timestamp: str | None) -> None:
        """Set the timer start timestamp."""
        self.set("timer_start", timestamp)

    def get_needs_review(self) -> bool:
        """Check if the app was closed without completing review."""
        return bool(self.get("needs_review", False))

    def set_needs_review(self, value: bool) -> None:
        """Set the needs_review flag."""
        self.set("needs_review", value)

    def get_current_day_id(self) -> str | None:
        """Get the current day ID."""
        return self.get("current_day_id")

    def set_current_day_id(self, day_id: str | None) -> None:
        """Set the current day ID."""
        self.set("current_day_id", day_id)

    def get_window_position(self) -> tuple[int, int]:
        """Get saved window position."""
        pos = self.get("window_position", [100, 100])
        return (pos[0], pos[1])

    def set_window_position(self, x: int, y: int) -> None:
        """Save window position."""
        self.set("window_position", [x, y])

    def get_window_size(self) -> tuple[int, int]:
        """Get saved window size."""
        size = self.get("window_size", [1200, 800])
        return (size[0], size[1])

    def set_window_size(self, width: int, height: int) -> None:
        """Save window size."""
        self.set("window_size", [width, height])

    def get_overlay_position(self) -> tuple[int, int]:
        """Get saved overlay position."""
        pos = self.get("overlay_position", [-1, 40])
        return (pos[0], pos[1])

    def set_overlay_position(self, x: int, y: int) -> None:
        """Save overlay position."""
        self.set("overlay_position", [x, y])

    def get_last_session_date(self) -> str | None:
        """Get the date of the last session."""
        return self.get("last_session_date")

    def set_last_session_date(self, date_str: str) -> None:
        """Set the date of the last session."""
        self.set("last_session_date", date_str)

    def clear_active_state(self) -> None:
        """Clear all active state (task, break, timer)."""
        self.set("active_task_id", None)
        self.set("active_break_id", None)
        self.set("timer_start", None)

    def _set_defaults(self) -> None:
        """Set default state values."""
        self._data = {
            "app_state": AppState.STARTUP.value,
            "current_day_id": None,
            "active_task_id": None,
            "active_break_id": None,
            "timer_start": None,
            "window_position": [100, 100],
            "window_size": [1200, 800],
            "overlay_position": [-1, 40],
            "last_session_date": None,
            "needs_review": False,
        }
