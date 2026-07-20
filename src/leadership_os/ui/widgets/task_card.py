"""TaskCard — displays a single task in the task list.

Shows title, priority indicator, deadline, estimated time, and status.
Design: Clean card with hairline border, priority color accent on left edge.
"""

from __future__ import annotations

import logging
from pathlib import Path

from kivy.lang import Builder
from kivy.properties import StringProperty, NumericProperty, BooleanProperty, ObjectProperty, ListProperty
from kivy.uix.boxlayout import BoxLayout

from leadership_os.ui.theme import theme
from leadership_os.utils.time_utils import format_duration_short

logger = logging.getLogger(__name__)

# Load KV file
_kv_path = Path(__file__).resolve().parent.parent / "kv" / "task_card.kv"
if _kv_path.exists():
    Builder.load_file(str(_kv_path))


class TaskCard(BoxLayout):
    """A card representing a single task in the task list."""

    # Task data
    task_id = StringProperty("")
    title = StringProperty("")
    priority = StringProperty("medium")
    status = StringProperty("pending")
    deadline = StringProperty("")
    estimated_minutes = NumericProperty(0)
    actual_seconds = NumericProperty(0)
    notes = StringProperty("")

    # Display state
    is_active = BooleanProperty(False)
    is_completed = BooleanProperty(False)
    display_order = NumericProperty(0)

    # Callbacks
    on_activate = ObjectProperty(lambda: None)
    on_complete = ObjectProperty(lambda: None)
    on_edit = ObjectProperty(lambda: None)
    on_delete = ObjectProperty(lambda: None)

    @property
    def priority_rgba(self) -> list[float]:
        """RGBA tuple for the priority accent color."""
        return list(theme.to_rgba(theme.priority(self.priority)))

    @property
    def priority_bg_rgba(self) -> list[float]:
        """RGBA tuple for the priority badge background (muted version)."""
        rgba = self.priority_rgba
        return rgba[:3] + [0.2]

    @property
    def status_rgba(self) -> list[float]:
        """RGBA tuple for the status icon color."""
        colors = {
            "pending": theme.text("secondary"),
            "active": theme.dark["primary"],
            "paused": theme.text("muted"),
            "completed": theme.dark["success"],
            "carried_forward": theme.dark["warning"],
            "archived": theme.text("muted"),
        }
        hex_color = colors.get(self.status, theme.text("secondary"))
        return list(theme.to_rgba(hex_color))

    @property
    def priority_color(self) -> str:
        return theme.priority(self.priority)

    @property
    def priority_label(self) -> str:
        return self.priority.upper()

    @property
    def time_display(self) -> str:
        if self.actual_seconds > 0:
            return format_duration_short(self.actual_seconds)
        if self.estimated_minutes > 0:
            return f"est. {self.estimated_minutes}m"
        return ""

    @property
    def status_icon(self) -> str:
        icons = {
            "pending": "checkbox-blank-circle-outline",
            "active": "play-circle",
            "paused": "pause-circle",
            "completed": "check-circle",
            "carried_forward": "forward",
            "archived": "archive",
        }
        return icons.get(self.status, "checkbox-blank-circle-outline")
