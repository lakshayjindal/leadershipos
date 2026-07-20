"""TaskForm — task creation and editing form.

Minimal form that initially shows only the title field.
Advanced options (priority, deadline, estimated time, notes) expand on request.

Design: Progressive disclosure — show only what's needed.
"""

from __future__ import annotations

import logging
from pathlib import Path

from kivy.clock import Clock
from kivy.lang import Builder
from kivy.properties import StringProperty, NumericProperty, ObjectProperty, BooleanProperty
from kivy.uix.boxlayout import BoxLayout
from kivymd.uix.textfield import MDTextField

logger = logging.getLogger(__name__)

# Load KV file
_kv_path = Path(__file__).resolve().parent.parent / "kv" / "task_form.kv"
if _kv_path.exists():
    Builder.load_file(str(_kv_path))


class TaskForm(BoxLayout):
    """Form for creating or editing a task.

    Shows required fields first (title), optional fields expand on request.
    """

    # Form fields
    title = StringProperty("")
    description = StringProperty("")
    priority = StringProperty("medium")
    deadline = StringProperty("")
    estimated_minutes = NumericProperty(0)
    notes = StringProperty("")

    # State
    is_edit_mode = BooleanProperty(False)
    editing_task_id = StringProperty("")
    advanced_visible = BooleanProperty(False)

    # Callbacks
    on_submit = ObjectProperty(lambda title, priority: None)
    on_cancel = ObjectProperty(lambda: None)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        Clock.schedule_once(self._focus_title, 0.1)

    def _focus_title(self, dt: float) -> None:
        """Focus the title input field after the form is rendered."""
        for child in self.walk():
            if isinstance(child, MDTextField) and child.focus:
                break

    def submit(self) -> None:
        """Submit the form — creates or updates the task."""
        title = self.title.strip()
        if not title:
            # Show validation error
            return
        self.on_submit(title, self.priority)
        self.reset()

    def cancel(self) -> None:
        """Cancel form entry."""
        self.reset()
        self.on_cancel()

    def reset(self) -> None:
        """Reset form to initial state."""
        self.title = ""
        self.description = ""
        self.priority = "medium"
        self.deadline = ""
        self.estimated_minutes = 0
        self.notes = ""
        self.is_edit_mode = False
        self.editing_task_id = ""
        self.advanced_visible = False

    def load_task(self, task_id: str, title: str, description: str = "",
                  priority: str = "medium", deadline: str = "",
                  estimated_minutes: int = 0, notes: str = "") -> None:
        """Load a task's data into the form for editing."""
        self.editing_task_id = task_id
        self.title = title
        self.description = description
        self.priority = priority
        self.deadline = deadline
        self.estimated_minutes = estimated_minutes
        self.notes = notes
        self.is_edit_mode = True

    def toggle_advanced(self) -> None:
        """Toggle advanced options visibility."""
        self.advanced_visible = not self.advanced_visible

    @property
    def submit_label(self) -> str:
        return "Save" if self.is_edit_mode else "Create"
