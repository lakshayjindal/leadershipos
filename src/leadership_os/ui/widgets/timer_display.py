"""TimerDisplay — large timer display with optional progress ring.

Shows elapsed time in large monospace font.
Optionally displays a circular progress ring when estimated duration is set.

Design: Focus on readability — large, clear, monospace. Progress ring is subtle.
"""

from __future__ import annotations

import math
import logging
from pathlib import Path

from kivy.clock import Clock
from kivy.graphics import Color, Ellipse, Line, Rectangle
from kivy.lang import Builder
from kivy.properties import StringProperty, NumericProperty, BooleanProperty, ListProperty
from kivy.uix.widget import Widget
from kivy.uix.boxlayout import BoxLayout

from leadership_os.ui.theme import theme
from leadership_os.utils.time_utils import format_duration

logger = logging.getLogger(__name__)

# Load KV file
_kv_path = Path(__file__).resolve().parent.parent / "kv" / "timer_display.kv"
if _kv_path.exists():
    Builder.load_file(str(_kv_path))


class ProgressRing(Widget):
    """A circular progress ring drawn with Kivy canvas."""

    progress = NumericProperty(0.0)  # 0.0 to 1.0
    ring_width = NumericProperty(4)
    ring_color = ListProperty([0.29, 0.44, 0.65, 1])  # primary blue

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.bind(pos=self._draw, size=self._draw, progress=self._draw,
                  ring_width=self._draw, ring_color=self._draw)

    def _draw(self, *args) -> None:
        self.canvas.clear()
        with self.canvas:
            center_x = self.center_x
            center_y = self.center_y
            radius = min(self.width, self.height) / 2 - self.ring_width

            # Background ring (track)
            Color(0.2, 0.2, 0.3, 0.3)
            Line(
                circle=(center_x, center_y, radius),
                width=self.ring_width,
            )

            # Progress arc
            if self.progress > 0:
                Color(*self.ring_color)
                # Calculate arc angles (Kivy uses 0-360 degrees starting from 3 o'clock)
                angle = 360 * self.progress
                Line(
                    circle=(center_x, center_y, radius, 0, angle),
                    width=self.ring_width,
                )


class TimerDisplay(BoxLayout):
    """Large timer display showing formatted elapsed time.

    Combines a large digital time display with an optional progress ring.
    """

    time_text = StringProperty("00:00:00")
    is_running = BooleanProperty(False)
    estimated_seconds = NumericProperty(0)  # 0 means no estimate (no ring)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._update_clock = Clock.schedule_interval(self._tick, 1.0)

    def _tick(self, dt: float) -> None:
        """Update display — wired to TimerEngine in Phase 5."""
        pass

    def set_time(self, seconds: int) -> None:
        self.time_text = format_duration(seconds)

    @property
    def progress(self) -> float:
        if self.estimated_seconds > 0:
            # Parse the current time_text to get elapsed seconds
            parts = self.time_text.split(":")
            elapsed = int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
            return min(1.0, elapsed / self.estimated_seconds)
        return 0.0
