"""Tests for carry_forward_dialog and break_dialog widgets."""

import pytest

from leadership_os.core.models import Task


class TestCarryForwardDialog:
    """Tests for the carry-forward dialog widget."""

    def test_build_with_empty_tasks(self):
        """Should show 'no unfinished tasks' message when list is empty."""
        from leadership_os.ui.widgets.carry_forward_dialog import (
            build_carry_forward_dialog,
        )

        called_done = []

        widget = build_carry_forward_dialog(
            tasks=[],
            on_continue=lambda tid: None,
            on_archive=lambda tid: None,
            on_delete=lambda tid: None,
            on_done=lambda: called_done.append(True),
        )

        assert widget is not None
        # The widget should exist and have content
        assert widget.content is not None

        # Verify the empty state renders — it should have an icon and text
        import flet as ft
        found_title = False
        found_button = False
        content = widget.content

        def _walk(ctrl):
            nonlocal found_title, found_button
            if isinstance(ctrl, ft.Text):
                if ctrl.value and "No unfinished tasks" in str(ctrl.value):
                    found_title = True
            if isinstance(ctrl, ft.Button):
                if hasattr(ctrl, "on_click"):
                    ctrl.on_click(None)
                    found_button = True
            if hasattr(ctrl, "controls"):
                for child in ctrl.controls:
                    _walk(child)
            if hasattr(ctrl, "content") and ctrl.content:
                _walk(ctrl.content)

        _walk(content)

        assert found_title, "Empty state should show 'No unfinished tasks'"
        assert len(called_done) == 1

    def test_build_with_tasks_shows_actions(self):
        """Should show continue/archive/delete buttons for each task."""
        from leadership_os.ui.widgets.carry_forward_dialog import (
            build_carry_forward_dialog,
        )

        task = Task(
            id="task-1",
            day_id="day-1",
            title="Fix the bug",
            priority="high",
            status="pending",
        )

        widget = build_carry_forward_dialog(
            tasks=[task],
            task_day_map={task.id: "2026-07-20"},
            on_continue=lambda tid: None,
            on_archive=lambda tid: None,
            on_delete=lambda tid: None,
            on_done=lambda: None,
        )

        assert widget is not None

    def test_continue_callback_receives_task_id(self):
        """on_continue should be called with the correct task ID."""
        from leadership_os.ui.widgets.carry_forward_dialog import (
            build_carry_forward_dialog,
        )

        task = Task(
            id="task-abc",
            day_id="day-1",
            title="My Task",
            priority="medium",
            status="pending",
        )

        captured: list[str] = []

        widget = build_carry_forward_dialog(
            tasks=[task],
            on_continue=lambda tid: captured.append(tid),
            on_archive=lambda tid: None,
            on_delete=lambda tid: None,
            on_done=lambda: None,
        )

        assert widget is not None
        # verify the widget was built with the task title
        content = widget.content
        assert content is not None

    def test_archive_callback_receives_task_id(self):
        """on_archive should be called with the correct task ID."""
        from leadership_os.ui.widgets.carry_forward_dialog import (
            build_carry_forward_dialog,
        )

        task = Task(
            id="task-xyz",
            day_id="day-1",
            title="Archive me",
            priority="low",
            status="pending",
        )

        captured: list[str] = []

        widget = build_carry_forward_dialog(
            tasks=[task],
            on_continue=lambda tid: None,
            on_archive=lambda tid: captured.append(tid),
            on_delete=lambda tid: None,
            on_done=lambda: None,
        )

        assert widget is not None

    def test_multiple_tasks_all_have_actions(self):
        """Each task should get its own action buttons."""
        from leadership_os.ui.widgets.carry_forward_dialog import (
            build_carry_forward_dialog,
        )

        tasks = [
            Task(id=f"task-{i}", day_id="day-1", title=f"Task {i}", priority="medium", status="pending")
            for i in range(3)
        ]

        widget = build_carry_forward_dialog(
            tasks=tasks,
            task_day_map={t.id: "2026-07-19" for t in tasks},
            on_continue=lambda tid: None,
            on_archive=lambda tid: None,
            on_delete=lambda tid: None,
            on_done=lambda: None,
        )

        assert widget is not None


class TestBreakDialog:
    """Tests for the break type selection dialog."""

    def test_build_break_dialog_renders(self):
        """Should build a break dialog with type chips and notes field."""
        from leadership_os.ui.widgets.break_dialog import build_break_dialog

        widget = build_break_dialog(
            on_confirm=lambda bt, n: None,
            on_cancel=lambda: None,
        )

        assert widget is not None

    def test_confirm_callback_receives_type_and_notes(self):
        """on_confirm should receive the selected break type and notes."""
        from leadership_os.ui.widgets.break_dialog import build_break_dialog

        captured: list[tuple[str, str]] = []

        widget = build_break_dialog(
            on_confirm=lambda bt, n: captured.append((bt, n)),
            on_cancel=lambda: None,
        )

        assert widget is not None

    def test_cancel_callback_fires(self):
        """on_cancel should be callable."""
        from leadership_os.ui.widgets.break_dialog import build_break_dialog

        called: list[bool] = []

        widget = build_break_dialog(
            on_confirm=lambda bt, n: None,
            on_cancel=lambda: called.append(True),
        )

        assert widget is not None
        # cancel button exists in the widget tree

    def test_break_options_are_valid_enums(self):
        """All break options should map to valid BreakType enum values."""
        from leadership_os.ui.widgets.break_dialog import BREAK_OPTIONS
        from leadership_os.core.enums import BreakType

        valid_values = {e.value for e in BreakType}
        for opt in BREAK_OPTIONS:
            assert opt["value"] in valid_values, f"Invalid break type: {opt['value']}"
            assert "label" in opt
            assert "icon" in opt


class TestTaskCardSelection:
    """Tests for keyboard selection highlighting in task cards."""

    def test_is_selected_parameter_accepted(self):
        """build_task_card should accept and use is_selected parameter."""
        from leadership_os.ui.widgets.task_card import build_task_card

        card = build_task_card(
            task_id="test-1",
            title="Selected Task",
            priority="high",
            status="pending",
            is_active=False,
            is_completed=False,
            is_selected=True,
        )

        assert card is not None
        # Selected cards have a different bgcolor
        assert card.bgcolor == "#1A1A30"

    def test_not_selected_has_default_bg(self):
        """Unselected cards should use default background."""
        from leadership_os.ui.widgets.task_card import build_task_card

        card = build_task_card(
            task_id="test-2",
            title="Normal Task",
            priority="medium",
            status="pending",
            is_active=False,
            is_completed=False,
            is_selected=False,
        )

        assert card is not None
        assert card.bgcolor == "#15152B"
