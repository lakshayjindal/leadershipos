"""Shared test fixtures for Leadership OS."""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from leadership_os.core.database import Database
from leadership_os.core.event_bus import EventBus
from leadership_os.core.state_manager import StateManager
from leadership_os.config.config_manager import ConfigManager
from leadership_os.core.models import Day, Task, WorkSession, BreakSession, Reflection
from leadership_os.core.enums import TaskStatus, Priority, AppState, BreakType


@pytest.fixture
def tmp_dir() -> Path:
    """Provide a temporary directory for test data."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def db(tmp_dir: Path) -> Database:
    """Provide an initialized database in a temp directory."""
    database = Database(tmp_dir / "test.db")
    database.initialize()
    yield database
    database.close()


@pytest.fixture
def config(tmp_dir: Path) -> ConfigManager:
    """Provide a config manager in a temp directory."""
    cfg = ConfigManager(tmp_dir / "config.toml")
    cfg.load()
    return cfg


@pytest.fixture
def state(tmp_dir: Path) -> StateManager:
    """Provide a state manager in a temp directory."""
    sm = StateManager(tmp_dir / "state.json")
    sm.load()
    return sm


@pytest.fixture
def event_bus() -> EventBus:
    """Provide a fresh event bus."""
    return EventBus()


@pytest.fixture
def sample_day(db: Database) -> Day:
    """Provide a sample day created in the database."""
    return db.get_or_create_today()


@pytest.fixture
def sample_task(db: Database, sample_day: Day) -> Task:
    """Provide a sample task created in the database."""
    task = Task(
        day_id=sample_day.id,
        title="Test Task",
        priority=Priority.HIGH.value,
    )
    return db.create_task(task)


# ─── Engine Fixtures ────────────────────────────────────────────────


@pytest.fixture
def task_engine(db: Database, event_bus: EventBus, state: StateManager):
    """Provide a TaskEngine instance."""
    from leadership_os.core.task_engine import TaskEngine
    return TaskEngine(db, event_bus, state)


@pytest.fixture
def timer_engine(db: Database, event_bus: EventBus, state: StateManager):
    """Provide a TimerEngine instance."""
    from leadership_os.core.timer_engine import TimerEngine
    return TimerEngine(db, event_bus, state)


@pytest.fixture
def break_engine(db: Database, event_bus: EventBus, state: StateManager, task_engine):
    """Provide a BreakEngine instance."""
    from leadership_os.core.break_engine import BreakEngine
    return BreakEngine(db, event_bus, state, task_engine)


@pytest.fixture
def recovery_mgr(db: Database, state: StateManager, event_bus: EventBus):
    """Provide a RecoveryManager instance."""
    from leadership_os.core.recovery import RecoveryManager
    return RecoveryManager(db, state, event_bus)


@pytest.fixture
def journal_engine(db: Database, event_bus: EventBus, config: ConfigManager):
    """Provide a JournalEngine instance."""
    from leadership_os.core.journal_engine import JournalEngine
    return JournalEngine(db, event_bus, config)

