"""Enumerations for Leadership OS.

Defines all valid states, priorities, and types used throughout the application.
Enums make invalid states harder to represent at the type level.
"""

from enum import Enum


class TaskStatus(str, Enum):
    """Lifecycle states a task can be in."""

    PENDING = "pending"
    ACTIVE = "active"
    COMPLETED = "completed"
    PAUSED = "paused"
    ARCHIVED = "archived"
    DELETED = "deleted"
    CARRIED_FORWARD = "carried_forward"

    @classmethod
    def valid_transitions(cls) -> dict["TaskStatus", list["TaskStatus"]]:
        """Return the map of valid state transitions."""
        return {
            cls.PENDING: [cls.ACTIVE, cls.ARCHIVED, cls.DELETED],
            cls.ACTIVE: [cls.PAUSED, cls.COMPLETED, cls.ARCHIVED, cls.DELETED],
            cls.PAUSED: [cls.ACTIVE, cls.COMPLETED, cls.ARCHIVED],
            cls.COMPLETED: [],  # Final — becomes 'closed' at day end
            cls.ARCHIVED: [],  # Permanent removal from active planning
            cls.DELETED: [],  # Permanent removal
            cls.CARRIED_FORWARD: [cls.ACTIVE, cls.PENDING, cls.ARCHIVED, cls.DELETED],
        }

    def can_transition_to(self, target: "TaskStatus") -> bool:
        """Check if a transition from this state to target is valid."""
        return target in self.valid_transitions().get(self, [])


class Priority(str, Enum):
    """Task priority levels — determines execution order."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

    @property
    def weight(self) -> int:
        """Numeric weight for sorting (lower = higher priority)."""
        weights = {
            self.CRITICAL: 0,
            self.HIGH: 1,
            self.MEDIUM: 2,
            self.LOW: 3,
        }
        return weights[self]

    def __lt__(self, other: object) -> bool:
        if not isinstance(other, Priority):
            return NotImplemented
        return self.weight < other.weight

    def __le__(self, other: object) -> bool:
        if not isinstance(other, Priority):
            return NotImplemented
        return self.weight <= other.weight

    def __gt__(self, other: object) -> bool:
        if not isinstance(other, Priority):
            return NotImplemented
        return self.weight > other.weight

    def __ge__(self, other: object) -> bool:
        if not isinstance(other, Priority):
            return NotImplemented
        return self.weight >= other.weight


class AppState(str, Enum):
    """Application workflow states — only one active at any time."""

    STARTUP = "startup"
    PLANNING = "planning"
    WORKING = "working"
    BREAK = "break"
    IDLE = "idle"
    REVIEW = "review"
    SHUTDOWN = "shutdown"

    @classmethod
    def valid_transitions(cls) -> dict["AppState", list["AppState"]]:
        """Return the map of valid state transitions."""
        return {
            cls.STARTUP: [cls.PLANNING, cls.WORKING],
            cls.PLANNING: [cls.WORKING],
            cls.WORKING: [cls.BREAK, cls.IDLE, cls.REVIEW],
            cls.BREAK: [cls.WORKING],
            cls.IDLE: [cls.WORKING, cls.REVIEW],
            cls.REVIEW: [cls.SHUTDOWN],
            cls.SHUTDOWN: [cls.STARTUP],
        }

    def can_transition_to(self, target: "AppState") -> bool:
        """Check if a transition from this state to target is valid."""
        return target in self.valid_transitions().get(self, [])


class BreakType(str, Enum):
    """Supported break types."""

    LUNCH = "lunch"
    DINNER = "dinner"
    TEA = "tea"
    PERSONAL = "personal"
    MEETING = "meeting"
    CUSTOM = "custom"


class DayStatus(str, Enum):
    """Day lifecycle status."""

    ACTIVE = "active"
    COMPLETED = "completed"
    ARCHIVED = "archived"
