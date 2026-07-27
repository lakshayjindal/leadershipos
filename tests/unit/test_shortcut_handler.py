"""Tests for the keyboard shortcut handler."""

from __future__ import annotations

import flet as ft
import pytest

from leadership_os.config.config_manager import ConfigManager
from leadership_os.ui.shortcut_handler import ShortcutHandler, _event_to_combo


@pytest.fixture
def config(tmp_path):
    cfg = ConfigManager(tmp_path / "config.toml")
    cfg.load()
    return cfg


def _make_event(*, key="a", name="", control=None, ctrl=False, shift=False, alt=False, meta=False):
    # Support both old and current Flet signatures
    if control is None:
        control = ctrl
    return ft.KeyboardEvent(name=name, key=key, control=control, ctrl=ctrl, shift=shift, alt=alt, meta=meta)


class TestEventToCombo:
    def test_simple_key(self):
        e = _make_event(key="n")
        assert _event_to_combo(e) == "n"

    def test_ctrl_combo(self):
        e = _make_event(key="n", ctrl=True)
        assert _event_to_combo(e) == "ctrl+n"

    def test_ctrl_shift_combo(self):
        e = _make_event(key="b", ctrl=True, shift=True)
        assert _event_to_combo(e) == "ctrl+shift+b"

    def test_escape(self):
        e = _make_event(key="Escape")
        assert _event_to_combo(e) == "escape"

    def test_modifier_only_returns_empty(self):
        e = _make_event(key="control", ctrl=True)
        assert _event_to_combo(e) == ""


class TestShortcutHandler:
    def test_dispatch_create_task(self, config: ConfigManager):
        actions_called = []

        def create_task():
            actions_called.append("create_task")

        handler = ShortcutHandler(config, {"create_task": create_task})
        e = _make_event(key="n", ctrl=True)
        handled = handler.handle(e)
        assert handled is True
        assert actions_called == ["create_task"]

    def test_unmapped_combo_returns_false(self, config: ConfigManager):
        handler = ShortcutHandler(config, {})
        e = _make_event(key="z", ctrl=True)
        assert handler.handle(e) is False

    def test_action_error_is_caught(self, config: ConfigManager):
        def raise_error():
            raise RuntimeError("boom")

        handler = ShortcutHandler(config, {"create_task": raise_error})
        e = _make_event(key="n", ctrl=True)
        # Should not propagate exception; handler returns False when action fails
        handled = handler.handle(e)
        assert handled is False

    def test_reload_shortcuts(self, config: ConfigManager):
        # Override a shortcut in config
        config.set("keyboard", "create_task", "ctrl+t")
        handler = ShortcutHandler(config, {"create_task": lambda: None})
        # After reload, ctrl+t should map to create_task
        handler.reload_shortcuts()
        e = _make_event(key="t", ctrl=True)
        assert handler.handle(e) is True

    def test_case_insensitive(self, config: ConfigManager):
        handler = ShortcutHandler(config, {"command_palette": lambda: None})
        e = _make_event(key="K", ctrl=True)
        assert handler.handle(e) is True
