"""Tests for Leadership OS data models."""

import pytest
from datetime import datetime

from leadership_os.core.models import (
    Day,
    Task,
    WorkSession,
    BreakSession,
    Reflection,
    DailySummary,
)
from leadership_os.core.enums import TaskStatus, Priority, BreakType


class TestDay:
    def test_create_day_with_defaults(self):
        day = Day(date="2026-07-14")
        assert day.date == "2026-07-14"
        assert day.status == "active"
        assert day.id  # UUID generated
        assert day.created_at

    def test_day_validation_rejects_empty_date(self):
        with pytest.raises(ValueError, match="date cannot be empty"):
            Day(date="")

    def test_day_validation_rejects_invalid_date_format(self):
        with pytest.raises(ValueError, match="Invalid date format"):
            Day(date="not-a-date")

    def test_day_accepts_valid_date(self):
        day = Day(date="2026-12-31")
        assert day.date == "2026-12-31"


class TestTask:
    def test_create_task_with_valid_data(self):
        task = Task(day_id="day-1", title="My Task")
        assert task.title == "My Task"
        assert task.day_id == "day-1"
        assert task.priority == Priority.MEDIUM.value
        assert task.status == TaskStatus.PENDING.value
        assert task.actual_seconds == 0

    def test_task_validation_rejects_empty_title(self):
        with pytest.raises(ValueError, match="title cannot be empty"):
            Task(day_id="day-1", title="")

    def test_task_validation_rejects_whitespace_only_title(self):
        with pytest.raises(ValueError, match="title cannot be empty"):
            Task(day_id="day-1", title="   ")

    def test_task_validation_rejects_long_title(self):
        with pytest.raises(ValueError, match="too long"):
            Task(day_id="day-1", title="x" * 201)

    def test_task_validation_rejects_empty_day_id(self):
        with pytest.raises(ValueError, match="day_id required"):
            Task(day_id="", title="My Task")

    def test_task_transition_pending_to_active(self):
        task = Task(day_id="day-1", title="Task", status=TaskStatus.PENDING.value)
        task.transition_to(TaskStatus.ACTIVE.value)
        assert task.status == TaskStatus.ACTIVE.value
        assert task.activated_at is not None

    def test_task_transition_active_to_completed(self):
        task = Task(day_id="day-1", title="Task", status=TaskStatus.ACTIVE.value)
        task.transition_to(TaskStatus.COMPLETED.value)
        assert task.status == TaskStatus.COMPLETED.value
        assert task.completed_at is not None

    def test_task_invalid_transition_raises(self):
        task = Task(day_id="day-1", title="Task", status=TaskStatus.PENDING.value)
        with pytest.raises(ValueError, match="Invalid transition"):
            task.transition_to(TaskStatus.COMPLETED.value)

    def test_task_add_work_time(self):
        task = Task(day_id="day-1", title="Task")
        task.add_work_time(300)
        assert task.actual_seconds == 300
        task.add_work_time(600)
        assert task.actual_seconds == 900

    def test_task_add_negative_work_time_raises(self):
        task = Task(day_id="day-1", title="Task")
        with pytest.raises(ValueError, match="negative"):
            task.add_work_time(-10)

    def test_task_can_transition_to(self):
        task = Task(day_id="day-1", title="Task", status=TaskStatus.ACTIVE.value)
        assert task.can_transition_to(TaskStatus.PAUSED.value)
        assert task.can_transition_to(TaskStatus.COMPLETED.value)
        assert not task.can_transition_to(TaskStatus.PENDING.value)


class TestWorkSession:
    def test_create_session(self):
        session = WorkSession(task_id="task-1")
        assert session.task_id == "task-1"
        assert session.is_running
        assert session.end_time is None

    def test_session_empty_task_id_raises(self):
        with pytest.raises(ValueError, match="task_id required"):
            WorkSession(task_id="")

    def test_session_stop(self):
        session = WorkSession(task_id="task-1")
        duration = session.stop()
        assert not session.is_running
        assert session.end_time is not None
        assert duration >= 0

    def test_session_stop_twice_raises(self):
        session = WorkSession(task_id="task-1")
        session.stop()
        with pytest.raises(ValueError, match="already stopped"):
            session.stop()


class TestBreakSession:
    def test_create_break(self):
        break_s = BreakSession(day_id="day-1", break_type=BreakType.LUNCH.value)
        assert break_s.day_id == "day-1"
        assert break_s.break_type == "lunch"
        assert break_s.is_running

    def test_break_empty_day_id_raises(self):
        with pytest.raises(ValueError, match="day_id required"):
            BreakSession(day_id="")

    def test_break_stop(self):
        break_s = BreakSession(day_id="day-1")
        duration = break_s.stop()
        assert not break_s.is_running
        assert break_s.end_time is not None
        assert duration >= 0


class TestReflection:
    def test_create_reflection(self):
        refl = Reflection(day_id="day-1", accomplishments="Did stuff")
        assert refl.day_id == "day-1"
        assert refl.accomplishments == "Did stuff"
        assert refl.has_content

    def test_reflection_empty_day_id_raises(self):
        with pytest.raises(ValueError, match="day_id required"):
            Reflection(day_id="")

    def test_reflection_has_content_false_when_empty(self):
        refl = Reflection(day_id="day-1")
        assert not refl.has_content

    def test_reflection_has_content_true_with_challenges(self):
        refl = Reflection(day_id="day-1", challenges="Was hard")
        assert refl.has_content


class TestDailySummary:
    def test_create_summary(self):
        summary = DailySummary(day_id="day-1")
        assert summary.day_id == "day-1"
        assert summary.total_planned == 0
        assert summary.completion_percentage == 0.0

    def test_summary_empty_day_id_raises(self):
        with pytest.raises(ValueError, match="day_id required"):
            DailySummary(day_id="")

    def test_summary_recalculate(self):
        tasks = [
            Task(day_id="day-1", title="T1", status=TaskStatus.COMPLETED.value),
            Task(day_id="day-1", title="T2", status=TaskStatus.PENDING.value),
            Task(day_id="day-1", title="T3", status=TaskStatus.CARRIED_FORWARD.value),
        ]
        summary = DailySummary(day_id="day-1")
        summary.recalculate(tasks, focus_seconds=3600, break_seconds=900)
        assert summary.total_planned == 3
        assert summary.completed == 1
        assert summary.carried_forward == 1
        assert summary.total_focus_seconds == 3600
        assert summary.total_break_seconds == 900
        assert summary.completion_percentage == 33.3

    def test_summary_properties(self):
        summary = DailySummary(day_id="day-1", total_focus_seconds=5400, total_break_seconds=3600)
        assert summary.focus_hours == 1
        assert summary.focus_minutes == 30
        assert summary.break_hours == 1
        assert summary.break_minutes == 0
