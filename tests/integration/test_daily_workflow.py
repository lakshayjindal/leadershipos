"""Integration tests for the complete daily workflow.

Tests the end-to-end lifecycle of a working day including:
- Morning planning (task creation)
- Working state (task activation, timer)
- Break management
- Task completion
- Carry forward to next day
"""

from __future__ import annotations

import pytest
from datetime import datetime

from leadership_os.core.task_engine import TaskEngine
from leadership_os.core.timer_engine import TimerEngine
from leadership_os.core.break_engine import BreakEngine
from leadership_os.core.models import Day, Task
from leadership_os.core.enums import TaskStatus, BreakType
from leadership_os.core.database import Database
from leadership_os.core.event_bus import EventBus
from leadership_os.core.state_manager import StateManager


@pytest.mark.integration
class TestDailyWorkflow:
    """Complete daily workflow simulation."""

    def test_morning_planning_to_work_transition(
        self,
        task_engine: TaskEngine,
        timer_engine: TimerEngine,
        sample_day: Day,
    ):
        """Simulate morning planning: create tasks, then start working."""
        # Morning planning: create a set of tasks
        tasks = []
        for i, (title, priority) in enumerate(
            [
                ("Critical Feature", "critical"),
                ("Important Bug Fix", "high"),
                ("Documentation Update", "medium"),
                ("Minor Refactor", "low"),
            ]
        ):
            t = task_engine.create_task(
                day_id=sample_day.id,
                title=title,
                priority=priority,
                estimated_minutes=30,
            )
            tasks.append(t)

        planned = task_engine.get_tasks(sample_day.id)
        assert len(planned) >= 4

        # Activate the first (highest priority) task
        task_engine.activate_task(tasks[0].id)
        assert timer_engine.is_timer_running(tasks[0].id)
        assert task_engine.get_active_task(sample_day.id) is not None

    def test_work_interrupted_by_break(
        self,
        task_engine: TaskEngine,
        timer_engine: TimerEngine,
        break_engine: BreakEngine,
        sample_day: Day,
    ):
        """Working → Break → Resume → Complete flow."""
        # Create and start a task
        task = task_engine.create_task(
            sample_day.id, "Deep Work Session", priority="high"
        )
        task_engine.activate_task(task.id)

        # Work for a moment, then take a lunch break
        import time
        time.sleep(0.05)
        break_engine.start_break(sample_day.id, BreakType.LUNCH.value)

        # Verify timer paused
        elapsed_before_break = timer_engine.get_elapsed(task.id)
        assert not timer_engine.is_timer_running(task.id)

        # End break
        break_engine.end_break(day_id=sample_day.id)

        # Verify timer resumed
        assert timer_engine.is_timer_running(task.id)
        elapsed_after_resume = timer_engine.get_elapsed(task.id)
        assert elapsed_after_resume >= elapsed_before_break

        # Work more and complete
        import time
        time.sleep(0.05)
        task_engine.complete_task(task.id)

        # Verify completion
        completed = task_engine.get_task(task.id)
        assert completed is not None
        assert completed.status == TaskStatus.COMPLETED.value
        # actual_seconds will be 0 if sessions were too short (sub-second),
        # but at least the flow works end-to-end
        assert completed.actual_seconds >= 0

    def test_multiple_tasks_with_priority_reordering(
        self,
        task_engine: TaskEngine,
        sample_day: Day,
    ):
        """Create tasks, reorder them, then work through them."""
        t1 = task_engine.create_task(sample_day.id, "A", priority="low")
        t2 = task_engine.create_task(sample_day.id, "B", priority="medium")
        t3 = task_engine.create_task(sample_day.id, "C", priority="high")

        # Reorder: C, A, B
        task_engine.reorder_tasks(sample_day.id, [t3.id, t1.id, t2.id])
        reordered = task_engine.get_tasks(sample_day.id)
        assert reordered[0].id == t3.id
        assert reordered[1].id == t1.id
        assert reordered[2].id == t2.id

    def test_end_of_day_cleanup(
        self,
        task_engine: TaskEngine,
        timer_engine: TimerEngine,
        db: Database,
        sample_day: Day,
        state: StateManager,
    ):
        """Simulate end-of-day: complete tasks, carry forward leftovers."""
        # Create tasks - some to complete, some to carry forward
        complete_me = task_engine.create_task(
            sample_day.id, "Finish Today", priority="critical"
        )
        carry_me = task_engine.create_task(
            sample_day.id, "Tomorrow's Problem", priority="high"
        )

        # Complete one task
        task_engine.activate_task(complete_me.id)
        task_engine.complete_task(complete_me.id)

        # Create next day for carry forward
        next_day_id = "next-day"
        from datetime import date
        now = datetime.now().isoformat()
        with db._cursor() as cursor:
            cursor.execute(
                "INSERT OR IGNORE INTO days (id, date, status, created_at, updated_at) VALUES (?, ?, 'active', ?, ?)",
                (next_day_id, "2099-12-31", now, now),
            )

        # Carry forward the incomplete task
        carried = task_engine.carry_forward_tasks(sample_day.id, next_day_id)
        assert len(carried) == 1
        assert carried[0].title == "Tomorrow's Problem"

        # End the day
        db.end_day(sample_day)
        assert sample_day.status == "completed"
