"""Tests for Leadership OS BreakEngine."""

import pytest
from pathlib import Path

from leadership_os.core.break_engine import BreakEngine
from leadership_os.core.task_engine import TaskEngine
from leadership_os.core.timer_engine import TimerEngine
from leadership_os.core.models import Task, Day, BreakSession
from leadership_os.core.enums import TaskStatus, BreakType, AppState
from leadership_os.core.database import Database
from leadership_os.core.event_bus import EventBus, BREAK_STARTED, BREAK_ENDED
from leadership_os.core.state_manager import StateManager


@pytest.fixture
def task_engine(db: Database, event_bus: EventBus, state: StateManager) -> TaskEngine:
    return TaskEngine(db, event_bus, state)


@pytest.fixture
def timer_engine(db: Database, event_bus: EventBus, state: StateManager) -> TimerEngine:
    return TimerEngine(db, event_bus, state)


@pytest.fixture
def break_engine(
    db: Database, event_bus: EventBus, state: StateManager, task_engine: TaskEngine
) -> BreakEngine:
    return BreakEngine(db, event_bus, state, task_engine)


class TestStartBreak:
    def test_start_break_creates_session(self, break_engine: BreakEngine, sample_day: Day):
        session = break_engine.start_break(sample_day.id, BreakType.LUNCH.value)
        assert session.day_id == sample_day.id
        assert session.break_type == BreakType.LUNCH.value
        assert session.is_running

    def test_start_break_sets_state(self, break_engine: BreakEngine, sample_day: Day, state: StateManager):
        session = break_engine.start_break(sample_day.id, BreakType.TEA.value)
        assert state.get_active_break_id() == session.id

    def test_start_break_pauses_active_task(self, break_engine: BreakEngine, task_engine: TaskEngine, sample_day: Day):
        task = task_engine.create_task(sample_day.id, "Break Pause Test")
        task_engine.activate_task(task.id)
        assert task_engine.get_active_task(sample_day.id) is not None

        break_engine.start_break(sample_day.id, BreakType.LUNCH.value)
        # The task should now be paused
        paused_task = task_engine.get_task(task.id)
        assert paused_task is not None
        assert paused_task.status == TaskStatus.PAUSED.value

    def test_start_break_emits_event(self, break_engine: BreakEngine, sample_day: Day, event_bus: EventBus):
        history_before = len(event_bus.get_history())
        break_engine.start_break(sample_day.id, BreakType.PERSONAL.value)
        history = event_bus.get_history()
        break_events = [e for e in history if e[0] == BREAK_STARTED]
        assert len(break_events) > 0
        assert break_events[-1][1]["break_type"] == BreakType.PERSONAL.value

    def test_start_break_with_default_type(self, break_engine: BreakEngine, sample_day: Day):
        session = break_engine.start_break(sample_day.id)
        assert session.break_type == BreakType.PERSONAL.value

    def test_start_break_invalid_type_falls_back(self, break_engine: BreakEngine, sample_day: Day):
        # Invalid break type should fall back to PERSONAL
        session = break_engine.start_break(sample_day.id, break_type="invalid_type")
        assert session.break_type == BreakType.PERSONAL.value


class TestEndBreak:
    def test_end_break_by_id(self, break_engine: BreakEngine, sample_day: Day):
        session = break_engine.start_break(sample_day.id, BreakType.LUNCH.value)
        ended = break_engine.end_break(break_id=session.id, day_id=sample_day.id)
        assert not ended.is_running
        assert ended.duration_seconds >= 0

    def test_end_break_by_day(self, break_engine: BreakEngine, sample_day: Day):
        break_engine.start_break(sample_day.id, BreakType.TEA.value)
        ended = break_engine.end_break(day_id=sample_day.id)
        assert not ended.is_running

    def test_end_break_clears_state(self, break_engine: BreakEngine, sample_day: Day, state: StateManager):
        break_engine.start_break(sample_day.id)
        break_engine.end_break(day_id=sample_day.id)
        assert state.get_active_break_id() is None

    def test_end_break_emits_event(self, break_engine: BreakEngine, sample_day: Day, event_bus: EventBus):
        break_engine.start_break(sample_day.id)
        history_before = len(event_bus.get_history())
        break_engine.end_break(day_id=sample_day.id)
        history = event_bus.get_history()
        end_events = [e for e in history if e[0] == BREAK_ENDED]
        assert len(end_events) > 0

    def test_end_no_active_break_raises(self, break_engine: BreakEngine):
        with pytest.raises(ValueError, match="No active break"):
            break_engine.end_break(day_id="nonexistent-day")

    def test_end_break_resumes_paused_task(self, break_engine: BreakEngine, task_engine: TaskEngine, sample_day: Day):
        """After ending a break, the previously paused task should be resumed."""
        task = task_engine.create_task(sample_day.id, "Resume After Break")
        task_engine.activate_task(task.id)
        break_engine.start_break(sample_day.id, BreakType.LUNCH.value)

        # Task should be paused during break
        paused = task_engine.get_task(task.id)
        assert paused is not None
        assert paused.status == TaskStatus.PAUSED.value

        # End break — task should resume
        break_engine.end_break(day_id=sample_day.id)
        resumed = task_engine.get_task(task.id)
        assert resumed is not None
        assert resumed.status == TaskStatus.ACTIVE.value

    def test_end_break_no_active_break_by_id_raises(self, break_engine: BreakEngine):
        with pytest.raises(ValueError, match="No active break"):
            break_engine.end_break(break_id="nonexistent")

    def test_end_break_no_id_or_day_raises(self, break_engine: BreakEngine):
        with pytest.raises(ValueError, match="Either break_id or day_id"):
            break_engine.end_break()


class TestQueryHelpers:
    def test_get_active_break(self, break_engine: BreakEngine, sample_day: Day):
        session = break_engine.start_break(sample_day.id)
        active = break_engine.get_active_break(sample_day.id)
        assert active is not None
        assert active.id == session.id

    def test_get_active_break_none(self, break_engine: BreakEngine, sample_day: Day):
        active = break_engine.get_active_break(sample_day.id)
        assert active is None

    def test_get_day_break_seconds(self, break_engine: BreakEngine, sample_day: Day):
        break_engine.start_break(sample_day.id, BreakType.LUNCH.value)
        break_engine.end_break(day_id=sample_day.id)
        seconds = break_engine.get_day_break_seconds(sample_day.id)
        assert seconds >= 0
