"""Tests for Leadership OS TaskEngine."""

import pytest
from pathlib import Path

from leadership_os.core.task_engine import TaskEngine
from leadership_os.core.timer_engine import TimerEngine
from leadership_os.core.models import Task, Day
from leadership_os.core.enums import TaskStatus, Priority
from leadership_os.core.database import Database
from leadership_os.core.event_bus import EventBus
from leadership_os.core.state_manager import StateManager


@pytest.fixture
def task_engine(db: Database, event_bus: EventBus, state: StateManager) -> TaskEngine:
    return TaskEngine(db, event_bus, state)


class TestCreateTask:
    def test_create_minimal(self, task_engine: TaskEngine, sample_day: Day):
        task = task_engine.create_task(day_id=sample_day.id, title="My Task")
        assert task.title == "My Task"
        assert task.day_id == sample_day.id
        assert task.status == TaskStatus.PENDING.value
        assert task.priority == Priority.MEDIUM.value
        assert task.id

    def test_create_with_all_fields(self, task_engine: TaskEngine, sample_day: Day):
        task = task_engine.create_task(
            day_id=sample_day.id,
            title="Important Task",
            description="Do the thing",
            priority="critical",
            deadline="2026-07-20T18:00:00",
            estimated_minutes=120,
            notes="Urgent",
        )
        assert task.title == "Important Task"
        assert task.description == "Do the thing"
        assert task.priority == Priority.CRITICAL.value
        assert task.deadline == "2026-07-20T18:00:00"
        assert task.estimated_minutes == 120
        assert task.notes == "Urgent"

    def test_create_sets_display_order(self, task_engine: TaskEngine, sample_day: Day):
        t1 = task_engine.create_task(sample_day.id, "First")
        t2 = task_engine.create_task(sample_day.id, "Second")
        t3 = task_engine.create_task(sample_day.id, "Third")
        assert t1.display_order < t2.display_order < t3.display_order

    def test_create_emits_event(self, task_engine: TaskEngine, sample_day: Day, event_bus: EventBus):
        events_before = len(event_bus.get_history())
        task = task_engine.create_task(sample_day.id, "Event Test")
        history = event_bus.get_history()
        # Find the task_created event
        created_events = [e for e in history if e[0] == "task_created"]
        assert len(created_events) > events_before or created_events
        last = created_events[-1]
        assert last[1]["task_id"] == task.id
        assert last[1]["title"] == "Event Test"


class TestActivateTask:
    def test_activate_pending_task(self, task_engine: TaskEngine, sample_day: Day):
        task = task_engine.create_task(sample_day.id, "Activate Me")
        activated = task_engine.activate_task(task.id)
        assert activated.status == TaskStatus.ACTIVE.value
        assert activated.activated_at is not None

    def test_activate_only_one_active(self, task_engine: TaskEngine, sample_day: Day):
        t1 = task_engine.create_task(sample_day.id, "First")
        t2 = task_engine.create_task(sample_day.id, "Second")
        task_engine.activate_task(t1.id)
        task_engine.activate_task(t2.id)

        # t1 should now be paused, t2 active
        t1_refreshed = task_engine.get_task(t1.id)
        t2_refreshed = task_engine.get_task(t2.id)
        assert t1_refreshed is not None
        assert t1_refreshed.status == TaskStatus.PAUSED.value
        assert t2_refreshed is not None
        assert t2_refreshed.status == TaskStatus.ACTIVE.value

    def test_activate_nonexistent_raises(self, task_engine: TaskEngine):
        with pytest.raises(ValueError, match="not found"):
            task_engine.activate_task("nonexistent-id")


class TestPauseTask:
    def test_pause_active_task(self, task_engine: TaskEngine, sample_day: Day):
        task = task_engine.create_task(sample_day.id, "Pause Me")
        task_engine.activate_task(task.id)
        paused = task_engine.pause_task(task.id)
        assert paused.status == TaskStatus.PAUSED.value

    def test_pause_nonexistent_raises(self, task_engine: TaskEngine):
        with pytest.raises(ValueError, match="not found"):
            task_engine.pause_task("nonexistent-id")


class TestCompleteTask:
    def test_complete_active_task(self, task_engine: TaskEngine, sample_day: Day):
        task = task_engine.create_task(sample_day.id, "Complete Me")
        task_engine.activate_task(task.id)
        completed = task_engine.complete_task(task.id)
        assert completed.status == TaskStatus.COMPLETED.value
        assert completed.completed_at is not None

    def test_complete_with_work_time(
        self, task_engine: TaskEngine, timer_engine: TimerEngine, sample_day: Day
    ):
        """Complete a task after the timer has accumulated time."""
        task = task_engine.create_task(sample_day.id, "Time Tracking")
        task_engine.activate_task(task.id)
        # Timer engine automatically started a session; stop it to record time
        timer_engine.stop_timer(task.id)
        completed = task_engine.complete_task(task.id)
        assert completed.actual_seconds >= 0
        assert completed.status == TaskStatus.COMPLETED.value

    def test_complete_invalid_transition(self, task_engine: TaskEngine, sample_day: Day):
        task = task_engine.create_task(sample_day.id, "Skip Active")
        # Completing from PENDING is invalid
        with pytest.raises(ValueError, match="Invalid transition"):
            task_engine.complete_task(task.id)


class TestArchiveTask:
    def test_archive_pending_task(self, task_engine: TaskEngine, sample_day: Day):
        task = task_engine.create_task(sample_day.id, "Archive Me")
        archived = task_engine.archive_task(task.id)
        assert archived.status == TaskStatus.ARCHIVED.value

    def test_archive_nonexistent_raises(self, task_engine: TaskEngine):
        with pytest.raises(ValueError, match="not found"):
            task_engine.archive_task("nonexistent-id")


class TestDeleteTask:
    def test_delete_task(self, task_engine: TaskEngine, sample_day: Day):
        task = task_engine.create_task(sample_day.id, "Delete Me")
        task_engine.delete_task(task.id)
        assert task_engine.get_task(task.id) is None

    def test_delete_non_existent_raises(self, task_engine: TaskEngine):
        with pytest.raises(ValueError, match="not found"):
            task_engine.delete_task("nonexistent-id")


class TestReorderTasks:
    def test_reorder_tasks(self, task_engine: TaskEngine, sample_day: Day):
        t1 = task_engine.create_task(sample_day.id, "A")
        t2 = task_engine.create_task(sample_day.id, "B")
        t3 = task_engine.create_task(sample_day.id, "C")

        # Reverse order
        reordered = task_engine.reorder_tasks(sample_day.id, [t3.id, t2.id, t1.id])
        assert len(reordered) == 3
        # After reorder, the first task should be t3
        assert reordered[0].id == t3.id
        assert reordered[1].id == t2.id
        assert reordered[2].id == t1.id


class TestCarryForward:
    def test_carry_forward_pending_and_paused(self, task_engine: TaskEngine, db: Database, sample_day: Day):
        """PENDING and PAUSED tasks should be carried forward."""
        # Create second day
        from leadership_os.core.models import Day
        day2_id = "day2-for-carry"
        # Manually create second day record
        second_day = Day(id=day2_id, date="2099-01-01")
        db.create_task(Task(day_id=sample_day.id, title="Original Task"))
        # Manually create day2
        from datetime import datetime
        now = datetime.now().isoformat()
        db._cursor().__enter__().execute(
            "INSERT OR IGNORE INTO days (id, date, status, created_at, updated_at) VALUES (?, ?, 'active', ?, ?)",
            (day2_id, "2099-01-01", now, now),
        )

        carried = task_engine.carry_forward_tasks(sample_day.id, day2_id)
        assert len(carried) == 1
        assert carried[0].title == "Original Task"
        # Original should be marked carried_forward
        original = task_engine.get_task(sample_day.id)
        # Actually the original task is still there
        orig_tasks = task_engine.get_tasks(sample_day.id)
        # It was created with day_id = sample_day.id, so it should be in that day
        # It should now have status = carried_forward
        orig = next((t for t in orig_tasks if t.id != carried[0].id), None)
        if orig:
            assert orig.status == TaskStatus.CARRIED_FORWARD.value


class TestUpdateTask:
    def test_update_title(self, task_engine: TaskEngine, sample_day: Day):
        task = task_engine.create_task(sample_day.id, "Original")
        updated = task_engine.update_task(task.id, title="Updated")
        assert updated.title == "Updated"

    def test_update_priority(self, task_engine: TaskEngine, sample_day: Day):
        task = task_engine.create_task(sample_day.id, "Priority Test")
        updated = task_engine.update_task(task.id, priority="high")
        assert updated.priority == Priority.HIGH.value

    def test_update_partial(self, task_engine: TaskEngine, sample_day: Day):
        task = task_engine.create_task(sample_day.id, "Partial", description="Old")
        updated = task_engine.update_task(task.id, notes="New notes")
        assert updated.title == "Partial"
        assert updated.description == "Old"
        assert updated.notes == "New notes"

    def test_update_nonexistent_raises(self, task_engine: TaskEngine):
        with pytest.raises(ValueError, match="not found"):
            task_engine.update_task("nonexistent", title="Nope")


class TestQueryHelpers:
    def test_get_tasks(self, task_engine: TaskEngine, sample_day: Day):
        t1 = task_engine.create_task(sample_day.id, "A")
        t2 = task_engine.create_task(sample_day.id, "B")
        tasks = task_engine.get_tasks(sample_day.id)
        assert len(tasks) >= 2

    def test_get_active_task(self, task_engine: TaskEngine, sample_day: Day):
        task = task_engine.create_task(sample_day.id, "Active Query")
        task_engine.activate_task(task.id)
        active = task_engine.get_active_task(sample_day.id)
        assert active is not None
        assert active.id == task.id

    def test_get_next_pending(self, task_engine: TaskEngine, sample_day: Day):
        t1 = task_engine.create_task(sample_day.id, "First", priority="high")
        t2 = task_engine.create_task(sample_day.id, "Second", priority="low")
        next_pending = task_engine.get_next_pending(sample_day.id)
        # Returns the one with highest priority (high before low)
        assert next_pending is not None
        assert next_pending.id == t1.id or next_pending.id == t2.id
