"""Tests for Leadership OS configuration manager."""

import pytest
from pathlib import Path

from leadership_os.config.config_manager import ConfigManager


class TestConfigManager:
    def test_load_creates_default_config(self, tmp_dir: Path):
        config = ConfigManager(tmp_dir / "config.toml")
        config.load()
        assert (tmp_dir / "config.toml").exists()

    def test_get_returns_default(self, config: ConfigManager):
        theme = config.get("ui", "theme")
        assert theme == "dark"

    def test_get_returns_fallback(self, config: ConfigManager):
        value = config.get("nonexistent", "key", fallback="default")
        assert value == "default"

    def test_set_and_get(self, config: ConfigManager):
        config.set("ui", "theme", "light")
        assert config.get("ui", "theme") == "light"

    def test_set_persists_after_save_and_reload(self, tmp_dir: Path):
        config_path = tmp_dir / "config.toml"
        config1 = ConfigManager(config_path)
        config1.load()
        config1.set("ui", "theme", "light")
        config1.save()

        config2 = ConfigManager(config_path)
        config2.load()
        assert config2.get("ui", "theme") == "light"

    def test_get_section(self, config: ConfigManager):
        ui_config = config.get_section("ui")
        assert "theme" in ui_config
        assert "overlay_opacity" in ui_config

    def test_set_section(self, config: ConfigManager):
        config.set_section("ui", {"theme": "light", "overlay_opacity": 0.5})
        assert config.get("ui", "theme") == "light"
        assert config.get("ui", "overlay_opacity") == 0.5

    def test_reset_to_defaults(self, config: ConfigManager):
        config.set("ui", "theme", "light")
        config.reset()
        assert config.get("ui", "theme") == "dark"

    def test_validate_valid_config(self, config: ConfigManager):
        errors = config.validate()
        assert len(errors) == 0

    def test_validate_invalid_theme(self, config: ConfigManager):
        config.set("ui", "theme", "neon")
        errors = config.validate()
        assert any("Invalid theme" in e for e in errors)

    def test_validate_invalid_opacity(self, config: ConfigManager):
        config.set("ui", "overlay_opacity", 2.0)
        errors = config.validate()
        assert any("opacity" in e for e in errors)

    def test_validate_invalid_time(self, config: ConfigManager):
        config.set("work_schedule", "start_time", "25:00")
        errors = config.validate()
        assert any("start_time" in e for e in errors)

    def test_export_config(self, config: ConfigManager):
        exported = config.export_config()
        assert "ui" in exported
        assert "work_schedule" in exported

    def test_import_config(self, tmp_dir: Path):
        config = ConfigManager(tmp_dir / "config.toml")
        config.load()
        config.import_config({"ui": {"theme": "light"}})
        assert config.get("ui", "theme") == "light"

    def test_work_schedule_defaults(self, config: ConfigManager):
        assert config.get("work_schedule", "start_time") == "09:00"
        assert config.get("work_schedule", "end_time") == "18:00"

    def test_keyboard_defaults(self, config: ConfigManager):
        assert config.get("keyboard", "create_task") == "ctrl+n"
        assert config.get("keyboard", "complete_task") == "ctrl+enter"
