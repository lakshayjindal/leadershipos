"""Tests for Leadership OS TimerEngine."""

import pytest
from pathlib import Path
from datetime import datetime, timedelta

from leadership_os.core.timer_engine import TimerEngine
from leadership_os.core.task_engine import TaskEngine
from leadership_os.core.models import Task, Day, WorkSession
from leadership_os.core.enums import TaskStatus
from leadership_os.core.database import Database
from leadership_os.core.event_bus import EventBus
from leadership_os.core.state_manager import StateManager


@pytest.fixture
def task_engine(db: Database, event_bus: EventBus, state: StateManager) -> TaskEngine:
    return TaskEngine(db, event_bus, state)


@pytest.fixture
def timer_engine(db: Database, event_bus: EventBus, state: StateManager) -> TimerEngine:
    return TimerEngine(db, event_bus, state)


class TestStartTimer:
    def test_start_timer_creates_session(self, timer_engine: TimerEngine, sample_task: Task):
        session = timer_engine.start_timer(sample_task.id)
        assert session.task_id == sample_task.id
        assert session.is_running
        assert session.start_time is not None

    def test_start_timer_sets_state(self, timer_engine: TimerEngine, sample_task: Task, state: StateManager):
        timer_engine.start_timer(sample_task.id)
        assert state.get_timer_start() is not None

    def test_start_timer_twice_ends_first(self, timer_engine: TimerEngine, sample_task: Task):
        s1 = timer_engine.start_timer(sample_task.id)
        s2 = timer_engine.start_timer(sample_task.id)
        # The first session should now be ended
        sessions = timer_engine.get_sessions(sample_task.id)
        assert len(sessions) == 2
        ended = [s for s in sessions if s.end_time is not None]
        assert len(ended) == 1

    def test_start_timer_nonexistent_task_raises(self, timer_engine: TimerEngine):
        with pytest.raises(ValueError, match="not found"):
            timer_engine.start_timer("nonexistent-id")

    def test_start_timer_emits_event(self, timer_engine: TimerEngine, sample_task: Task, event_bus: EventBus):
        history_before = len(event_bus.get_history())
        timer_engine.start_timer(sample_task.id)
        history = event_bus.get_history()
        timer_events = [e for e in history if e[0] == "timer_started"]
        assert len(timer_events) > 0
        assert timer_events[-1][1]["task_id"] == sample_task.id


class TestPauseTimer:
    def test_pause_timer(self, timer_engine: TimerEngine, sample_task: Task):
        session = timer_engine.start_timer(sample_task.id)
        paused = timer_engine.pause_timer(sample_task.id)
        assert paused is not None
        assert not paused.is_running
        assert paused.duration_seconds >= 0

    def test_pause_timer_clears_state(self, timer_engine: TimerEngine, sample_task: Task, state: StateManager):
        timer_engine.start_timer(sample_task.id)
        timer_engine.pause_timer(sample_task.id)
        assert state.get_timer_start() is None

    def test_pause_no_active_session(self, timer_engine: TimerEngine, sample_task: Task):
        result = timer_engine.pause_timer(sample_task.id)
        assert result is None


class TestResumeTimer:
    def test_resume_timer_creates_new_session(self, timer_engine: TimerEngine, sample_task: Task):
        timer_engine.start_timer(sample_task.id)
        timer_engine.pause_timer(sample_task.id)
        resumed = timer_engine.resume_timer(sample_task.id)
        assert resumed.is_running
        assert resumed.task_id == sample_task.id

    def test_resume_timer_maintains_two_sessions(self, timer_engine: TimerEngine, sample_task: Task):
        s1 = timer_engine.start_timer(sample_task.id)
        timer_engine.pause_timer(sample_task.id)
        s2 = timer_engine.resume_timer(sample_task.id)
        sessions = timer_engine.get_sessions(sample_task.id)
        assert len(sessions) == 2

    def test_resume_emits_event(self, timer_engine: TimerEngine, sample_task: Task, event_bus: EventBus):
        timer_engine.start_timer(sample_task.id)
        timer_engine.pause_timer(sample_task.id)
        history_before = len(event_bus.get_history())
        timer_engine.resume_timer(sample_task.id)
        history = event_bus.get_history()
        resume_events = [e for e in history if e[0] == "timer_resumed"]
        assert len(resume_events) > 0


class TestStopTimer:
    def test_stop_timer(self, timer_engine: TimerEngine, sample_task: Task):
        session = timer_engine.start_timer(sample_task.id)
        stopped = timer_engine.stop_timer(sample_task.id)
        assert stopped is not None
        assert not stopped.is_running
        assert stopped.duration_seconds >= 0

    def test_stop_timer_updates_task_actual_seconds(self, timer_engine: TimerEngine, db: Database, sample_task: Task):
        # Create a session with known duration
        start = (datetime.now() - timedelta(seconds=1800)).isoformat()
        session = WorkSession(task_id=sample_task.id, start_time=start)
        db.create_work_session(session)
        timer_engine.stop_timer(sample_task.id)
        task = db.get_task(sample_task.id)
        assert task is not None
        assert task.actual_seconds >= 1800

    def test_stop_no_active_session(self, timer_engine: TimerEngine, sample_task: Task):
        result = timer_engine.stop_timer(sample_task.id)
        assert result is None


class TestElapsed:
    def test_get_elapsed_with_completed_sessions(self, timer_engine: TimerEngine, db: Database, sample_task: Task):
        # Add a completed session with known duration
        start = (datetime.now() - timedelta(seconds=600)).isoformat()
        end = (datetime.now() - timedelta(seconds=300)).isoformat()
        session = WorkSession(task_id=sample_task.id, start_time=start, end_time=end, duration_seconds=300)
        db.create_work_session(session)
        elapsed = timer_engine.get_elapsed(sample_task.id)
        assert elapsed >= 300

    def test_get_elapsed_with_running_session(self, timer_engine: TimerEngine, sample_task: Task):
        timer_engine.start_timer(sample_task.id)
        elapsed = timer_engine.get_elapsed(sample_task.id)
        assert elapsed >= 0
        # Should increase over time
        import time
        time.sleep(0.01)
        elapsed2 = timer_engine.get_elapsed(sample_task.id)
        assert elapsed2 >= elapsed


class TestDayFocusTime:
    def test_get_day_focus_seconds(self, timer_engine: TimerEngine, db: Database, sample_day: Day, sample_task: Task):
        # Add work sessions for the day
        start = (datetime.now() - timedelta(seconds=3600)).isoformat()
        session = WorkSession(task_id=sample_task.id, start_time=start)
        db.create_work_session(session)
        timer_engine.stop_timer(sample_task.id)
        focus = timer_engine.get_day_focus_seconds(sample_day.id)
        assert focus >= 0


class TestAutoTimer:
    def test_timer_starts_on_task_activation(self, timer_engine: TimerEngine, task_engine: TaskEngine, sample_day: Day):
        task = task_engine.create_task(sample_day.id, "Auto Timer")
        task_engine.activate_task(task.id)
        assert timer_engine.is_timer_running(task.id)

    def test_timer_pauses_on_task_pause(self, timer_engine: TimerEngine, task_engine: TaskEngine, sample_day: Day):
        task = task_engine.create_task(sample_day.id, "Auto Pause")
        task_engine.activate_task(task.id)
        task_engine.pause_task(task.id)
        assert not timer_engine.is_timer_running(task.id)

    def test_timer_stops_on_task_complete(self, timer_engine: TimerEngine, task_engine: TaskEngine, sample_day: Day):
        task = task_engine.create_task(sample_day.id, "Auto Stop")
        task_engine.activate_task(task.id)
        task_engine.complete_task(task.id)
        assert not timer_engine.is_timer_running(task.id)
