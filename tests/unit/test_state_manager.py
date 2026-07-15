"""Tests for Leadership OS state manager."""

import pytest
from pathlib import Path

from leadership_os.core.state_manager import StateManager
from leadership_os.core.enums import AppState


class TestStateManager:
    def test_load_creates_default_state(self, tmp_dir: Path):
        state = StateManager(tmp_dir / "state.json")
        state.load()
        assert (tmp_dir / "state.json").exists()

    def test_default_state_values(self, state: StateManager):
        assert state.get_app_state() == AppState.STARTUP.value
        assert state.get_active_task_id() is None
        assert state.get_active_break_id() is None
        assert state.get_timer_start() is None
        assert state.get_needs_review() is False

    def test_set_and_get(self, state: StateManager):
        state.set("custom_key", "custom_value")
        assert state.get("custom_key") == "custom_value"

    def test_get_with_default(self, state: StateManager):
        value = state.get("nonexistent", "default")
        assert value == "default"

    def test_set_app_state(self, state: StateManager):
        state.set_app_state(AppState.PLANNING.value)
        assert state.get_app_state() == AppState.PLANNING.value

    def test_set_active_task_id(self, state: StateManager):
        state.set_active_task_id("task-123")
        assert state.get_active_task_id() == "task-123"

    def test_set_active_break_id(self, state: StateManager):
        state.set_active_break_id("break-456")
        assert state.get_active_break_id() == "break-456"

    def test_timer_start(self, state: StateManager):
        state.set_timer_start("2026-07-14T09:00:00")
        assert state.get_timer_start() == "2026-07-14T09:00:00"

    def test_needs_review(self, state: StateManager):
        state.set_needs_review(True)
        assert state.get_needs_review() is True
        state.set_needs_review(False)
        assert state.get_needs_review() is False

    def test_window_position(self, state: StateManager):
        state.set_window_position(200, 300)
        assert state.get_window_position() == (200, 300)

    def test_window_size(self, state: StateManager):
        state.set_window_size(1400, 900)
        assert state.get_window_size() == (1400, 900)

    def test_overlay_position(self, state: StateManager):
        state.set_overlay_position(1600, 50)
        assert state.get_overlay_position() == (1600, 50)

    def test_last_session_date(self, state: StateManager):
        state.set_last_session_date("2026-07-14")
        assert state.get_last_session_date() == "2026-07-14"

    def test_clear_active_state(self, state: StateManager):
        state.set_active_task_id("task-1")
        state.set_active_break_id("break-1")
        state.set_timer_start("2026-07-14T09:00:00")
        state.clear_active_state()
        assert state.get_active_task_id() is None
        assert state.get_active_break_id() is None
        assert state.get_timer_start() is None

    def test_persists_after_save_and_reload(self, tmp_dir: Path):
        state_path = tmp_dir / "state.json"
        state1 = StateManager(state_path)
        state1.load()
        state1.set_app_state(AppState.WORKING.value)
        state1.set_active_task_id("task-abc")
        state1.save()

        state2 = StateManager(state_path)
        state2.load()
        assert state2.get_app_state() == AppState.WORKING.value
        assert state2.get_active_task_id() == "task-abc"

    def test_corrupted_json_creates_defaults(self, tmp_dir: Path):
        state_path = tmp_dir / "state.json"
        state_path.write_text("not valid json {{{")
        state = StateManager(state_path)
        state.load()
        assert state.get_app_state() == AppState.STARTUP.value

    def test_current_day_id(self, state: StateManager):
        state.set_current_day_id("day-789")
        assert state.get_current_day_id() == "day-789"
