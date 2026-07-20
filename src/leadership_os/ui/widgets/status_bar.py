"""StatusBar — bottom status bar.

Shows minimal session information: focus time, completed tasks, keyboard hint.
Design: Very small, unobtrusive, hairline-top border.
"""

from __future__ import annotations

import logging
from pathlib import Path

from kivy.clock import Clock
from kivy.lang import Builder
from kivy.properties import StringProperty, NumericProperty, ObjectProperty
from kivy.uix.boxlayout import BoxLayout

from leadership_os.utils.time_utils import format_duration_short

logger = logging.getLogger(__name__)

# Load KV file
_kv_path = Path(__file__).resolve().parent.parent / "kv" / "status_bar.kv"
if _kv_path.exists():
    Builder.load_file(str(_kv_path))


class StatusBar(BoxLayout):
    """Bottom status bar showing lightweight session information."""

    focus_time_display = StringProperty("0m")
    completed_display = StringProperty("0")
    hint_text = StringProperty("[ESC] Help")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._update_clock = Clock.schedule_interval(self._tick, 5.0)

    def _tick(self, dt: float) -> None:
        """Periodic update — will be wired to engines in Phase 4+."""
        pass

    def update_focus(self, seconds: int) -> None:
        self.focus_time_display = format_duration_short(seconds)

    def update_completed(self, completed: int) -> None:
        self.completed_display = str(completed)
