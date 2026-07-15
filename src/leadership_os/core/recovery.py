"""Recovery — startup recovery and crash handling.

Responsibilities:
- Detect and handle orphaned work/break sessions
- Check the {@code needs_review} flag for incomplete end-of-day review
- Determine the appropriate startup app state
- Provide structured recovery result for the UI layer

Design principle: Never lose data. Always recover automatically when possible.
Only ask the user for action when manual intervention is required.

Recovery Scenarios:
1. Active timer running → safely close session at last known time
2. Break in progress → resume or discard based on user choice
3. Review started but not completed → resume review
4. App crashed during planning → restore partial plan
5. Multiple days without closing → carry forward tasks
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, date
from typing import Any

from leadership_os.core.database import Database
from leadership_os.core.event_bus import EventBus, DAY_STARTED, APP_STATE_CHANGED
from leadership_os.core.state_manager import StateManager
from leadership_os.core.enums import AppState, TaskStatus, DayStatus

logger = logging.getLogger(__name__)


@dataclass
class RecoveryResult:
    """Structured result of the recovery check for the UI layer.

    Attributes:
        needs_recovery: Whether any recovery action is needed.
        needs_review: Whether the previous day's review was incomplete.
        active_task_found: Whether an active task was found from previous session.
        active_break_found: Whether an active break was found from previous session.
        last_session_date: The date of the last recorded session.
        suggested_state: The suggested app state after recovery.
        orphaned_sessions: Number of work sessions that were recovered/closed.
        message: User-facing message describing the recovery action taken.
    """

    needs_recovery: bool = False
    needs_review: bool = False
    active_task_found: bool = False
    active_break_found: bool = False
    last_session_date: str | None = None
    suggested_state: str = AppState.PLANNING.value
    orphaned_sessions: int = 0
    message: str = ""


class RecoveryManager:
    """Performs startup recovery checks and actions."""

    def __init__(
        self, db: Database, state_manager: StateManager, event_bus: EventBus
    ) -> None:
        self.db = db
        self.state = state_manager
        self.event_bus = event_bus

    # ─── Main recovery entry point ────────────────────────────────────

    def check_recovery_needed(self) -> RecoveryResult:
        """Check the system state and determine if recovery is needed.

        This is called at startup BEFORE any engine is fully initialized.
        It examines the persisted state and database to find anomalies.

        Returns:
            A RecoveryResult describing what recovery (if any) is needed.
        """
        result = RecoveryResult()
        today = date.today().isoformat()

        # Get the last session date from state
        last_session_date = self.state.get_last_session_date()
        result.last_session_date = last_session_date

        # Check if the previous day's review was incomplete
        needs_review = self.state.get_needs_review()
        if needs_review and last_session_date and last_session_date < today:
            result.needs_review = True
            result.needs_recovery = True
            result.message = "Previous day's review was not completed."
            logger.info(
                "Recovery: needs_review=True, last_session=%s",
                last_session_date,
            )

        # Check for orphaned active sessions (from a crash)
        app_state = self.state.get_app_state()
        active_task_id = self.state.get_active_task_id()
        active_break_id = self.state.get_active_break_id()

        if active_task_id and app_state in (AppState.WORKING.value, AppState.IDLE.value):
            result.active_task_found = True
            result.needs_recovery = True

        if active_break_id and app_state == AppState.BREAK.value:
            result.active_break_found = True
            result.needs_recovery = True

        if result.active_task_found or result.active_break_found:
            if not result.message:
                result.message = "Active sessions found from previous session."

        # Determine suggested state
        result.suggested_state = self._determine_startup_state(result)

        return result

    # ─── Perform recovery ─────────────────────────────────────────────

    def perform_recovery(self, recovery_result: RecoveryResult | None = None) -> RecoveryResult:
        """Execute automatic recovery actions.

        Closes orphaned sessions, resets state flags, and prepares the
        system for a clean startup. This is the "automatic" recovery path
        (no user interaction required).

        Returns:
            The final recovery result after actions are taken.
        """
        if recovery_result is None:
            recovery_result = self.check_recovery_needed()

        # Close orphaned work sessions
        orphaned = self._close_orphaned_work_sessions()
        recovery_result.orphaned_sessions = len(orphaned)

        # Close orphaned break sessions
        self._close_orphaned_break_sessions()

        # Clear active state (task, break, timer) for clean startup
        self.state.clear_active_state()

        # Reset the needs_review flag if no longer relevant (handled by review flow)
        # (We do NOT clear needs_review here — the review screen handles that)

        # Update last session date to today (since we're starting afresh)
        today = date.today().isoformat()
        self.state.set_last_session_date(today)
        self.state.save()

        logger.info(
            "Recovery complete: closed %d orphaned sessions, message=%s",
            recovery_result.orphaned_sessions,
            recovery_result.message,
        )
        return recovery_result

    # ─── Suggested startup state ──────────────────────────────────────

    def determine_startup_state(self) -> str:
        """Determine the appropriate app state for startup.

        This is a convenience wrapper around check_recovery_needed
        that returns just the suggested state string.

        Returns:
            One of AppState values: PLANNING, WORKING, or REVIEW.
        """
        result = self.check_recovery_needed()
        return result.suggested_state

    def _determine_startup_state(
        self, result: RecoveryResult
    ) -> str:
        """Determine the appropriate app state based on recovery context."""
        if result.needs_review:
            return AppState.REVIEW.value

        # If there are active tasks from today, go to working
        today = date.today().isoformat()
        today_day = self.db.get_day_by_date(today)
        if today_day is not None:
            tasks = self.db.get_tasks_by_day(today_day.id)
            planned = [
                t
                for t in tasks
                if t.status
                in (
                    TaskStatus.PENDING.value,
                    TaskStatus.ACTIVE.value,
                    TaskStatus.PAUSED.value,
                )
            ]
            if planned:
                return AppState.WORKING.value

        # Default to planning for a fresh day
        return AppState.PLANNING.value

    # ─── Internal recovery actions ────────────────────────────────────

    def _close_orphaned_work_sessions(self) -> list[dict[str, Any]]:
        """Close any work sessions that are still marked as active (no end_time).

        This can happen if the app crashes while a timer is running.

        Returns:
            List of dicts describing each closed session.
        """
        closed: list[dict[str, Any]] = []
        now = datetime.now().isoformat()

        # Find all active sessions across all tasks
        # We need to query the database directly
        day_id = self.state.get_current_day_id()
        if day_id is None:
            return closed

        tasks = self.db.get_tasks_by_day(day_id)
        for task in tasks:
            active = self.db.get_active_session(task.id)
            if active is not None:
                # Close the session using database method
                ended = self.db.end_work_session(active.id)
                if ended is not None:
                    closed.append(
                        {
                            "session_id": ended.id,
                            "task_id": task.id,
                            "task_title": task.title,
                            "duration_seconds": ended.duration_seconds,
                        }
                    )
                    logger.info(
                        "Closed orphaned work session for task '%s': %d seconds",
                        task.title,
                        ended.duration_seconds,
                    )

        return closed

    def _close_orphaned_break_sessions(self) -> int:
        """Close any break sessions that are still active.

        Returns:
            Number of orphaned break sessions closed.
        """
        count = 0
        day_id = self.state.get_current_day_id()
        if day_id is None:
            return count

        active_break = self.db.get_active_break(day_id)
        if active_break is not None:
            ended = self.db.end_break(active_break.id)
            if ended is not None:
                count += 1
                logger.info(
                    "Closed orphaned break session: %s (%d seconds)",
                    ended.id,
                    ended.duration_seconds,
                )

        return count
