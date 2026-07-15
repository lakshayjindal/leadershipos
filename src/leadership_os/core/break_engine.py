"""Break Engine — manages break session lifecycle.

Responsibilities:
- Start a break (pauses active task, creates break session)
- End a break (resumes paused task, ends break session)
- Track break durations
- Emit break events via EventBus

Design principle: Breaks are interruptions to focused work. When a break starts,
the active task is automatically paused. When the break ends, the task resumes.
The user never needs to manually pause and resume.
"""

from __future__ import annotations

import logging
from datetime import datetime

from leadership_os.core.database import Database
from leadership_os.core.event_bus import (
    EventBus,
    BREAK_STARTED,
    BREAK_ENDED,
)
from leadership_os.core.models import BreakSession
from leadership_os.core.state_manager import StateManager
from leadership_os.core.task_engine import TaskEngine
from leadership_os.core.enums import TaskStatus, BreakType

logger = logging.getLogger(__name__)


class BreakEngine:
    """Manages break session lifecycle, coordinating with TaskEngine."""

    def __init__(
        self,
        db: Database,
        event_bus: EventBus,
        state_manager: StateManager,
        task_engine: TaskEngine,
    ) -> None:
        self.db = db
        self.event_bus = event_bus
        self.state = state_manager
        self.task_engine = task_engine

    # ─── Start Break ──────────────────────────────────────────────────

    def start_break(
        self,
        day_id: str,
        break_type: str = BreakType.PERSONAL.value,
        notes: str = "",
    ) -> BreakSession:
        """Start a break session.

        Workflow:
        1. If there is an active task, pause it
        2. Create a new break session
        3. Update state with break ID
        4. Emit BREAK_STARTED event

        Returns:
            The newly created BreakSession.
        """
        # Pause the active task (if any)
        active_task = self.db.get_active_task(day_id)
        if active_task is not None:
            self.task_engine.pause_task(active_task.id)
            logger.info(
                "Paused task '%s' for break", active_task.title
            )

        # Validate break type
        try:
            break_type_enum = BreakType(break_type)
        except ValueError:
            break_type = BreakType.PERSONAL.value

        now = datetime.now().isoformat()
        session = BreakSession(
            day_id=day_id,
            break_type=break_type,
            start_time=now,
            notes=notes,
        )
        created = self.db.create_break_session(session)

        self.state.set_active_break_id(created.id)
        self.event_bus.emit(
            BREAK_STARTED,
            {
                "break_id": created.id,
                "day_id": day_id,
                "break_type": break_type,
                "start_time": now,
                "paused_task_id": active_task.id if active_task else None,
            },
        )
        logger.info(
            "Break started: %s (%s)", created.id, break_type
        )
        return created

    # ─── End Break ────────────────────────────────────────────────────

    def end_break(
        self, break_id: str | None = None, day_id: str | None = None
    ) -> BreakSession:
        """End a break session.

        If break_id is provided, ends that specific break directly.
        Otherwise, uses day_id to find the active break for today.

        Workflow:
        1. End the break session (calculate duration)
        2. Clear active break from state
        3. Find the previously paused task and resume it
        4. Emit BREAK_ENDED event

        Args:
            break_id: ID of the break to end (optional).
            day_id: The day ID to find the active break (fallback).

        Returns:
            The ended BreakSession with calculated duration.

        Raises:
            ValueError: If no active break is found.
        """
        # Find and end the break
        if break_id:
            ended = self.db.end_break(break_id)
            if ended is None:
                raise ValueError(f"No active break session found for id: {break_id}")
        elif day_id:
            session = self.db.get_active_break(day_id)
            if session is None:
                raise ValueError("No active break session found")
            ended = self.db.end_break(session.id)
            if ended is None:
                session.stop()
                ended = session
        else:
            raise ValueError("Either break_id or day_id must be provided")

        self.state.set_active_break_id(None)

        # Resume the previously paused task (if any)
        resumed_task_id = None
        if ended.day_id:
            paused_tasks = self.db.get_tasks_by_day(ended.day_id)
            # Find the first paused task (the one we paused for this break)
            paused = [
                t for t in paused_tasks
                if t.status == TaskStatus.PAUSED.value
            ]
            if paused:
                last_paused = paused[0]
                try:
                    self.task_engine.activate_task(last_paused.id)
                    resumed_task_id = last_paused.id
                    logger.info(
                        "Resumed task '%s' after break",
                        last_paused.title,
                    )
                except ValueError:
                    logger.warning(
                        "Could not resume task %s", last_paused.id
                    )

        self.event_bus.emit(
            BREAK_ENDED,
            {
                "break_id": ended.id,
                "day_id": ended.day_id,
                "break_type": ended.break_type,
                "duration_seconds": ended.duration_seconds,
                "resumed_task_id": resumed_task_id,
            },
        )
        logger.info(
            "Break ended: %s (%d seconds)",
            ended.id,
            ended.duration_seconds,
        )
        return ended

    # ─── Query helpers ────────────────────────────────────────────────

    def get_active_break(self, day_id: str) -> BreakSession | None:
        """Get the currently active break for a day."""
        return self.db.get_active_break(day_id)

    def get_day_break_seconds(self, day_id: str) -> int:
        """Get total break time for a day."""
        return self.db.calculate_day_break_seconds(day_id)
