"""Keyboard shortcuts handler for Leadership OS.

Provides a centralized keyboard event interceptor that maps key combinations
to application actions using the configured keyboard shortcuts from ConfigManager.

Design: The handler is attached to page.on_keyboard_event. It reads the keymap
from ConfigManager and dispatches to the appropriate app methods or EventBus.
"""

from __future__ import annotations

import logging
from collections.abc import Callable

import flet as ft

from leadership_os.config.config_manager import ConfigManager

logger = logging.getLogger(__name__)


class ShortcutHandler:
    """Centralized keyboard shortcut dispatcher.

    Maps keyboard combos (e.g., "ctrl+n") to named actions.
    Supports customizable shortcuts from ConfigManager with hardcoded fallbacks.

    Usage:
        handler = ShortcutHandler(config, action_map)
        page.on_keyboard_event = handler.handle
    """

    def __init__(
        self,
        config: ConfigManager,
        action_map: dict[str, Callable[[], None]],
    ) -> None:
        """Initialize the shortcut handler.

        Args:
            config: ConfigManager for reading configured shortcuts.
            action_map: Maps action names to callables.
                Keys: "create_task", "complete_task", "pause_task",
                      "start_break", "end_break", "end_day",
                      "command_palette", "settings", "undo", "escape"
        """
        self._config = config
        self._action_map = action_map

        # Hardcoded fallbacks for critical shortcuts
        self._fallbacks: dict[str, str] = {
            "create_task": "ctrl+n",
            "complete_task": "ctrl+enter",
            "pause_task": "ctrl+space",
            "start_break": "ctrl+b",
            "end_break": "ctrl+shift+b",
            "end_day": "ctrl+e",
            "command_palette": "ctrl+k",
            "settings": "ctrl+,",
            "escape": "escape",
        }

        # Build the reverse map: combo → action_name
        self._combo_map: dict[str, str] = {}
        self._rebuild_combo_map()

    def _rebuild_combo_map(self) -> None:
        """Rebuild the combo-to-action map from config or fallbacks."""
        self._combo_map.clear()
        keyboard_section = self._config.get_section("keyboard")

        for action_name, fallback_combo in self._fallbacks.items():
            # Config keys use underscores like the section keys
            config_key = _action_to_config_key(action_name)
            configured = keyboard_section.get(config_key, fallback_combo)
            self._combo_map[configured.lower().strip()] = action_name

    def reload_shortcuts(self) -> None:
        """Reload shortcuts from config (called after settings save)."""
        self._rebuild_combo_map()
        logger.info("Keyboard shortcuts reloaded from config")

    def handle(self, e: ft.KeyboardEvent) -> bool:
        """Handle a keyboard event. Return True to mark event handled.

        This is the callback attached to page.on_keyboard_event.
        """
        # Build a normalized combo string from the event
        combo = _event_to_combo(e)

        # Check if this combo maps to an action
        action_name = self._combo_map.get(combo)
        if action_name is None:
            return False

        # Dispatch the action
        action_fn = self._action_map.get(action_name)
        if action_fn is not None:
            try:
                action_fn()
                logger.debug("Shortcut dispatched: %s → %s", combo, action_name)
                return True
            except Exception as exc:
                logger.error(
                    "Error executing shortcut %s (%s): %s",
                    combo, action_name, exc, exc_info=True,
                )
        return False


def _event_to_combo(e: ft.KeyboardEvent) -> str:
    """Convert a Flet KeyboardEvent to a normalized combo string.

    Examples:
        Ctrl+N → "ctrl+n"
        Ctrl+Shift+B → "ctrl+shift+b"
        Escape → "escape"
        Enter → "enter"
    """
    parts: list[str] = []

    if e.ctrl:
        parts.append("ctrl")
    if e.alt:
        parts.append("alt")
    if e.shift:
        parts.append("shift")
    if e.meta:
        parts.append("meta")

    key = e.key.lower().strip()
    if key:
        # Skip modifier-only combos
        if key in ("control", "ctrl", "shift", "alt", "meta"):
            return ""
        parts.append(key)

    return "+".join(parts) if parts else ""


def _action_to_config_key(action_name: str) -> str:
    """Map internal action names to config keys.

    Actions: "create_task" → "create_task"
             "complete_task" → "complete_task"
             "pause_task" → "pause_task"
             "start_break" → "start_break"
             "end_break" → "end_break"
             "end_day" → "end_day"
             "command_palette" → "command_palette"
             "settings" → "settings"
             "escape" → "escape"
    """
    return action_name
