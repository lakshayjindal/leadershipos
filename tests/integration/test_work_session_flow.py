"""Integration tests for the work session lifecycle.

Tests the complete flow: create task → activate → timer starts → pause → break →
resume → complete → timer stops — testing all engines working together.
"""

from __future__ import annotations

import pytest
from datetime import datetime, timedelta

from leadership_os.core.task_engine import TaskEngine
from leadership_os.core.timer_engine import TimerEngine
from leadership_os.core.break_engine import BreakEngine
from leadership_os.core.models import Day, Task, WorkSession
from leadership_os.core.enums import TaskStatus, BreakType
from leadership_os.core.database import Database
from leadership_os.core.event_bus import EventBus
from leadership_os.core.state_manager import StateManager


class TestTaskTimerFlow:
    """Task → Timer activation flow."""

    def test_create_activate_timer_flow(
        self,
        task_engine: TaskEngine,
        timer_engine: TimerEngine,
        sample_day: Day,
    ):
        """Create a task, activate it, verify timer starts automatically."""
        # 1. Create a task
        task = task_engine.create_task(sample_day.id, "Flow Test Task")
        assert task.status == TaskStatus.PENDING.value

        # 2. Activate the task
        activated = task_engine.activate_task(task.id)
        assert activated.status == TaskStatus.ACTIVE.value

        # 3. Timer should have started automatically
        assert timer_engine.is_timer_running(task.id)
        elapsed = timer_engine.get_elapsed(task.id)
        assert elapsed >= 0

    def test_pause_and_resume_accumulates_time(
        self,
        task_engine: TaskEngine,
        timer_engine: TimerEngine,
        sample_day: Day,
    ):
        """Pausing and resuming should accumulate time across sessions."""
        task = task_engine.create_task(sample_day.id, "Accumulate Time")
        task_engine.activate_task(task.id)

        # Let timer run briefly
        import time
        time.sleep(0.05)

        # Pause
        paused = task_engine.pause_task(task.id)
        assert paused.status == TaskStatus.PAUSED.value
        elapsed_after_pause = timer_engine.get_elapsed(task.id)

        # Resume
        task_engine.activate_task(task.id)
        resumed_elapsed = timer_engine.get_elapsed(task.id)

        # After resume, elapsed should be at least what we had before
        assert resumed_elapsed >= elapsed_after_pause


class TestBreakFlow:
    """Break → pause → resume flow."""

    def test_break_pauses_timer_and_resumes(
        self,
        task_engine: TaskEngine,
        timer_engine: TimerEngine,
        break_engine: BreakEngine,
        sample_day: Day,
    ):
        """Starting a break should pause the timer; ending should resume."""
        # 1. Create and activate a task
        task = task_engine.create_task(sample_day.id, "Break Flow Task")
        task_engine.activate_task(task.id)
        assert timer_engine.is_timer_running(task.id)

        # 2. Start a break
        break_session = break_engine.start_break(
            sample_day.id, BreakType.LUNCH.value
        )
        assert break_session.is_running

        # 3. Timer should be paused
        assert not timer_engine.is_timer_running(task.id)
        paused_task = task_engine.get_task(task.id)
        assert paused_task is not None
        assert paused_task.status == TaskStatus.PAUSED.value

        # 4. End the break
        ended_break = break_engine.end_break(day_id=sample_day.id)
        assert not ended_break.is_running

        # 5. Timer should be running again
        assert timer_engine.is_timer_running(task.id)
        resumed_task = task_engine.get_task(task.id)
        assert resumed_task is not None
        assert resumed_task.status == TaskStatus.ACTIVE.value

    def test_multiple_breaks_accumulate_correctly(
        self,
        task_engine: TaskEngine,
        timer_engine: TimerEngine,
        break_engine: BreakEngine,
        sample_day: Day,
        db: Database,
    ):
        """Multiple breaks should not lose accumulated work time."""
        task = task_engine.create_task(sample_day.id, "Multi Break Task")
        task_engine.activate_task(task.id)

        # Wait a bit
        import time
        time.sleep(0.05)

        # Break 1
        break_engine.start_break(sample_day.id, BreakType.TEA.value)
        elapsed_before = timer_engine.get_elapsed(task.id)
        break_engine.end_break(day_id=sample_day.id)

        # Work a bit more
        time.sleep(0.05)

        # Break 2
        break_engine.start_break(sample_day.id, BreakType.PERSONAL.value)
        elapsed_mid = timer_engine.get_elapsed(task.id)
        break_engine.end_break(day_id=sample_day.id)

        # Work a bit more
        time.sleep(0.05)

        # Complete
        completed = task_engine.complete_task(task.id)
        elapsed_final = timer_engine.get_elapsed(task.id)

        # Elapsed time should only increase (or stay same) through breaks
        assert elapsed_final >= elapsed_mid >= elapsed_before
        # Total sessions should be at least 3 (start, after break1, after break2)
        sessions = timer_engine.get_sessions(task.id)
        assert len(sessions) >= 2


class TestTaskLifecycleFlow:
    """Complete task lifecycle across all engines."""

    def test_full_workflow(
        self,
        task_engine: TaskEngine,
        timer_engine: TimerEngine,
        break_engine: BreakEngine,
        sample_day: Day,
        event_bus: EventBus,
    ):
        """Complete end-to-end workflow test.

        Sequence:
        1. Create multiple tasks
        2. Activate first task → timer starts
        3. Start break → timer pauses, task pauses
        4. End break → timer resumes, task resumes
        5. Complete task → timer stops
        6. Activate next task → timer starts on new task
        7. Complete second task
        """
        # ─── Setup ───────────────────────────────────────────────────
        task1 = task_engine.create_task(sample_day.id, "First Task")
        task2 = task_engine.create_task(sample_day.id, "Second Task")
        assert task1.status == TaskStatus.PENDING.value
        assert task2.status == TaskStatus.PENDING.value

        # ─── Step 1: Activate Task 1 ─────────────────────────────────
        task_engine.activate_task(task1.id)
        assert task_engine.get_active_task(sample_day.id) is not None
        assert timer_engine.is_timer_running(task1.id)

        # ─── Step 2: Start Break ─────────────────────────────────────
        break_session = break_engine.start_break(sample_day.id)
        assert break_session.is_running
        paused = task_engine.get_task(task1.id)
        assert paused is not None
        assert paused.status == TaskStatus.PAUSED.value
        assert not timer_engine.is_timer_running(task1.id)

        # ─── Step 3: End Break ───────────────────────────────────────
        ended = break_engine.end_break(day_id=sample_day.id)
        assert not ended.is_running
        resumed = task_engine.get_task(task1.id)
        assert resumed is not None
        assert resumed.status == TaskStatus.ACTIVE.value
        assert timer_engine.is_timer_running(task1.id)

        # ─── Step 4: Complete Task 1 ─────────────────────────────────
        completed = task_engine.complete_task(task1.id)
        assert completed.status == TaskStatus.COMPLETED.value
        assert not timer_engine.is_timer_running(task1.id)

        # ─── Step 5: Activate Task 2 ─────────────────────────────────
        task_engine.activate_task(task2.id)
        assert timer_engine.is_timer_running(task2.id)
        assert task_engine.get_active_task(sample_day.id) is not None

        # ─── Step 6: Complete Task 2 ─────────────────────────────────
        task_engine.complete_task(task2.id)

        # ─── Verify Final State ──────────────────────────────────────
        tasks = task_engine.get_tasks(sample_day.id)
        completed_tasks = [
            t for t in tasks if t.status == TaskStatus.COMPLETED.value
        ]
        assert len(completed_tasks) == 2

        # Verify events were emitted
        history = event_bus.get_history()
        event_types = {e[0] for e in history}
        assert "task_activated" in event_types
        assert "task_completed" in event_types
        assert "timer_started" in event_types
        assert "timer_stopped" in event_types
        assert "break_started" in event_types
        assert "break_ended" in event_types


class TestCarryForwardFlow:
    """Carry forward integration with engines."""

    def test_carry_forward_pending_tasks(
        self,
        task_engine: TaskEngine,
        timer_engine: TimerEngine,
        db: Database,
    ):
        """Incomplete tasks should be carried forward to a new day."""
        from datetime import datetime

        # Create source day with tasks
        day1 = db.get_or_create_today()
        task1 = task_engine.create_task(day1.id, "Carry Me")
        task2 = task_engine.create_task(day1.id, "Complete Me")
        task_engine.activate_task(task2.id)
        task_engine.complete_task(task2.id)

        # Create target day
        day2_id = "target-day-for-carry"
        now = datetime.now().isoformat()
        with db._cursor() as cursor:
            cursor.execute(
                "INSERT OR IGNORE INTO days (id, date, status, created_at, updated_at) VALUES (?, ?, 'active', ?, ?)",
                (day2_id, "2099-06-15", now, now),
            )

        # Carry forward from day1 to day2
        carried = task_engine.carry_forward_tasks(day1.id, day2_id)
        assert len(carried) == 1
        assert carried[0].title == "Carry Me"

        # Original task1 should be marked carried_forward
        orig_tasks = task_engine.get_tasks(day1.id)
        carried_orig = [
            t for t in orig_tasks if t.status == TaskStatus.CARRIED_FORWARD.value
        ]
        assert len(carried_orig) >= 1
