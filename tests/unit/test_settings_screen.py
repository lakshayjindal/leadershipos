"""Tests for the settings screen."""

from __future__ import annotations

import flet as ft

from leadership_os.config.config_manager import ConfigManager
from leadership_os.ui.widgets.settings_screen import build_settings_screen


class TestBuildSettingsScreen:
    def test_build_returns_container(self, config: ConfigManager, event_bus):
        screen = build_settings_screen(
            config,
            event_bus,
            on_close=lambda: None,
        )
        assert isinstance(screen, ft.Container)

    def test_close_callback_invoked(self, config: ConfigManager, event_bus):
        calls = []

        def on_close():
            calls.append("close")

        screen = build_settings_screen(config, event_bus, on_close=on_close)
        # Locate the close IconButton in the header row
        header_container = screen.content.controls[0]
        close_button = header_container.content.controls[2]
        close_button.on_click(None)
        assert "close" in calls


# ─── Helpers ─────────────────────────────────────────────────────────


def _walk(control):
    """Yield a control and all its descendants."""
    yield control
    if hasattr(control, "content") and control.content is not None:
        yield from _walk(control.content)
    if hasattr(control, "controls"):
        for child in control.controls:
            yield from _walk(child)


def _find_save_button(screen):
    """Find the Save Settings button in the settings screen tree."""
    for c in _walk(screen):
        if isinstance(c, ft.Button):
            content = getattr(c, "content", None)
            if isinstance(content, ft.Text) and "Save Settings" in (content.value or ""):
                return c
    return None


class _DetachedEvent:
    """Simulates Flet's click event after a CONFIG_CHANGED rebuild.

    The clicked button has been detached from the page tree by the time the
    handler continues, so accessing ``e.page`` raises the exact RuntimeError
    seen in production.
    """

    @property
    def page(self):
        raise RuntimeError("Control must be added to the page first")


class _FakeSettingsPage:
    """Minimal page stub that records the snackbar."""

    def __init__(self):
        self.snack_bar = None
        self.updated = False

    def update(self):
        self.updated = True


class TestSaveAfterThemeRebuild:
    """Saving settings must not crash after CONFIG_CHANGED rebuilds the UI.

    Regression: on_save used ``e.page``, but the synchronous CONFIG_CHANGED
    emit detaches the clicked button first, raising
    ``RuntimeError: Control must be added to the page first``.
    """

    def test_save_uses_injected_page_not_e_page(self, config: ConfigManager, event_bus):
        page = _FakeSettingsPage()
        screen = build_settings_screen(
            config,
            event_bus,
            on_close=lambda: None,
            page=page,
        )
        save_btn = _find_save_button(screen)
        assert save_btn is not None

        # Even though e.page raises (button detached after rebuild), the
        # handler must not touch it — the snackbar goes to the injected page.
        save_btn.on_click(_DetachedEvent())

        assert page.snack_bar is not None, "Snackbar should be shown via the injected page"
        assert page.updated is True
        assert config.get("ui", "theme") == "light"  # saved without crashing

    def test_save_without_page_is_safe(self, config: ConfigManager, event_bus):
        """page is optional — the snackbar is simply skipped."""
        screen = build_settings_screen(
            config,
            event_bus,
            on_close=lambda: None,
        )
        save_btn = _find_save_button(screen)
        assert save_btn is not None
        save_btn.on_click(_DetachedEvent())  # must not raise
