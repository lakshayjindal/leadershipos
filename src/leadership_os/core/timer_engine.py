"""Timer Engine — manages work session tracking.

Responsibilities:
- Start, pause, resume, and stop work sessions
- Calculate elapsed time using absolute timestamps (survives sleep/hibernate)
- Track accumulated time across multiple sessions per task
- Emit timer events via EventBus

Design principle: Timer accuracy is paramount. Elapsed time is calculated as
current_time - session_start_time, NOT via a counter or interval. This means
the timer survives sleep, hibernate, and app restarts.

A task may have many work sessions (e.g., if interrupted by breaks).
The total time is the sum of all completed sessions plus the current running one.
"""

from __future__ import annotations

import logging
from datetime import datetime

from leadership_os.core.database import Database
from leadership_os.core.event_bus import (
    EventBus,
    TIMER_STARTED,
    TIMER_PAUSED,
    TIMER_STOPPED,
    TIMER_RESUMED,
    TASK_ACTIVATED,
    TASK_PAUSED,
    TASK_COMPLETED,
)
from leadership_os.core.models import Task, WorkSession
from leadership_os.core.state_manager import StateManager

logger = logging.getLogger(__name__)


class TimerEngine:
    """Manages work session lifecycle and elapsed-time calculations.

    The timer engine is event-driven: it subscribes to task lifecycle events
    so that timers start/pause/stop automatically when tasks transition.
    """

    def __init__(
        self, db: Database, event_bus: EventBus, state_manager: StateManager
    ) -> None:
        self.db = db
        self.event_bus = event_bus
        self.state = state_manager

        # Subscribe to task lifecycle events for automatic timer control
        event_bus.subscribe(TASK_ACTIVATED, self._on_task_activated)
        event_bus.subscribe(TASK_PAUSED, self._on_task_paused)
        event_bus.subscribe(TASK_COMPLETED, self._on_task_completed)

    # ─── Event Handlers ───────────────────────────────────────────────

    def _on_task_activated(
        self, event: str, data: dict
    ) -> None:
        """Start the timer automatically when a task is activated."""
        task_id = data.get("task_id", "")
        if task_id:
            try:
                self.start_timer(task_id)
            except Exception as e:
                logger.error("Failed to start timer on task activation: %s", e)

    def _on_task_paused(self, event: str, data: dict) -> None:
        """Pause the timer automatically when a task is paused."""
        task_id = data.get("task_id", "")
        if task_id:
            try:
                self.pause_timer(task_id)
            except Exception as e:
                logger.error("Failed to pause timer on task pause: %s", e)

    def _on_task_completed(self, event: str, data: dict) -> None:
        """Stop the timer automatically when a task is completed."""
        task_id = data.get("task_id", "")
        if task_id:
            try:
                self.stop_timer(task_id)
            except Exception as e:
                logger.error("Failed to stop timer on task complete: %s", e)

    # ─── Timer Operations ─────────────────────────────────────────────

    def start_timer(self, task_id: str) -> WorkSession:
        """Start a new work session for the given task.

        Creates a fresh work session with the current timestamp.
        Updates state with the timer start time.

        Raises:
            ValueError: If the task doesn't exist or if a session is already running.
        """
        # Verify task exists
        task = self.db.get_task(task_id)
        if task is None:
            raise ValueError(f"Task not found: {task_id}")

        # Ensure no active session already
        active = self.db.get_active_session(task_id)
        if active is not None:
            logger.warning(
                "Timer already running for task %s, stopping first", task_id
            )
            self._end_session(active)

        now = datetime.now().isoformat()
        session = WorkSession(task_id=task_id, start_time=now)
        created = self.db.create_work_session(session)

        self.state.set_timer_start(now)
        self.event_bus.emit(
            TIMER_STARTED,
            {
                "task_id": task_id,
                "session_id": created.id,
                "start_time": now,
            },
        )
        logger.debug("Timer started for task %s at %s", task_id, now)
        return created

    def pause_timer(self, task_id: str) -> WorkSession | None:
        """Pause the running timer for a task by ending its current session.

        Calculates the elapsed duration from the active session's start time
        and updates the session record. Does NOT create a new session (that
        happens on resume).

        Returns:
            The ended session, or None if no active session existed.
        """
        active = self.db.get_active_session(task_id)
        if active is None:
            logger.warning("No active session to pause for task %s", task_id)
            return None

        ended = self._end_session(active)

        self.state.set_timer_start(None)
        self.event_bus.emit(
            TIMER_PAUSED,
            {
                "task_id": task_id,
                "session_id": ended.id,
                "duration_seconds": ended.duration_seconds,
            },
        )
        return ended

    def resume_timer(self, task_id: str) -> WorkSession:
        """Resume the timer for a task by creating a new work session.

        The elapsed time from the previous session is already recorded.
        A fresh session is started to continue accumulating time.

        Raises:
            ValueError: If the task doesn't exist.
        """
        task = self.db.get_task(task_id)
        if task is None:
            raise ValueError(f"Task not found: {task_id}")

        # Safely end any lingering active session
        active = self.db.get_active_session(task_id)
        if active is not None:
            self._end_session(active)

        now = datetime.now().isoformat()
        session = WorkSession(task_id=task_id, start_time=now)
        created = self.db.create_work_session(session)

        self.state.set_timer_start(now)
        self.event_bus.emit(
            TIMER_RESUMED,
            {
                "task_id": task_id,
                "session_id": created.id,
                "start_time": now,
            },
        )
        return created

    def stop_timer(self, task_id: str) -> WorkSession | None:
        """Stop the timer permanently (e.g., on task completion).

        Ends the active session and updates the task's accumulated time
        in the database. The task's actual_seconds field is recalculated
        from ALL completed sessions.

        Returns:
            The ended session, or None if no active session existed.
        """
        active = self.db.get_active_session(task_id)
        if active is None:
            logger.warning("No active session to stop for task %s", task_id)
            return None

        ended = self._end_session(active)

        # Update task's actual_seconds from all completed sessions
        sessions = self.db.get_sessions_by_task(task_id)
        total = sum(s.duration_seconds for s in sessions if s.end_time is not None)
        task = self.db.get_task(task_id)
        if task is not None:
            task.actual_seconds = total
            self.db.update_task(task)

        self.state.set_timer_start(None)
        self.event_bus.emit(
            TIMER_STOPPED,
            {
                "task_id": task_id,
                "session_id": ended.id,
                "duration_seconds": ended.duration_seconds,
                "total_seconds": total,
            },
        )
        return ended

    # ─── Query helpers ────────────────────────────────────────────────

    def get_elapsed(self, task_id: str) -> int:
        """Get the current elapsed seconds for a task.

        Sums all completed sessions PLUS the current running session (if any).
        Uses absolute timestamps for accuracy.
        """
        # Sum all completed sessions
        sessions = self.db.get_sessions_by_task(task_id)
        total = sum(s.duration_seconds for s in sessions if s.end_time is not None)

        # Add ongoing session duration
        active = self.db.get_active_session(task_id)
        if active is not None:
            try:
                start = datetime.fromisoformat(active.start_time)
                now = datetime.now()
                total += max(0, int((now - start).total_seconds()))
            except ValueError:
                pass

        return total

    def get_day_focus_seconds(self, day_id: str) -> int:
        """Get total focus time across all tasks for a day."""
        return self.db.calculate_day_focus_seconds(day_id)

    def get_sessions(self, task_id: str) -> list[WorkSession]:
        """Get all work sessions for a task, ordered by start time."""
        return self.db.get_sessions_by_task(task_id)

    def is_timer_running(self, task_id: str) -> bool:
        """Check if there is an active (un-ended) session for this task."""
        return self.db.get_active_session(task_id) is not None

    # ─── Internal helpers ─────────────────────────────────────────────

    def _end_session(self, session: WorkSession) -> WorkSession:
        """End a work session and return it with calculated duration.

        Uses the database's end_work_session which calculates duration
        from julianday differences for accuracy.
        """
        ended = self.db.end_work_session(session.id)
        if ended is None:
            # Fallback: stop via model if database update didn't return row
            session.stop()
            ended = session
        return ended
