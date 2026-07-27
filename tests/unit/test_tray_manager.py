"""Tests for the system tray manager."""

from __future__ import annotations

import sys
from unittest.mock import MagicMock

from leadership_os.core.event_bus import EventBus

# pystray and PIL need a display; mock them for CI/headless environments
# before importing the module under test.
_mock_pystray = MagicMock()
sys.modules["pystray"] = _mock_pystray

_mock_pil = MagicMock()
_mock_image_class = MagicMock()
_mock_pil.Image = _mock_image_class
_mock_pil.ImageDraw = MagicMock()
sys.modules["PIL"] = _mock_pil
sys.modules["PIL.Image"] = _mock_pil.Image
sys.modules["PIL.ImageDraw"] = _mock_pil.ImageDraw

from leadership_os.tray.tray_manager import TrayManager, _generate_icon  # noqa: E402


class TestTrayIconGeneration:
    def test_generate_icon(self):
        # Since PIL is mocked, _generate_icon returns whatever the mock creates.
        _generate_icon(64, 64)
        assert _mock_image_class.new.called


class TestTrayManagerState:
    def test_initial_state(self):
        bus = EventBus()
        tray = TrayManager(bus)
        assert tray._current_task_title == "No active task"
        assert tray._is_working is False
        assert tray._is_break is False

    def test_task_activated_updates_state(self):
        bus = EventBus()
        tray = TrayManager(bus)
        bus.emit("task_activated", {"title": "Focus Task"})
        assert tray._current_task_title == "Focus Task"
        assert tray._is_working is True
        assert tray._is_break is False

    def test_task_completed_clears_state(self):
        bus = EventBus()
        tray = TrayManager(bus)
        bus.emit("task_activated", {"title": "Focus Task"})
        bus.emit("task_completed", {"task_id": "t1"})
        assert tray._is_working is False
        assert tray._current_task_title == "No active task"

    def test_break_started_and_ended(self):
        bus = EventBus()
        tray = TrayManager(bus)
        bus.emit("break_started", {"break_type": "lunch"})
        assert tray._is_break is True
        assert tray._is_working is False
        assert tray._current_task_title == "On Break"

        bus.emit("break_ended", {"break_type": "lunch"})
        assert tray._is_break is False

    def test_update_progress(self):
        bus = EventBus()
        tray = TrayManager(bus)
        tray.update_progress("25m", 2, 5)
        assert tray._focus_time == "25m"
        assert tray._task_progress == "2/5 tasks"
