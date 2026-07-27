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
