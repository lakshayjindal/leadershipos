"""Data models for Leadership OS.

Every entity in the system is represented as a dataclass with validation.
These models are independent of storage — they represent the logical data model.

Design principle: Store facts rather than interpretations.
Everything else (statistics, reports, trends) is derived from these facts.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, date

from leadership_os.core.enums import (
    TaskStatus,
    Priority,
    DayStatus,
    BreakType,
)


def _uuid() -> str:
    """Generate a new UUID4 string."""
    return str(uuid.uuid4())


def _now_iso() -> str:
    """Return current UTC time as ISO timestamp."""
    return datetime.now().isoformat()


def _today_str() -> str:
    """Return today's date as YYYY-MM-DD."""
    return date.today().isoformat()


# ─── Day ──────────────────────────────────────────────────────────────


@dataclass
class Day:
    """Represents one calendar day — the primary container for all work.

    Every task, session, break, and reflection belongs to exactly one Day.
    """

    id: str = field(default_factory=_uuid)
    date: str = field(default_factory=_today_str)
    start_time: str | None = None
    end_time: str | None = None
    status: str = DayStatus.ACTIVE.value
    created_at: str = field(default_factory=_now_iso)
    updated_at: str = field(default_factory=_now_iso)

    def __post_init__(self) -> None:
        self._validate()

    def _validate(self) -> None:
        if not self.id:
            raise ValueError("Day id cannot be empty")
        if not self.date:
            raise ValueError("Day date cannot be empty")
        # Validate date format
        try:
            datetime.strptime(self.date, "%Y-%m-%d")
        except ValueError:
            raise ValueError(f"Invalid date format: {self.date!r}. Expected YYYY-MM-DD")


# ─── Task ─────────────────────────────────────────────────────────────


@dataclass
class Task:
    """Represents a unit of work — the primary object the user interacts with.

    A task moves through well-defined states throughout its lifetime.
    """

    id: str = field(default_factory=_uuid)
    day_id: str = ""
    title: str = ""
    description: str = ""
    priority: str = Priority.MEDIUM.value
    status: str = TaskStatus.PENDING.value
    deadline: str | None = None
    estimated_minutes: int | None = None
    actual_seconds: int = 0
    created_at: str = field(default_factory=_now_iso)
    activated_at: str | None = None
    completed_at: str | None = None
    display_order: int = 0
    notes: str = ""

    def __post_init__(self) -> None:
        self._validate()

    def _validate(self) -> None:
        if not self.title or not self.title.strip():
            raise ValueError("Task title cannot be empty")
        if len(self.title) > 200:
            raise ValueError(f"Task title too long: {len(self.title)} chars (max 200)")
        if not self.day_id:
            raise ValueError("Task must belong to a day (day_id required)")

    def can_transition_to(self, target_status: str) -> bool:
        """Check if this task can transition to the given status."""
        current = TaskStatus(self.status)
        target = TaskStatus(target_status)
        return current.can_transition_to(target)

    def transition_to(self, target_status: str) -> None:
        """Transition task to a new status. Raises ValueError if invalid."""
        if not self.can_transition_to(target_status):
            raise ValueError(
                f"Invalid transition: {self.status} → {target_status}"
            )
        now = _now_iso()
        if target_status == TaskStatus.ACTIVE.value and self.activated_at is None:
            self.activated_at = now
        elif target_status == TaskStatus.COMPLETED.value:
            self.completed_at = now
        self.status = target_status

    def add_work_time(self, seconds: int) -> None:
        """Add time spent on this task (from work sessions)."""
        if seconds < 0:
            raise ValueError("Cannot add negative work time")
        self.actual_seconds += seconds


# ─── Work Session ─────────────────────────────────────────────────────


@dataclass
class WorkSession:
    """One uninterrupted period of focused work on a task.

    A task may contain many work sessions. The total task duration
    is calculated from the sum of all sessions.
    """

    id: str = field(default_factory=_uuid)
    task_id: str = ""
    start_time: str = field(default_factory=_now_iso)
    end_time: str | None = None
    duration_seconds: int = 0
    created_at: str = field(default_factory=_now_iso)

    def __post_init__(self) -> None:
        if not self.task_id:
            raise ValueError("WorkSession must belong to a task (task_id required)")

    @property
    def is_running(self) -> bool:
        """Whether this session is currently active (no end time set)."""
        return self.end_time is None

    def stop(self) -> int:
        """Stop the session and return duration in seconds."""
        if self.end_time is not None:
            raise ValueError("Session already stopped")
        self.end_time = _now_iso()
        # Calculate duration from timestamps
        try:
            start = datetime.fromisoformat(self.start_time)
            end = datetime.fromisoformat(self.end_time)
            self.duration_seconds = max(0, int((end - start).total_seconds()))
        except ValueError:
            # If timestamps are malformed, use 0
            self.duration_seconds = 0
        return self.duration_seconds


# ─── Break Session ────────────────────────────────────────────────────


@dataclass
class BreakSession:
    """Represents intentional non-working time.

    Breaks are independent of tasks and never contribute to focus time.
    """

    id: str = field(default_factory=_uuid)
    day_id: str = ""
    break_type: str = BreakType.PERSONAL.value
    start_time: str = field(default_factory=_now_iso)
    end_time: str | None = None
    duration_seconds: int = 0
    notes: str = ""

    def __post_init__(self) -> None:
        if not self.day_id:
            raise ValueError("BreakSession must belong to a day (day_id required)")

    @property
    def is_running(self) -> bool:
        """Whether this break is currently active."""
        return self.end_time is None

    def stop(self) -> int:
        """Stop the break and return duration in seconds."""
        if self.end_time is not None:
            raise ValueError("Break already stopped")
        self.end_time = _now_iso()
        try:
            start = datetime.fromisoformat(self.start_time)
            end = datetime.fromisoformat(self.end_time)
            self.duration_seconds = max(0, int((end - start).total_seconds()))
        except ValueError:
            self.duration_seconds = 0
        return self.duration_seconds


# ─── Reflection ───────────────────────────────────────────────────────


@dataclass
class Reflection:
    """Answers provided during the End-of-Day Review.

    There is exactly one Reflection per Day.
    """

    id: str = field(default_factory=_uuid)
    day_id: str = ""
    accomplishments: str = ""
    challenges: str = ""
    tomorrow_first: str = ""
    additional_notes: str = ""
    created_at: str = field(default_factory=_now_iso)

    def __post_init__(self) -> None:
        if not self.day_id:
            raise ValueError("Reflection must belong to a day (day_id required)")

    @property
    def has_content(self) -> bool:
        """Whether any reflection field has meaningful content."""
        return bool(
            self.accomplishments.strip()
            or self.challenges.strip()
            or self.tomorrow_first.strip()
        )


# ─── Daily Summary ────────────────────────────────────────────────────


@dataclass
class DailySummary:
    """Calculated information for a completed day.

    This entity exists to simplify reporting and journal generation.
    All values here are derived from the day's data, not manually entered.
    """

    id: str = field(default_factory=_uuid)
    day_id: str = ""
    total_planned: int = 0
    completed: int = 0
    carried_forward: int = 0
    archived: int = 0
    deleted: int = 0
    total_focus_seconds: int = 0
    total_break_seconds: int = 0
    completion_percentage: float = 0.0
    longest_session_seconds: int = 0
    session_count: int = 0
    journal_rel_path: str = ""  # Relative to vault
    generated_at: str = field(default_factory=_now_iso)

    def __post_init__(self) -> None:
        if not self.day_id:
            raise ValueError("DailySummary must belong to a day (day_id required)")

    @property
    def focus_hours(self) -> int:
        """Focus time in whole hours."""
        return self.total_focus_seconds // 3600

    @property
    def focus_minutes(self) -> int:
        """Remaining focus minutes after hours."""
        return (self.total_focus_seconds % 3600) // 60

    @property
    def break_hours(self) -> int:
        """Break time in whole hours."""
        return self.total_break_seconds // 3600

    @property
    def break_minutes(self) -> int:
        """Remaining break minutes after hours."""
        return (self.total_break_seconds % 3600) // 60

    def recalculate(self, tasks: list[Task], focus_seconds: int, break_seconds: int) -> None:
        """Recalculate summary from raw task and session data."""
        self.total_planned = len(
            [t for t in tasks if t.status != TaskStatus.DELETED.value]
        )
        self.completed = len(
            [t for t in tasks if t.status == TaskStatus.COMPLETED.value]
        )
        self.carried_forward = len(
            [t for t in tasks if t.status == TaskStatus.CARRIED_FORWARD.value]
        )
        self.archived = len(
            [t for t in tasks if t.status == TaskStatus.ARCHIVED.value]
        )
        self.deleted = len(
            [t for t in tasks if t.status == TaskStatus.DELETED.value]
        )
        self.total_focus_seconds = focus_seconds
        self.total_break_seconds = break_seconds
        if self.total_planned > 0:
            self.completion_percentage = round(
                (self.completed / self.total_planned) * 100, 1
            )
        else:
            self.completion_percentage = 0.0
