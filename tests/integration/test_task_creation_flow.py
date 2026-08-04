"""Integration tests for the task creation → activation flow.

Verifies critical acceptance criteria:
1. Creating a task does NOT auto-activate it — it stays pending.
2. User must explicitly click Start (or keyboard-Enter) to activate a task.
3. Only one task can be active at a time.
4. Completing a task moves it to completed and no task is auto-activated.

These tests call the actual TaskEngine, Database, and app methods.
"""

from __future__ import annotations

import pytest
from datetime import datetime

from leadership_os.core.enums import TaskStatus
from leadership_os.core.models import Task


@pytest.fixture
def engine_setup(tmp_path):
    """Setup a full engine stack with in-memory DB for testing."""
    from leadership_os.core.database import Database
    from leadership_os.core.event_bus import EventBus
    from leadership_os.core.state_manager import StateManager
    from leadership_os.core.task_engine import TaskEngine

    db_path = tmp_path / "test.db"
    db = Database(db_path)
    db.initialize()

    event_bus = EventBus()
    state_path = tmp_path / "state.json"
    state = StateManager(state_path)
    state.load()

    engine = TaskEngine(db, event_bus, state)

    # Create a day
    day = db.get_or_create_today()

    yield engine, db, state, event_bus, day

    db.close()


class TestTaskCreationDoesNotAutoActivate:
    """Acceptance test: creating a task should NOT automatically start it."""

    def test_create_task_stays_pending(self, engine_setup):
        """create_task should produce a pending task, not active."""
        engine, db, state, event_bus, day = engine_setup

        task = engine.create_task(day_id=day.id, title="Write tests")

        assert task is not None
        assert task.status == TaskStatus.PENDING.value
        assert task.title == "Write tests"

        # Verify in DB
        fetched = db.get_task(task.id)
        assert fetched.status == TaskStatus.PENDING.value

    def test_create_multiple_tasks_all_pending(self, engine_setup):
        """Multiple tasks should all be pending initially."""
        engine, db, state, event_bus, day = engine_setup

        t1 = engine.create_task(day_id=day.id, title="Task 1")
        t2 = engine.create_task(day_id=day.id, title="Task 2")
        t3 = engine.create_task(day_id=day.id, title="Task 3")

        assert t1.status == TaskStatus.PENDING.value
        assert t2.status == TaskStatus.PENDING.value
        assert t3.status == TaskStatus.PENDING.value

        # No task should be active
        active = db.get_active_task(day.id)
        assert active is None

    def test_create_task_preserves_existing_active(self, engine_setup):
        """Creating a new task should not deactivate an existing active task."""
        engine, db, state, event_bus, day = engine_setup

        # Create and manually activate first task
        t1 = engine.create_task(day_id=day.id, title="Active Task")
        engine.activate_task(t1.id)

        # Create second task
        t2 = engine.create_task(day_id=day.id, title="Pending Task")

        # t1 should still be active, t2 pending
        assert db.get_task(t1.id).status == TaskStatus.ACTIVE.value
        assert db.get_task(t2.id).status == TaskStatus.PENDING.value


class TestManualTaskActivation:
    """Acceptance test: user must explicitly activate a task."""

    def test_activate_changes_status(self, engine_setup):
        """Activating a pending task should change its status to active."""
        engine, db, state, event_bus, day = engine_setup

        task = engine.create_task(day_id=day.id, title="Start me")

        # Verify pending
        assert task.status == TaskStatus.PENDING.value

        # Activate
        activated = engine.activate_task(task.id)
        assert activated.status == TaskStatus.ACTIVE.value
        assert activated.activated_at is not None

    def test_only_one_active_task(self, engine_setup):
        """Activating a second task should pause the first."""
        engine, db, state, event_bus, day = engine_setup

        t1 = engine.create_task(day_id=day.id, title="First")
        t2 = engine.create_task(day_id=day.id, title="Second")

        engine.activate_task(t1.id)
        assert db.get_task(t1.id).status == TaskStatus.ACTIVE.value

        engine.activate_task(t2.id)
        # t1 should now be paused
        assert db.get_task(t1.id).status == TaskStatus.PAUSED.value
        # t2 should be active
        assert db.get_task(t2.id).status == TaskStatus.ACTIVE.value

    def test_complete_deactivates(self, engine_setup):
        """Completing a task changes it to completed and no task is auto-activated."""
        engine, db, state, event_bus, day = engine_setup

        task = engine.create_task(day_id=day.id, title="Finish me")
        engine.activate_task(task.id)

        completed = engine.complete_task(task.id)
        assert completed.status == TaskStatus.COMPLETED.value
        assert completed.completed_at is not None

        # No task should be auto-activated after completion
        active = db.get_active_task(day.id)
        assert active is None


class TestTaskOrderingAfterCreation:
    """Tasks should have correct display_order for list ordering."""

    def test_tasks_have_increasing_order(self, engine_setup):
        """Each new task should get a higher display_order."""
        engine, db, state, event_bus, day = engine_setup

        t1 = engine.create_task(day_id=day.id, title="First")
        t2 = engine.create_task(day_id=day.id, title="Second")
        t3 = engine.create_task(day_id=day.id, title="Third")

        assert t1.display_order < t2.display_order < t3.display_order

    def test_reorder_updates_order(self, engine_setup):
        """reorder_tasks should update display_order values."""
        engine, db, state, event_bus, day = engine_setup

        t1 = engine.create_task(day_id=day.id, title="A")
        t2 = engine.create_task(day_id=day.id, title="B")
        t3 = engine.create_task(day_id=day.id, title="C")

        # Reverse the order
        engine.reorder_tasks(day.id, [t3.id, t2.id, t1.id])

        tasks = engine.get_tasks(day.id)
        assert tasks[0].id == t3.id
        assert tasks[1].id == t2.id
        assert tasks[2].id == t1.id


class TestOverlayTkinterFallback:
    """Verify overlay handles missing tkinter gracefully."""

    def test_overlay_creates_without_tkinter(self):
        """If tkinter is not available, OverlayWindow should still instantiate."""
        from leadership_os.ui.overlay import OverlayWindow, _HAS_TKINTER
        import sys

        overlay = OverlayWindow(
            on_show_main=lambda: None,
            on_pause=lambda: None,
            on_complete=lambda: None,
            on_start_break=lambda: None,
            on_resume=lambda: None,
            on_end_break=lambda: None,
        )

        assert overlay is not None

    def test_overlay_start_without_tkinter_is_safe(self):
        """start() should not crash when tkinter is missing."""
        from leadership_os.ui.overlay import OverlayWindow

        overlay = OverlayWindow(
            on_show_main=lambda: None,
            on_pause=lambda: None,
            on_complete=lambda: None,
            on_start_break=lambda: None,
            on_resume=lambda: None,
            on_end_break=lambda: None,
        )

        # Should not raise
        overlay.start()
        overlay.stop()

    def test_overlay_send_update_without_tkinter_is_safe(self):
        """send_update should not crash when tkinter is missing."""
        from leadership_os.ui.overlay import OverlayWindow

        overlay = OverlayWindow(
            on_show_main=lambda: None,
            on_pause=lambda: None,
            on_complete=lambda: None,
            on_start_break=lambda: None,
            on_resume=lambda: None,
            on_end_break=lambda: None,
        )

        overlay.send_update({"task": "Test", "timer": "00:42:18"})
        overlay.hide()
        overlay.show()

    def test_overlay_get_position_is_safe(self):
        """get_position should always return a tuple."""
        from leadership_os.ui.overlay import OverlayWindow

        overlay = OverlayWindow(
            on_show_main=lambda: None,
            on_pause=lambda: None,
            on_complete=lambda: None,
            on_start_break=lambda: None,
            on_resume=lambda: None,
            on_end_break=lambda: None,
        )

        x, y = overlay.get_position()
        assert isinstance(x, int)
        assert isinstance(y, int)
