"""Sidebar — left navigation panel.

Provides primary navigation between Today, History, and Settings contexts.
Bottom section shows lightweight session information.

Design: Minimal, compact, never resized. Uses calm blue accent for active state.
"""

from __future__ import annotations

from kivy.clock import Clock
from kivy.lang import Builder
from kivy.properties import StringProperty, NumericProperty, ObjectProperty
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.relativelayout import RelativeLayout
from kivymd.uix.behaviors import RectangularRippleBehavior

from leadership_os.ui.theme import theme
from leadership_os.utils.time_utils import format_duration_short

import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# Load KV file
_kv_path = Path(__file__).resolve().parent.parent / "kv" / "sidebar.kv"
if _kv_path.exists():
    Builder.load_file(str(_kv_path))


class SidebarNavItem(ButtonBehavior, RectangularRippleBehavior, RelativeLayout):
    """A single navigation item in the sidebar."""

    text = StringProperty("")
    icon = StringProperty("")
    active = NumericProperty(0)  # 0 = inactive, 1 = active
    badge_text = StringProperty("")

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            # KV binding handles active state via root.app_state
            return super().on_touch_down(touch)
        return super().on_touch_down(touch)


class Sidebar(BoxLayout):
    """Left navigation sidebar for Leadership OS.

    Displays navigation items and a bottom section with current session info.
    """

    app_state = StringProperty("startup")
    focus_time = NumericProperty(0)
    completed_count = NumericProperty(0)
    total_count = NumericProperty(0)

    # Callbacks (no 'on_' prefix — Kivy reserves on_X for event bindings)
    today_callback = ObjectProperty(lambda: None)
    history_callback = ObjectProperty(lambda: None)
    settings_callback = ObjectProperty(lambda: None)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._update_clock = Clock.schedule_interval(self._update_info, 5.0)

    def _update_info(self, dt: float) -> None:
        """Periodically update session info display."""
        pass  # Will be wired to engines in Phase 4+

    @property
    def focus_display(self) -> str:
        return format_duration_short(self.focus_time)

    @property
    def progress_display(self) -> str:
        if self.total_count > 0:
            return f"{self.completed_count} / {self.total_count}"
        return "0 / 0"
