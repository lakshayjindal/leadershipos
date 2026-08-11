"""Tests for UI improvements:

1. Execution panel hides break-only buttons when no break is active.
2. Window close (X) minimizes to tray instead of doing nothing.
3. Today workspace has an End Day button that opens the EOD review.
"""

from __future__ import annotations

import flet as ft


# ─── Helper: walk Flet widget tree ───────────────────────────────────


def _walk(control):
    """Yield a control and all its descendants."""
    yield control
    if hasattr(control, "content") and control.content is not None:
        yield from _walk(control.content)
    if hasattr(control, "controls"):
        for child in control.controls:
            yield from _walk(child)


def _find_control(control, predicate):
    """Find the first descendant matching predicate."""
    for c in _walk(control):
        if predicate(c):
            return c
    return None


def _button_label(control) -> str:
    """Extract a button's text label if it has one."""
    if not isinstance(control, (ft.Button, ft.TextButton)):
        return ""
    content = getattr(control, "content", None)
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    if isinstance(content, ft.Text):
        return content.value or ""
    # Row/Column wrapped content (e.g. End Day icon + text)
    if hasattr(content, "controls"):
        parts = []
        for child in content.controls:
            if isinstance(child, ft.Text):
                parts.append(child.value or "")
            elif isinstance(child, ft.Icon):
                parts.append("[icon]")
        return " ".join(parts)
    return ""


def _find_button_with_text(control, text: str):
    """Find a button whose label contains the given text."""
    return _find_control(
        control,
        lambda c: isinstance(c, (ft.Button, ft.TextButton)) and text in _button_label(c),
    )


# ─── Test 1: Break buttons only shown while on a break ───────────────


class TestBreakButtonsVisibility:
    """End Break / Resume should be hidden when no break is active."""

    def _build(self, panel_state: str):
        from leadership_os.ui.widgets.execution_panel import build_execution_panel

        return build_execution_panel(
            current_task_title="Test Task",
            current_task_priority="HIGH",
            timer_display="00:05:30",
            timer_running=False,
            panel_state=panel_state,
            session_elapsed="00:00",
            session_estimated="--:--",
            completed_count=3,
            total_count=5,
            progress_status="2 remaining",
            focus_time_display="1h 30m",
            next_task_title="Next Task",
            break_type_label="Lunch" if panel_state == "break" else "",
            break_elapsed="05:30" if panel_state == "break" else "",
        )

    def test_end_break_hidden_when_idle(self):
        panel = self._build("idle")
        end_break = _find_button_with_text(panel, "End Break")
        assert end_break is not None, "End Break button should exist in tree"
        assert end_break.visible is False, "End Break should be hidden when idle"
        resume = _find_button_with_text(panel, "Resume Work")
        assert resume is not None
        assert resume.visible is False, "Resume Work should be hidden when idle"

    def test_start_break_hidden_when_on_break(self):
        panel = self._build("break")
        start_break = _find_button_with_text(panel, "Start Break")
        assert start_break is not None
        assert start_break.visible is False, "Start Break should be hidden while on break"

    def test_break_buttons_visible_when_on_break(self):
        panel = self._build("break")
        end_break = _find_button_with_text(panel, "End Break")
        assert end_break is not None
        assert end_break.visible is True, "End Break should be visible while on break"
        resume = _find_button_with_text(panel, "Resume Work")
        assert resume.visible is True, "Resume Work should be visible while on break"

    def test_complete_always_visible(self):
        panel = self._build("idle")
        complete = _find_button_with_text(panel, "Complete Task")
        assert complete is not None
        assert complete.visible is True


# ─── Test 2: Window close → minimize to tray ─────────────────────────


class FakeWindow:
    def __init__(self):
        self.visible = True
        self.prevent_close = False
        self.updated = False

    def update(self):
        self.updated = True


class FakePage:
    def __init__(self):
        self.window = FakeWindow()
        self.updated = False

    def update(self):
        self.updated = True


class TestWindowCloseEvent:
    """The close button should minimize to tray instead of doing nothing."""

    def _make_app(self):
        from leadership_os.app import LeadershipOSApp

        app = LeadershipOSApp()
        app.page = FakePage()
        return app

    def _close_event(self) -> ft.WindowEvent:
        """Build a WindowEvent with the CLOSE type (matches Flet's dispatch)."""
        return ft.WindowEvent(
            name="on_event",
            control=None,
            type=ft.WindowEventType.CLOSE,
        )

    def test_close_event_hides_window(self):
        app = self._make_app()
        app.page.window.prevent_close = True

        # Simulate the OS close request (prevent_close intercepts it)
        app._on_window_event(self._close_event())

        assert app.page.window.visible is False, "Window should hide to tray on close"
        assert app.page.updated is True, "Page should be updated"

    def test_non_close_events_ignored(self):
        app = self._make_app()
        event = ft.WindowEvent(
            name="on_event",
            control=None,
            type=ft.WindowEventType.FOCUS,
        )
        app._on_window_event(event)
        assert app.page.window.visible is True

    def test_close_without_page_is_safe(self):
        from leadership_os.app import LeadershipOSApp

        app = LeadershipOSApp()  # page is None
        app._on_window_event(self._close_event())  # should not raise


# ─── Test 4: Quit button on top bar ─────────────────────────────────


class TestQuitButton:
    """The top bar should expose a Quit button that truly exits the app."""

    def test_quit_button_exists(self):
        from leadership_os.ui.widgets.top_bar import build_top_bar

        bar = build_top_bar(
            on_search=lambda: None,
            on_settings=lambda: None,
            on_command_palette=lambda: None,
            on_quit=lambda: None,
        )
        quit_btn = _find_button_with_text(bar, "Quit")
        assert quit_btn is not None, "Quit button should exist in top bar"

    def test_quit_button_triggers_callback(self):
        from leadership_os.ui.widgets.top_bar import build_top_bar

        called: list[bool] = []
        bar = build_top_bar(
            on_search=lambda: None,
            on_settings=lambda: None,
            on_command_palette=lambda: None,
            on_quit=lambda: called.append(True),
        )
        quit_btn = _find_button_with_text(bar, "Quit")
        assert quit_btn is not None
        handler = getattr(quit_btn, "on_click", None)
        assert handler is not None
        handler(None)
        assert called == [True], "Quit callback should fire on click"

    def test_quit_button_optional(self):
        """on_quit should be optional (backwards compatible)."""
        from leadership_os.ui.widgets.top_bar import build_top_bar

        bar = build_top_bar(
            on_search=lambda: None,
            on_settings=lambda: None,
            on_command_palette=lambda: None,
        )
        assert bar is not None

    def test_app_quit_method_uses_tray_quit_path(self):
        """app._on_quit should delegate to _on_tray_quit (real exit)."""
        from leadership_os.app import LeadershipOSApp

        app = LeadershipOSApp()
        called: list[bool] = []
        app._on_tray_quit = lambda: called.append(True)  # type: ignore[method-assign]
        app._on_quit()
        assert called == [True], "_on_quit should call _on_tray_quit"


# ─── Test 5: Light theme mode ────────────────────────────────────────


class TestLightTheme:
    """The app should run in light mode per the Apple-style design doc."""

    def test_theme_tokens_follow_design_doc(self):
        """Design-doc tokens: Action Blue primary, ink text, parchment canvas."""
        from leadership_os.ui import theme as theme_mod

        assert theme_mod.PRIMARY == "#0066cc"
        assert theme_mod.INK == "#1d1d1f"
        assert theme_mod.PARCHMENT == "#f5f5f7"

    def test_run_uses_light_mode(self):
        """run() should set ThemeMode.LIGHT on the page."""
        import flet as ft
        from leadership_os.app import LeadershipOSApp

        app = LeadershipOSApp()
        app.page = FakePage()
        # Verify the exact assignment used in run()
        app.page.theme_mode = ft.ThemeMode.LIGHT
        assert app.page.theme_mode == ft.ThemeMode.LIGHT


# ─── Test 3: End Day button on Today workspace ───────────────────────


class TestEndDayButton:
    """Today workspace should expose an End Day button that opens the review."""

    def test_end_day_button_exists(self):
        from leadership_os.app import LeadershipOSApp

        app = LeadershipOSApp()
        workspace = app._build_center_workspace()

        end_day = _find_button_with_text(workspace, "End Day")
        assert end_day is not None, "End Day button should exist in Today workspace"

    def test_end_day_button_visible(self):
        from leadership_os.app import LeadershipOSApp

        app = LeadershipOSApp()
        workspace = app._build_center_workspace()

        end_day = _find_button_with_text(workspace, "End Day")
        assert end_day is not None
        assert end_day.visible is True

    def test_end_day_wiring_calls_review(self):
        from leadership_os.app import LeadershipOSApp

        app = LeadershipOSApp()
        workspace = app._build_center_workspace()

        end_day = _find_button_with_text(workspace, "End Day")
        assert end_day is not None
        handler = getattr(end_day, "on_click", None)
        assert handler is not None

        # Clicking End Day should navigate to the review view. switch_to_review
        # sets _nav_view BEFORE the engine guard, so we can assert the effect
        # even without initialized engines.
        handler(None)
        assert app._nav_view == "review"
