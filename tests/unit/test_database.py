"""Tests for Leadership OS database operations."""

import pytest
from pathlib import Path

from leadership_os.core.database import Database
from leadership_os.core.models import (
    Day, Task, WorkSession, BreakSession, Reflection, DailySummary,
)
from leadership_os.core.enums import TaskStatus, Priority, DayStatus, BreakType


class TestDatabaseInit:
    def test_initialize_creates_database(self, tmp_dir: Path):
        db = Database(tmp_dir / "test.db")
        db.initialize()
        assert (tmp_dir / "test.db").exists()
        db.close()

    def test_initialize_creates_tables(self, tmp_dir: Path):
        db = Database(tmp_dir / "test.db")
        db.initialize()
        # Verify tables exist by querying them
        with db._cursor() as cursor:
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = {row[0] for row in cursor.fetchall()}
            assert "days" in tables
            assert "tasks" in tables
            assert "work_sessions" in tables
            assert "break_sessions" in tables
            assert "reflections" in tables
            assert "daily_summaries" in tables
            assert "schema_version" in tables
        db.close()

    def test_double_initialize_is_safe(self, tmp_dir: Path):
        db = Database(tmp_dir / "test.db")
        db.initialize()
        db.initialize()  # Should not raise
        db.close()


class TestDayOperations:
    def test_get_or_create_today(self, db: Database):
        day = db.get_or_create_today()
        assert day.date  # YYYY-MM-DD format
        assert day.status == DayStatus.ACTIVE.value
        assert day.id

    def test_get_or_create_today_is_idempotent(self, db: Database):
        day1 = db.get_or_create_today()
        day2 = db.get_or_create_today()
        assert day1.id == day2.id

    def test_get_day_by_date(self, db: Database):
        day = db.get_or_create_today()
        found = db.get_day_by_date(day.date)
        assert found is not None
        assert found.id == day.id

    def test_get_day_by_date_not_found(self, db: Database):
        found = db.get_day_by_date("2000-01-01")
        assert found is None

    def test_get_previous_days(self, db: Database):
        day = db.get_or_create_today()
        previous = db.get_previous_days()
        assert isinstance(previous, list)
        # Today should not be in previous days
        for d in previous:
            assert d.date < day.date

    def test_end_day(self, db: Database):
        day = db.get_or_create_today()
        db.end_day(day)
        assert day.status == DayStatus.COMPLETED.value
        assert day.end_time is not None


class TestTaskOperations:
    def test_create_task(self, db: Database):
        day = db.get_or_create_today()
        task = Task(day_id=day.id, title="Test Task", priority=Priority.HIGH.value)
        created = db.create_task(task)
        assert created.id
        assert created.title == "Test Task"

    def test_get_task(self, db: Database):
        day = db.get_or_create_today()
        task = Task(day_id=day.id, title="Find Me")
        created = db.create_task(task)
        found = db.get_task(created.id)
        assert found is not None
        assert found.title == "Find Me"

    def test_get_tasks_by_day(self, db: Database):
        day = db.get_or_create_today()
        db.create_task(Task(day_id=day.id, title="Task 1"))
        db.create_task(Task(day_id=day.id, title="Task 2"))
        db.create_task(Task(day_id=day.id, title="Task 3"))
        tasks = db.get_tasks_by_day(day.id)
        assert len(tasks) == 3

    def test_update_task(self, db: Database):
        day = db.get_or_create_today()
        task = Task(day_id=day.id, title="Original")
        created = db.create_task(task)
        created.title = "Updated"
        db.update_task(created)
        found = db.get_task(created.id)
        assert found is not None
        assert found.title == "Updated"

    def test_delete_task(self, db: Database):
        day = db.get_or_create_today()
        task = Task(day_id=day.id, title="Delete Me")
        created = db.create_task(task)
        db.delete_task(created.id)
        found = db.get_task(created.id)
        assert found is None

    def test_get_active_task(self, db: Database):
        day = db.get_or_create_today()
        task = Task(day_id=day.id, title="Active Task", status=TaskStatus.ACTIVE.value)
        db.create_task(task)
        active = db.get_active_task(day.id)
        assert active is not None
        assert active.title == "Active Task"

    def test_get_active_task_none(self, db: Database):
        day = db.get_or_create_today()
        active = db.get_active_task(day.id)
        assert active is None

    def test_set_task_status(self, db: Database):
        day = db.get_or_create_today()
        task = Task(day_id=day.id, title="Status Test")
        created = db.create_task(task)
        db.set_task_status(created.id, TaskStatus.ACTIVE.value)
        found = db.get_task(created.id)
        assert found is not None
        assert found.status == TaskStatus.ACTIVE.value


class TestWorkSessionOperations:
    def test_create_work_session(self, db: Database):
        day = db.get_or_create_today()
        task = Task(day_id=day.id, title="Work Task")
        created = db.create_task(task)
        session = WorkSession(task_id=created.id)
        saved = db.create_work_session(session)
        assert saved.id
        assert saved.task_id == created.id

    def test_get_active_session(self, db: Database):
        day = db.get_or_create_today()
        task = Task(day_id=day.id, title="Work Task")
        created = db.create_task(task)
        session = WorkSession(task_id=created.id)
        db.create_work_session(session)
        active = db.get_active_session(created.id)
        assert active is not None
        assert active.is_running

    def test_get_sessions_by_task(self, db: Database):
        day = db.get_or_create_today()
        task = Task(day_id=day.id, title="Multi Session")
        created = db.create_task(task)
        db.create_work_session(WorkSession(task_id=created.id))
        db.create_work_session(WorkSession(task_id=created.id))
        sessions = db.get_sessions_by_task(created.id)
        assert len(sessions) == 2

    def test_end_work_session(self, db: Database):
        day = db.get_or_create_today()
        task = Task(day_id=day.id, title="End Session")
        created = db.create_task(task)
        session = WorkSession(task_id=created.id)
        db.create_work_session(session)
        ended = db.end_work_session(session.id)
        assert ended is not None
        assert not ended.is_running
        assert ended.duration_seconds >= 0


class TestBreakSessionOperations:
    def test_create_break_session(self, db: Database):
        day = db.get_or_create_today()
        break_s = BreakSession(day_id=day.id, break_type=BreakType.LUNCH.value)
        saved = db.create_break_session(break_s)
        assert saved.id
        assert saved.break_type == "lunch"

    def test_get_active_break(self, db: Database):
        day = db.get_or_create_today()
        break_s = BreakSession(day_id=day.id, break_type=BreakType.TEA.value)
        db.create_break_session(break_s)
        active = db.get_active_break(day.id)
        assert active is not None
        assert active.is_running

    def test_end_break(self, db: Database):
        day = db.get_or_create_today()
        break_s = BreakSession(day_id=day.id, break_type=BreakType.PERSONAL.value)
        db.create_break_session(break_s)
        ended = db.end_break(break_s.id)
        assert ended is not None
        assert not ended.is_running


class TestReflectionOperations:
    def test_save_reflection(self, db: Database):
        day = db.get_or_create_today()
        refl = Reflection(day_id=day.id, accomplishments="Did great work")
        saved = db.save_reflection(refl)
        assert saved.id

    def test_get_reflection(self, db: Database):
        day = db.get_or_create_today()
        refl = Reflection(
            day_id=day.id,
            accomplishments="Accomplished X",
            challenges="Challenge Y",
        )
        db.save_reflection(refl)
        found = db.get_reflection(day.id)
        assert found is not None
        assert found.accomplishments == "Accomplished X"
        assert found.challenges == "Challenge Y"

    def test_save_reflection_replaces(self, db: Database):
        day = db.get_or_create_today()
        refl1 = Reflection(day_id=day.id, accomplishments="First")
        db.save_reflection(refl1)
        refl2 = Reflection(day_id=day.id, accomplishments="Second")
        db.save_reflection(refl2)
        found = db.get_reflection(day.id)
        assert found is not None
        assert found.accomplishments == "Second"


class TestSummaryOperations:
    def test_save_summary(self, db: Database):
        day = db.get_or_create_today()
        summary = DailySummary(day_id=day.id, total_planned=5, completed=3)
        saved = db.save_summary(summary)
        assert saved.id

    def test_get_summary(self, db: Database):
        day = db.get_or_create_today()
        summary = DailySummary(day_id=day.id, total_planned=5, completed=3)
        db.save_summary(summary)
        found = db.get_summary(day.id)
        assert found is not None
        assert found.total_planned == 5
        assert found.completed == 3


class TestCalculationHelpers:
    def test_calculate_day_focus_seconds(self, db: Database):
        day = db.get_or_create_today()
        task = Task(day_id=day.id, title="Focus Task")
        created = db.create_task(task)
        session = WorkSession(task_id=created.id)
        session.stop()  # Stop immediately (minimal duration)
        db.create_work_session(session)
        focus = db.calculate_day_focus_seconds(day.id)
        assert focus >= 0

    def test_calculate_day_break_seconds(self, db: Database):
        day = db.get_or_create_today()
        break_s = BreakSession(day_id=day.id)
        break_s.stop()
        db.create_break_session(break_s)
        break_secs = db.calculate_day_break_seconds(day.id)
        assert break_secs >= 0

    def test_get_session_count(self, db: Database):
        day = db.get_or_create_today()
        task = Task(day_id=day.id, title="Counted")
        created = db.create_task(task)
        session = WorkSession(task_id=created.id)
        session.stop()
        db.create_work_session(session)
        count = db.get_session_count(day.id)
        assert count == 1
