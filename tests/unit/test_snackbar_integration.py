"""Integration tests that catch Flet API compatibility issues at test time.

These tests simulate user interactions (like clicking Save on settings) to verify
that no AttributeError is raised at runtime due to incorrect Flet API usage.

Because these tests were missing, runtime errors like:
- 'Page' object has no attribute 'show_snack_bar'
- 'Page' object has no attribute 'open'
...were only discovered when a user actually ran the app and clicked buttons.
"""

from __future__ import annotations

import pytest
import flet as ft


# ─── Helper: Fake Page for testing SnackBar calls ────────────────────

class FakePage:
    """A minimal fake flet.Page that accepts snack_bar assignments.

    Used to verify that SnackBar code doesn't use AttributeErrors at runtime.
    """

    def __init__(self) -> None:
        self.snack_bar = None
        self._updated = False

    def update(self) -> None:
        self._updated = True


class FakeControlEvent:
    """A minimal fake flet.ControlEvent that wraps a FakePage."""

    def __init__(self, page: FakePage) -> None:
        self.page = page
        self.control = None


# ─── Test: settings_screen on_save uses correct SnackBar API ──────────

class TestSettingsScreenSnackBar:
    """Verify settings_screen.py uses the correct Flet 0.86 SnackBar API."""

    def test_on_save_snackbar_uses_correct_api(self):
        """on_save should set page.snack_bar and page.snack_bar.open, not call missing methods."""
        from leadership_os.ui.widgets.settings_screen import build_settings_screen
        from leadership_os.config.config_manager import ConfigManager
        from leadership_os.core.event_bus import EventBus

        # Setup
        import tempfile, os
        from pathlib import Path
        tmpdir = tempfile.mkdtemp()
        config_path = Path(tmpdir) / "config.toml"
        config = ConfigManager(config_path)
        config.load()
        event_bus = EventBus()

        fake_page = FakePage()
        close_called: list[bool] = []

        # Build the settings screen
        widget = build_settings_screen(
            config=config,
            event_bus=event_bus,
            on_close=lambda: close_called.append(True),
        )

        assert widget is not None

        # Find the Save button by walking the widget tree
        save_button = _find_button_by_text(widget, "Save Settings")
        assert save_button is not None, "Save button should exist in settings screen"

        # Simulate clicking Save — this used to crash with AttributeError
        event = FakeControlEvent(fake_page)
        save_button.on_click(event)

        # Verify SnackBar was set with the correct API
        assert fake_page.snack_bar is not None, (
            "SnackBar should be set on page.snack_bar"
        )
        assert fake_page.snack_bar.open is True, (
            "SnackBar.open should be True"
        )
        assert fake_page._updated is True, (
            "page.update() should have been called"
        )

        # Verify the snack bar content
        assert isinstance(fake_page.snack_bar, ft.SnackBar)
        assert fake_page.snack_bar.bgcolor == "#66A66B"

    def test_all_settings_tabs_render(self):
        """Every settings tab should render without errors."""
        from leadership_os.ui.widgets.settings_screen import build_settings_screen
        from leadership_os.config.config_manager import ConfigManager
        from leadership_os.core.event_bus import EventBus
        import tempfile, os
        from pathlib import Path

        tmpdir = tempfile.mkdtemp()
        config_path = Path(tmpdir) / "config.toml"
        config = ConfigManager(config_path)
        config.load()
        event_bus = EventBus()

        widget = build_settings_screen(
            config=config,
            event_bus=event_bus,
            on_close=lambda: None,
        )

        assert widget is not None


class TestAppSnackBarPattern:
    """Verify the SnackBar pattern used in app.py is correct."""

    def test_snackbar_pattern_works_with_fake_page(self):
        """The pattern: page.snack_bar = bar; page.snack_bar.open = True; page.update() should work."""
        fake_page = FakePage()

        # This is the exact pattern used in app.py _handle_review_finalize
        fake_page.snack_bar = ft.SnackBar(
            content=ft.Text("Test message", color="white", size=13),
            bgcolor="#C45B5B",
            duration=3000,
        )
        fake_page.snack_bar.open = True
        fake_page.update()

        assert fake_page.snack_bar is not None
        assert fake_page.snack_bar.open is True
        assert fake_page._updated is True

    def test_snackbar_content_is_keyword_arg(self):
        """ft.SnackBar in Flet 0.86 requires content= keyword, not positional."""
        # This should not raise
        bar = ft.SnackBar(
            content=ft.Text("Hello", color="white", size=13),
            bgcolor="#66A66B",
            duration=2000,
        )
        assert bar is not None
        assert bar.duration == 2000


# ─── Test: Carry-forward dialog builds without errors ────────────────

class TestCarryForwardBuilding:
    """Verify carry_forward_dialog builds without errors with various inputs."""

    def test_empty_list_renders(self):
        """Empty task list should render 'no unfinished tasks'."""
        from leadership_os.ui.widgets.carry_forward_dialog import build_carry_forward_dialog

        widget = build_carry_forward_dialog(
            tasks=[],
            on_continue=lambda t: None,
            on_archive=lambda t: None,
            on_delete=lambda t: None,
            on_done=lambda: None,
        )
        assert widget is not None

    def test_with_tasks_renders(self):
        """Should render tasks with action buttons."""
        from leadership_os.core.models import Task
        from leadership_os.ui.widgets.carry_forward_dialog import build_carry_forward_dialog

        task = Task(id="t1", day_id="d1", title="Test Task", priority="high", status="pending")
        widget = build_carry_forward_dialog(
            tasks=[task],
            task_day_map={"t1": "2026-07-20"},
            on_continue=lambda t: None,
            on_archive=lambda t: None,
            on_delete=lambda t: None,
            on_done=lambda: None,
        )
        assert widget is not None


# ─── Test: Break dialog builds without errors ────────────────────────

class TestBreakDialogBuilding:
    """Verify break_dialog builds without errors."""

    def test_break_dialog_renders(self):
        """Break dialog should render with type chips."""
        from leadership_os.ui.widgets.break_dialog import build_break_dialog

        widget = build_break_dialog(
            on_confirm=lambda bt, n: None,
            on_cancel=lambda: None,
        )
        assert widget is not None

    def test_break_options_are_valid(self):
        """All BREAK_OPTIONS should use valid BreakType values."""
        from leadership_os.ui.widgets.break_dialog import BREAK_OPTIONS
        from leadership_os.core.enums import BreakType

        valid = {e.value for e in BreakType}
        for opt in BREAK_OPTIONS:
            assert opt["value"] in valid
            assert "label" in opt
            assert "icon" in opt


# ─── Test: Execution panel with break params ─────────────────────────

class TestExecutionPanelBreak:
    """Verify execution_panel accepts break params without errors."""

    def test_panel_with_break_params(self):
        """Should render panel with break_type_label and break_elapsed."""
        from leadership_os.ui.widgets.execution_panel import build_execution_panel

        panel = build_execution_panel(
            current_task_title="Test Task",
            current_task_priority="HIGH",
            timer_display="00:05:30",
            timer_running=False,
            panel_state="break",
            session_elapsed="00:00",
            session_estimated="--:--",
            completed_count=3,
            total_count=5,
            progress_status="2 remaining",
            focus_time_display="1h 30m",
            next_task_title="Next Task",
            break_type_label="Lunch",
            break_elapsed="05:30",
        )
        assert panel is not None


# ─── Test: Task card with is_selected param ──────────────────────────

class TestTaskCardSelection:
    """Verify task_card supports is_selected parameter."""

    def test_selected_card_renders(self):
        """Should render with is_selected=True."""
        from leadership_os.ui.widgets.task_card import build_task_card

        card = build_task_card(
            task_id="t1",
            title="Task",
            priority="medium",
            status="pending",
            is_active=False,
            is_completed=False,
            is_selected=True,
        )
        assert card is not None
        assert card.bgcolor == "#1A1A30"

    def test_unselected_card_renders(self):
        """Should render with is_selected=False."""
        from leadership_os.ui.widgets.task_card import build_task_card

        card = build_task_card(
            task_id="t1",
            title="Task",
            priority="medium",
            status="pending",
            is_active=False,
            is_completed=False,
            is_selected=False,
        )
        assert card is not None
        assert card.bgcolor == "#15152B"


# ─── Test: All widget modules import cleanly ─────────────────────────

class TestAllWidgetsImport:
    """Verify all widget modules import without errors."""

    def test_all_widgets_import(self):
        """Every widget module should be importable."""
        modules = [
            "leadership_os.ui.widgets.task_card",
            "leadership_os.ui.widgets.task_form",
            "leadership_os.ui.widgets.settings_screen",
            "leadership_os.ui.widgets.execution_panel",
            "leadership_os.ui.widgets.sidebar",
            "leadership_os.ui.widgets.top_bar",
            "leadership_os.ui.widgets.status_bar",
            "leadership_os.ui.widgets.timer_display",
            "leadership_os.ui.widgets.progress_bar",
            "leadership_os.ui.widgets.review_screen",
            "leadership_os.ui.widgets.history_screen",
            "leadership_os.ui.widgets.command_palette",
            "leadership_os.ui.widgets.carry_forward_dialog",
            "leadership_os.ui.widgets.break_dialog",
        ]
        for mod_name in modules:
            __import__(mod_name)

    def test_all_core_modules_import(self):
        """Every core module should be importable."""
        modules = [
            "leadership_os.core.database",
            "leadership_os.core.models",
            "leadership_os.core.enums",
            "leadership_os.core.event_bus",
            "leadership_os.core.state_manager",
            "leadership_os.core.task_engine",
            "leadership_os.core.timer_engine",
            "leadership_os.core.break_engine",
            "leadership_os.core.journal_engine",
            "leadership_os.core.recovery",
            "leadership_os.core.instance_lock",
        ]
        for mod_name in modules:
            __import__(mod_name)


# ─── Helpers ─────────────────────────────────────────────────────────

def _find_button_by_text(container, label: str):
    """Walk a Flet widget tree to find a Button with given text."""
    if isinstance(container, ft.Button):
        if hasattr(container, "content") and container.content:
            c = container.content
            if isinstance(c, ft.Text) and c.value == label:
                return container
            # Check for Column/Row wrapping
            if hasattr(c, "controls"):
                for child in c.controls:
                    if isinstance(child, ft.Text) and child.value == label:
                        return container
    if hasattr(container, "content") and container.content:
        result = _find_button_by_text(container.content, label)
        if result:
            return result
    if hasattr(container, "controls"):
        for child in container.controls:
            result = _find_button_by_text(child, label)
            if result:
                return result
    return None
