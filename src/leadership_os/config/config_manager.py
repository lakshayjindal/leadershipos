"""Configuration manager for Leadership OS.

Responsibilities:
- Load configuration from TOML file
- Save configuration to TOML file
- Provide defaults for missing values
- Validate configuration values
- Handle import/export

Design principle: Configuration should influence behavior, not implementation.
"""

from __future__ import annotations

import logging

try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib
from pathlib import Path
from typing import Any

try:
    import tomli_w
except ImportError:
    tomli_w = None  # type: ignore[assignment]

from leadership_os.config.defaults import DEFAULTS, get_default

logger = logging.getLogger(__name__)


class ConfigManager:
    """Manages application configuration via TOML files.

    Usage:
        config = ConfigManager(Path("data/config.toml"))
        config.load()
        theme = config.get("ui", "theme")
        config.set("ui", "theme", "light")
        config.save()
    """

    def __init__(self, config_path: Path) -> None:
        self.config_path = config_path
        self._data: dict[str, dict[str, Any]] = {}
        self._loaded = False

    def load(self) -> None:
        """Load configuration from file, merging with defaults."""
        self._data = self._deep_copy_defaults()

        if self.config_path.exists():
            try:
                with open(self.config_path, "rb") as f:
                    file_data = tomllib.load(f)
                # Merge file data into defaults (file overrides defaults)
                for section, values in file_data.items():
                    if isinstance(values, dict):
                        if section not in self._data:
                            self._data[section] = {}
                        self._data[section].update(values)
                self._loaded = True
                logger.info("Configuration loaded from %s", self.config_path)
            except Exception as e:
                logger.warning("Failed to load config from %s: %s", self.config_path, e)
                self._loaded = True
        else:
            # No config file — use defaults and save
            self.save()
            self._loaded = True
            logger.info("Created default configuration at %s", self.config_path)

    def save(self) -> None:
        """Save current configuration to file."""
        if tomli_w is None:
            raise RuntimeError("tomli_w is required for saving configuration")
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_path, "wb") as f:
            tomli_w.dump(self._data, f)
        logger.info("Configuration saved to %s", self.config_path)

    def get(self, section: str, key: str, fallback: Any = None) -> Any:
        """Get a configuration value. Returns default if not set."""
        if not self._loaded:
            self.load()
        value = self._data.get(section, {}).get(key)
        if value is None:
            return get_default(section, key) if fallback is None else fallback
        return value

    def get_section(self, section: str) -> dict[str, Any]:
        """Get all values for a configuration section."""
        if not self._loaded:
            self.load()
        defaults = DEFAULTS.get(section, {}).copy()
        current = self._data.get(section, {}).copy()
        defaults.update(current)
        return defaults

    def set(self, section: str, key: str, value: Any) -> None:
        """Set a configuration value (in memory only — call save() to persist)."""
        if not self._loaded:
            self.load()
        if section not in self._data:
            self._data[section] = {}
        self._data[section][key] = value

    def set_section(self, section: str, values: dict[str, Any]) -> None:
        """Set multiple values for a configuration section."""
        if not self._loaded:
            self.load()
        if section not in self._data:
            self._data[section] = {}
        self._data[section].update(values)

    def reset(self) -> None:
        """Reset all configuration to defaults and save."""
        self._data = self._deep_copy_defaults()
        self.save()
        logger.info("Configuration reset to defaults")

    def export_config(self) -> dict[str, dict[str, Any]]:
        """Export current configuration as a dictionary."""
        if not self._loaded:
            self.load()
        return self._deep_copy(self._data)

    def import_config(self, data: dict[str, dict[str, Any]]) -> None:
        """Import configuration from a dictionary."""
        self._data = self._deep_copy(data)
        self.save()
        logger.info("Configuration imported")

    def validate(self) -> list[str]:
        """Validate current configuration. Returns list of error messages."""
        errors: list[str] = []

        # Validate theme
        theme = self.get("ui", "theme")
        if theme not in ("dark", "light", "system"):
            errors.append(f"Invalid theme: {theme!r}")

        # Validate overlay opacity
        opacity = self.get("ui", "overlay_opacity")
        if not isinstance(opacity, (int, float)) or not (0.0 <= opacity <= 1.0):
            errors.append(f"Invalid overlay opacity: {opacity!r}")

        # Validate time formats
        for section, key in [
            ("work_schedule", "start_time"),
            ("work_schedule", "end_time"),
            ("work_schedule", "lunch_time"),
            ("work_schedule", "dinner_time"),
            ("notifications", "end_of_day_time"),
        ]:
            time_val = self.get(section, key)
            if time_val and not self._is_valid_time(time_val):
                errors.append(f"Invalid time format for {section}.{key}: {time_val!r}")

        # Validate deadline reminder minutes
        reminder = self.get("notifications", "deadline_reminder_minutes")
        if not isinstance(reminder, int) or reminder < 0:
            errors.append(f"Invalid deadline reminder minutes: {reminder!r}")

        return errors

    @staticmethod
    def _is_valid_time(time_str: str) -> bool:
        """Check if a string is a valid HH:MM time format."""
        try:
            parts = time_str.split(":")
            if len(parts) != 2:
                return False
            hour, minute = int(parts[0]), int(parts[1])
            return 0 <= hour <= 23 and 0 <= minute <= 59
        except (ValueError, IndexError):
            return False

    @staticmethod
    def _deep_copy_defaults() -> dict[str, dict[str, Any]]:
        """Deep copy the defaults dictionary."""
        return {section: dict(values) for section, values in DEFAULTS.items()}

    @staticmethod
    def _deep_copy(data: dict[str, dict[str, Any]]) -> dict[str, dict[str, Any]]:
        """Deep copy a nested dictionary."""
        return {section: dict(values) for section, values in data.items()}
