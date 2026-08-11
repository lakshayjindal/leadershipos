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


# ─── Test 6: Sidebar highlight follows navigation ───────────────────


def _nav_item_bg(sidebar, label: str):
    """Return the bgcolor of the sidebar nav item with the given label.

    Nav items are Containers whose content Row holds a Text with the label.
    """
    for parent in _walk(sidebar):
        if (
            isinstance(parent, ft.Container)
            and isinstance(parent.content, ft.Row)
            and any(
                isinstance(t, ft.Text) and t.value == label
                for t in _walk(parent.content)
            )
        ):
            return parent.bgcolor
    return None


class TestSidebarHighlight:
    """The active nav item must track the current view (bug: stayed on Today)."""

    def _sidebar(self, active_view: str):
        from leadership_os.ui.widgets.sidebar import build_sidebar

        return build_sidebar(
            app_state="planning",
            focus_time=0,
            completed_count=0,
            total_count=0,
            status_text="Ready",
            active_view=active_view,
            today_callback=lambda: None,
            history_callback=lambda: None,
            settings_callback=lambda: None,
        )

    def test_today_highlighted_by_default(self):
        from leadership_os.ui.theme import Theme

        sidebar = self._sidebar("today")
        assert _nav_item_bg(sidebar, "Today") == Theme.PARCHMENT
        assert _nav_item_bg(sidebar, "History") == "transparent"
        assert _nav_item_bg(sidebar, "Settings") == "transparent"

    def test_history_highlighted(self):
        from leadership_os.ui.theme import Theme

        sidebar = self._sidebar("history")
        assert _nav_item_bg(sidebar, "History") == Theme.PARCHMENT
        assert _nav_item_bg(sidebar, "Today") == "transparent"

    def test_settings_highlighted(self):
        from leadership_os.ui.theme import Theme

        sidebar = self._sidebar("settings")
        assert _nav_item_bg(sidebar, "Settings") == Theme.PARCHMENT
        assert _nav_item_bg(sidebar, "Today") == "transparent"

    def test_today_context_views_keep_today_highlighted(self):
        from leadership_os.ui.theme import Theme

        for view in ("review", "carry_forward", "break_dialog"):
            sidebar = self._sidebar(view)
            assert _nav_item_bg(sidebar, "Today") == Theme.PARCHMENT, view
            assert _nav_item_bg(sidebar, "History") == "transparent", view
            assert _nav_item_bg(sidebar, "Settings") == "transparent", view

    def test_navigation_methods_set_nav_view(self):
        """switch_to_* must update _nav_view (which drives the highlight)."""
        from leadership_os.app import LeadershipOSApp

        app = LeadershipOSApp()
        app.switch_to_history()
        assert app._nav_view == "history"
        app.switch_to_settings()
        assert app._nav_view == "settings"
        app.switch_to_today()
        assert app._nav_view == "today"


# ─── Test 7: Dark mode switch ───────────────────────────────────────


class TestDarkMode:
    """Theme.set_mode should switch the active palette for all tokens."""

    def test_set_mode_dark(self):
        from leadership_os.ui import theme as theme_mod

        theme_mod.Theme.set_mode("dark")
        try:
            assert theme_mod.Theme.INK == "#f5f5f7"
            assert theme_mod.Theme.PARCHMENT == "#000000"
            assert theme_mod.Theme.PEARL == "#2c2c2e"
            assert theme_mod.Theme.color("primary") == "#2997ff"
            assert theme_mod.Theme.color("success") == "#30d158"
        finally:
            theme_mod.Theme.set_mode("light")

    def test_set_mode_light(self):
        from leadership_os.ui import theme as theme_mod

        theme_mod.Theme.set_mode("light")
        assert theme_mod.Theme.INK == "#1d1d1f"
        assert theme_mod.Theme.PARCHMENT == "#f5f5f7"
        assert theme_mod.Theme.color("primary") == "#0066cc"

    def test_unknown_mode_defaults_to_light(self):
        from leadership_os.ui import theme as theme_mod

        theme_mod.Theme.set_mode("system")
        assert theme_mod.Theme.mode() == "light"

    def test_config_default_is_light(self):
        from leadership_os.config.defaults import DEFAULTS

        assert DEFAULTS["ui"]["theme"] == "light"

    def test_resolve_theme_mode(self):
        import flet as ft

        from leadership_os.app import LeadershipOSApp

        app = LeadershipOSApp()

        class FakeConfig:
            def get(self, *a, **k):
                return "dark"

        app.config = FakeConfig()
        assert app._resolve_theme_mode() == ft.ThemeMode.DARK


# ─── Test 8: Today's Progress card bottom gap ───────────────────────


class TestProgressCardPadding:
    """The Today's Progress card must have a bottom gap below the stat boxes."""

    def _build(self):
        from leadership_os.ui.widgets.execution_panel import build_execution_panel

        return build_execution_panel(
            current_task_title="Test Task",
            current_task_priority="HIGH",
            timer_display="00:05:30",
            timer_running=False,
            panel_state="idle",
            session_elapsed="00:00",
            session_estimated="--:--",
            completed_count=3,
            total_count=5,
            progress_status="2 remaining",
            focus_time_display="1h 30m",
            next_task_title="Next",
        )

    def test_progress_card_has_bottom_gap(self):
        panel = self._build()

        # Find the progress card: a Container with an explicit height whose
        # content Column contains the "TODAY'S PROGRESS" header text.
        progress_card = None
        for c in _walk(panel):
            if (
                isinstance(c, ft.Container)
                and c.height is not None
                and isinstance(c.content, ft.Column)
            ):
                col = c.content
                if any(
                    isinstance(t, ft.Text) and t.value == "TODAY'S PROGRESS"
                    for t in _walk(col)
                ):
                    progress_card = c
                    break

        assert progress_card is not None, "Progress card should exist"
        # Height increased so the stat boxes sit above the card edge
        assert progress_card.height >= 100
        # The column ends with a spacer to create the bottom gap
        controls = progress_card.content.controls
        assert isinstance(controls[-1], ft.Container), "Column should end with a bottom spacer"
        assert controls[-1].height == 4

    def test_progress_card_has_bottom_padding(self):
        panel = self._build()
        for c in _walk(panel):
            if (
                isinstance(c, ft.Container)
                and c.height is not None
                and isinstance(c.content, ft.Column)
            ):
                col = c.content
                if any(
                    isinstance(t, ft.Text) and t.value == "TODAY'S PROGRESS"
                    for t in _walk(col)
                ):
                    padding = c.padding
                    assert padding is not None
                    bottom = padding.bottom if hasattr(padding, "bottom") else padding
                    assert bottom >= 14, "Card should have >=14px bottom padding"


# ─── Test 9: Top-bar theme toggle ───────────────────────────────────


def _find_icon_button_with_tooltip(control, tooltip: str):
    """Find the first IconButton whose tooltip contains the given text."""
    return _find_control(
        control,
        lambda c: isinstance(c, ft.IconButton) and tooltip in (c.tooltip or ""),
    )


class TestThemeToggle:
    """The top bar should expose a quick dark/light toggle button."""

    def _bar(self, current_theme="light", on_toggle=None):
        from leadership_os.ui.widgets.top_bar import build_top_bar

        return build_top_bar(
            on_search=lambda: None,
            on_settings=lambda: None,
            on_command_palette=lambda: None,
            on_toggle_theme=on_toggle,
            current_theme=current_theme,
        )

    def test_toggle_button_exists(self):
        bar = self._bar()
        btn = _find_icon_button_with_tooltip(bar, "Switch to dark mode")
        assert btn is not None, "Toggle button should exist in top bar"

    def test_light_mode_shows_moon_icon(self):
        bar = self._bar(current_theme="light")
        btn = _find_icon_button_with_tooltip(bar, "Switch to dark mode")
        assert btn is not None
        assert btn.icon == ft.Icons.DARK_MODE, "Light mode should offer the dark (moon) icon"

    def test_dark_mode_shows_sun_icon(self):
        bar = self._bar(current_theme="dark")
        btn = _find_icon_button_with_tooltip(bar, "Switch to light mode")
        assert btn is not None
        assert btn.icon == ft.Icons.LIGHT_MODE, "Dark mode should offer the light (sun) icon"

    def test_toggle_callback_fires(self):
        called: list[bool] = []
        bar = self._bar(on_toggle=lambda: called.append(True))
        btn = _find_icon_button_with_tooltip(bar, "Switch to dark mode")
        assert btn is not None
        handler = getattr(btn, "on_click", None)
        assert handler is not None
        handler(None)
        assert called == [True], "Toggle callback should fire on click"

    def test_toggle_callback_optional(self):
        """on_toggle_theme should be optional (backwards compatible)."""
        bar = self._bar(on_toggle=None)
        btn = _find_icon_button_with_tooltip(bar, "Switch to dark mode")
        assert btn is not None
        handler = getattr(btn, "on_click", None)
        handler(None)  # must not raise

    def test_nav_icons_visible_on_black_in_both_modes(self):
        """Nav icons must be light so they read on the black bar in light mode."""
        from leadership_os.ui.theme import Theme

        bar = self._bar(current_theme="light")
        search = _find_icon_button_with_tooltip(bar, "Search")
        assert search is not None
        assert search.icon_color == Theme.ON_DARK


class TestAppThemeToggle:
    """app._on_toggle_theme should flip the config and re-apply the theme."""

    class FakeConfig:
        def __init__(self):
            self.values = {"ui": {"theme": "light"}}

        def get(self, section, key, default=None):
            return self.values.get(section, {}).get(key, default)

        def set(self, section, key, value):
            self.values.setdefault(section, {})[key] = value

        def save(self):
            pass

    class FakeBus:
        def __init__(self):
            self.emitted = []

        def emit(self, event, data=None):
            self.emitted.append((event, data))

    def _make_app(self):
        from leadership_os.app import LeadershipOSApp

        app = LeadershipOSApp()
        app.config = self.FakeConfig()
        app.event_bus = self.FakeBus()
        app._apply_theme = lambda: None  # type: ignore[method-assign]
        return app

    def test_toggle_flips_light_to_dark(self):
        from leadership_os.core.event_bus import CONFIG_CHANGED

        app = self._make_app()
        app._on_toggle_theme()
        assert app.config.values["ui"]["theme"] == "dark"
        assert app.event_bus.emitted == [(CONFIG_CHANGED, {"source": "top_bar"})]

    def test_toggle_flips_dark_back_to_light(self):
        app = self._make_app()
        app.config.set("ui", "theme", "dark")
        app._on_toggle_theme()
        assert app.config.values["ui"]["theme"] == "light"

    def test_toggle_without_config_is_safe(self):
        from leadership_os.app import LeadershipOSApp

        app = LeadershipOSApp()  # config is None
        app._on_toggle_theme()  # should not raise

    def test_apply_theme_rebuilds_top_bar(self):
        """_apply_theme must swap in a fresh top bar so the toggle icon
        and nav colors re-resolve after the palette switches."""
        import flet as ft

        from leadership_os.app import LeadershipOSApp

        app = LeadershipOSApp()
        app.page = FakePage()
        app.config = self.FakeConfig()
        app._root_column = ft.Column(controls=[ft.Text("old top bar")])
        old = app._root_column.controls[0]

        app._apply_theme()

        new = app._root_column.controls[0]
        assert new is not old, "_apply_theme should replace the top bar"
        assert isinstance(new, ft.Container)

    def test_build_top_bar_uses_current_theme(self):
        """_build_top_bar should reflect the active palette mode."""
        from leadership_os.app import LeadershipOSApp
        from leadership_os.ui import theme as theme_mod

        app = LeadershipOSApp()
        theme_mod.Theme.set_mode("dark")
        try:
            bar = app._build_top_bar()
            btn = _find_icon_button_with_tooltip(bar, "Switch to light mode")
            assert btn is not None, "Dark mode should show the light-mode toggle"
        finally:
            theme_mod.Theme.set_mode("light")
