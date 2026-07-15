"""Tests for Leadership OS RecoveryManager."""

import pytest
from pathlib import Path
from datetime import datetime, timedelta

from leadership_os.core.recovery import RecoveryManager, RecoveryResult
from leadership_os.core.models import Task, Day, WorkSession, BreakSession
from leadership_os.core.enums import TaskStatus, BreakType, AppState
from leadership_os.core.database import Database
from leadership_os.core.event_bus import EventBus
from leadership_os.core.state_manager import StateManager


@pytest.fixture
def recovery_mgr(db: Database, state: StateManager, event_bus: EventBus) -> RecoveryManager:
    return RecoveryManager(db, state, event_bus)


class TestCheckRecovery:
    def test_fresh_state_no_recovery_needed(self, recovery_mgr: RecoveryManager):
        """A fresh state with no previous session should not need recovery."""
        result = recovery_mgr.check_recovery_needed()
        # Fresh state has defaults, so no recovery needed
        assert isinstance(result, RecoveryResult)
        assert result.suggested_state in (
            AppState.PLANNING.value, AppState.WORKING.value
        )

    def test_needs_review_detected(self, recovery_mgr: RecoveryManager, state: StateManager):
        """If the app was closed without review, needs_review should be detected."""
        state.set_needs_review(True)
        state.set_last_session_date("2026-07-13")
        state.save()

        result = recovery_mgr.check_recovery_needed()
        assert result.needs_review is True
        assert result.needs_recovery is True

    def test_active_task_detected(self, recovery_mgr: RecoveryManager, state: StateManager):
        """If there's an active task in state, it should be detected."""
        state.set_app_state(AppState.WORKING.value)
        state.set_active_task_id("active-task-id")
        state.save()

        result = recovery_mgr.check_recovery_needed()
        assert result.active_task_found is True
        assert result.needs_recovery is True

    def test_active_break_detected(self, recovery_mgr: RecoveryManager, state: StateManager):
        """If there's an active break in state, it should be detected."""
        state.set_app_state(AppState.BREAK.value)
        state.set_active_break_id("active-break-id")
        state.save()

        result = recovery_mgr.check_recovery_needed()
        assert result.active_break_found is True
        assert result.needs_recovery is True


class TestStartupState:
    def test_determine_planning_for_fresh_day(self, recovery_mgr: RecoveryManager):
        """A fresh day with no tasks should go to PLANNING."""
        state = recovery_mgr.determine_startup_state()
        assert state == AppState.PLANNING.value

    def test_determine_working_when_tasks_exist(self, recovery_mgr: RecoveryManager, db: Database):
        """If today already has planned tasks, go to WORKING."""
        day = db.get_or_create_today()
        db.create_task(Task(day_id=day.id, title="Existing Task"))
        state = recovery_mgr.determine_startup_state()
        assert state == AppState.WORKING.value

    def test_determine_review_when_needed(self, recovery_mgr: RecoveryManager, state: StateManager):
        """If needs_review, go to REVIEW state."""
        state.set_needs_review(True)
        state.set_last_session_date("2026-07-13")
        state.save()
        state_result = recovery_mgr.determine_startup_state()
        assert state_result == AppState.REVIEW.value


class TestPerformRecovery:
    def test_perform_recovery_clears_active_state(self, recovery_mgr: RecoveryManager, state: StateManager):
        """Performing recovery should clear active state flags."""
        state.set_active_task_id("some-task")
        state.set_active_break_id("some-break")
        state.set_timer_start("2026-07-14T09:00:00")
        state.save()

        result = recovery_mgr.perform_recovery()
        assert state.get_active_task_id() is None
        assert state.get_active_break_id() is None
        assert state.get_timer_start() is None
        assert isinstance(result, RecoveryResult)

    def test_perform_recovery_closes_orphaned_sessions(self, recovery_mgr: RecoveryManager, db: Database, state: StateManager):
        """Active sessions should be closed during recovery."""
        # Create a day and task with an active session
        day = db.get_or_create_today()
        task = db.create_task(Task(day_id=day.id, title="Orphaned Task", status=TaskStatus.ACTIVE.value))
        session = WorkSession(task_id=task.id)
        db.create_work_session(session)
        state.set_current_day_id(day.id)
        state.set_active_task_id(task.id)
        state.save()

        result = recovery_mgr.perform_recovery()
        # The sessions should have been closed
        assert result.orphaned_sessions >= 1
        # Verify no sessions are still active
        active = db.get_active_session(task.id)
        assert active is None

    def test_perform_recovery_updates_last_session_date(self, recovery_mgr: RecoveryManager, state: StateManager):
        """After recovery, last_session_date should be updated to today."""
        state.set_last_session_date("2026-07-13")
        state.save()

        recovery_mgr.perform_recovery()
        # Should now be today's date
        from datetime import date
        assert state.get_last_session_date() == date.today().isoformat()

    def test_perform_recovery_no_issues(self, recovery_mgr: RecoveryManager):
        """Recovery with no issues should work without errors."""
        # Just run it and make sure it doesn't crash
        result = recovery_mgr.perform_recovery()
        assert result is not None
        assert result.orphaned_sessions == 0
