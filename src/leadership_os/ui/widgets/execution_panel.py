"""ExecutionPanel — right execution panel.

The heart of Leadership OS. Shows current task, focus timer, session info,
daily progress, next task, and action buttons.

Design: Always visible, ~300-360px wide. Displays the most critical information.
"""

from __future__ import annotations

import logging
from pathlib import Path

from kivy.clock import Clock
from kivy.lang import Builder
from kivy.properties import StringProperty, NumericProperty, BooleanProperty, ObjectProperty
from kivy.uix.boxlayout import BoxLayout

from leadership_os.ui.theme import theme
from leadership_os.utils.time_utils import format_duration_short, format_duration

logger = logging.getLogger(__name__)

# Load KV file
_kv_path = Path(__file__).resolve().parent.parent / "kv" / "execution_panel.kv"
if _kv_path.exists():
    Builder.load_file(str(_kv_path))


class ExecutionPanel(BoxLayout):
    """Right execution panel — timer, current task, progress, actions."""

    # Current task info
    current_task_title = StringProperty("No active task")
    current_task_priority = StringProperty("")
    current_task_priority_color = StringProperty("#9898B8")

    # Timer
    timer_display = StringProperty("00:00:00")
    timer_running = BooleanProperty(False)
    is_break = BooleanProperty(False)

    # Session info
    session_elapsed = StringProperty("00:00")
    session_estimated = StringProperty("--:--")

    # Progress
    completed_count = NumericProperty(0)
    total_count = NumericProperty(0)

    # Next task
    next_task_title = StringProperty("")

    # Progress status
    progress_status = StringProperty("No tasks yet")
    focus_time_display = StringProperty("0m")

    # State
    panel_state = StringProperty("idle")  # idle, working, break

    # Callbacks
    on_pause = ObjectProperty(lambda: None)
    on_complete = ObjectProperty(lambda: None)
    on_start_break = ObjectProperty(lambda: None)
    on_resume = ObjectProperty(lambda: None)
    on_end_break = ObjectProperty(lambda: None)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._tick_clock = Clock.schedule_interval(self._update_timer, 1.0)

    def _update_timer(self, dt: float) -> None:
        """Update timer display each second."""
        # Will be wired to TimerEngine in Phase 5
        pass

    def set_task(self, title: str, priority: str) -> None:
        self.current_task_title = title
        self.current_task_priority = priority.upper()
        self.current_task_priority_color = theme.priority(priority)

    def clear_task(self) -> None:
        self.current_task_title = "No active task"
        self.current_task_priority = ""
        self.panel_state = "idle"

    @property
    def progress_percent(self) -> float:
        if self.total_count > 0:
            return (self.completed_count / self.total_count) * 100
        return 0.0
