"""ProgressBar — daily progress indicator.

Shows task completion progress with a horizontal bar.
Used in the sidebar and execution panel for quick status at a glance.
"""

from __future__ import annotations

import logging
from pathlib import Path

from kivy.graphics import Color, RoundedRectangle
from kivy.lang import Builder
from kivy.properties import NumericProperty, StringProperty, ListProperty
from kivy.uix.widget import Widget

from leadership_os.ui.theme import theme

logger = logging.getLogger(__name__)

# Load KV file
_kv_path = Path(__file__).resolve().parent.parent / "kv" / "progress_bar.kv"
if _kv_path.exists():
    Builder.load_file(str(_kv_path))


class ProgressBar(Widget):
    """A custom horizontal progress bar for daily task completion.

    Shows completed vs total tasks with a subtle filled bar.
    Color transitions from warm amber (low) to calm blue (mid) to muted green (high).
    """

    value = NumericProperty(0)       # Completed count
    max_value = NumericProperty(100)  # Total count
    bar_height = NumericProperty(6)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.bind(pos=self._draw, size=self._draw, value=self._draw,
                  max_value=self._draw, bar_height=self._draw)

    def _draw(self, *args) -> None:
        self.canvas.clear()
        if self.max_value <= 0:
            return

        progress = min(1.0, self.value / self.max_value)
        bar_width = self.width * progress

        with self.canvas:
            # Background track
            Color(0.2, 0.2, 0.3, 0.3)
            RoundedRectangle(
                pos=(self.x, self.y + (self.height - self.bar_height) / 2),
                size=(self.width, self.bar_height),
                radius=[self.bar_height / 2],
            )

            # Filled progress
            if progress > 0:
                # Interpolate color based on progress
                color = self._get_progress_color(progress)
                Color(*color)
                RoundedRectangle(
                    pos=(self.x, self.y + (self.height - self.bar_height) / 2),
                    size=(bar_width, self.bar_height),
                    radius=[self.bar_height / 2],
                )

    @staticmethod
    def _get_progress_color(progress: float) -> list[float]:
        """Get color for the given progress level (0.0 - 1.0)."""
        # Low: warm amber (#C4A35A), Mid: calm blue (#4A6FA5), High: muted green (#5B9A6B)
        if progress < 0.4:
            # Amber-ish
            return [0.77, 0.64, 0.35, 1.0]
        elif progress < 0.75:
            # Blue-ish
            return [0.29, 0.44, 0.65, 1.0]
        else:
            # Green-ish
            return [0.36, 0.60, 0.42, 1.0]

    @property
    def percent(self) -> float:
        if self.max_value > 0:
            return (self.value / self.max_value) * 100
        return 0.0

    @property
    def display_text(self) -> str:
        return f"{int(self.value)} / {int(self.max_value)}"
