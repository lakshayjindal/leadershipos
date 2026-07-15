"""Default configuration values for Leadership OS.

These defaults are used when no config file exists or when a config key
is missing. The defaults reflect common working patterns rather than edge cases.
"""

from __future__ import annotations

from typing import Any

# ─── Default Configuration ────────────────────────────────────────────

DEFAULTS: dict[str, dict[str, Any]] = {
    "work_schedule": {
        "start_time": "09:00",
        "end_time": "18:00",
        "lunch_time": "13:00",
        "dinner_time": "19:00",
        "work_days": ["monday", "tuesday", "wednesday", "thursday", "friday"],
    },
    "ui": {
        "theme": "dark",
        "overlay_opacity": 0.85,
        "overlay_position_x": -1,
        "overlay_position_y": 40,
        "show_overlay": True,
    },
    "journaling": {
        "vault_path": "~/Documents/Obsidian",
        "journal_dir": "Daily Notes",
        "filename_format": "YYYY-MM-DD.md",
    },
    "notifications": {
        "enabled": True,
        "deadline_reminder_minutes": 30,
        "break_reminder": False,
        "end_of_day_time": "17:30",
        "do_not_disturb_start": "",
        "do_not_disturb_end": "",
    },
    "keyboard": {
        "create_task": "ctrl+n",
        "complete_task": "ctrl+enter",
        "pause_task": "ctrl+space",
        "start_break": "ctrl+b",
        "end_break": "ctrl+shift+b",
        "end_day": "ctrl+e",
        "settings": "ctrl+,",
        "command_palette": "ctrl+k",
    },
    "startup": {
        "launch_at_system_startup": False,
        "restore_previous_session": True,
        "minimize_to_tray": True,
        "open_overlay_on_start": True,
    },
}


def get_default(section: str, key: str) -> Any:
    """Get a default value by section and key."""
    return DEFAULTS.get(section, {}).get(key)


def get_section_defaults(section: str) -> dict[str, Any]:
    """Get all defaults for a section."""
    return DEFAULTS.get(section, {}).copy()
