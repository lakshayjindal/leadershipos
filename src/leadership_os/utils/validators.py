"""Validation utilities for Leadership OS.

Responsibilities:
- Validate user input before it reaches business logic
- Provide clear error messages
- Prevent invalid data from being persisted
"""

from __future__ import annotations

import re
from typing import Any


class ValidationError(Exception):
    """Raised when input validation fails."""

    def __init__(self, field: str, message: str) -> None:
        self.field = field
        self.message = message
        super().__init__(f"{field}: {message}")


def validate_task_title(title: str) -> str:
    """Validate and clean a task title.

    Raises:
        ValidationError if title is empty or too long.
    """
    cleaned = title.strip()
    if not cleaned:
        raise ValidationError("title", "Task title cannot be empty")
    if len(cleaned) > 200:
        raise ValidationError("title", f"Task title too long: {len(cleaned)} chars (max 200)")
    return cleaned


def validate_priority(priority: str) -> str:
    """Validate a priority value.

    Raises:
        ValidationError if priority is not a valid value.
    """
    valid = {"critical", "high", "medium", "low"}
    if priority.lower() not in valid:
        raise ValidationError(
            "priority",
            f"Invalid priority: {priority!r}. Must be one of: {', '.join(sorted(valid))}"
        )
    return priority.lower()


def validate_task_status(status: str) -> str:
    """Validate a task status value."""
    valid = {"pending", "active", "completed", "paused", "archived", "deleted", "carried_forward"}
    if status.lower() not in valid:
        raise ValidationError(
            "status",
            f"Invalid status: {status!r}. Must be one of: {', '.join(sorted(valid))}"
        )
    return status.lower()


def validate_break_type(break_type: str) -> str:
    """Validate a break type value."""
    valid = {"lunch", "dinner", "tea", "personal", "meeting", "custom"}
    if break_type.lower() not in valid:
        raise ValidationError(
            "break_type",
            f"Invalid break type: {break_type!r}. Must be one of: {', '.join(sorted(valid))}"
        )
    return break_type.lower()


def validate_time_format(time_str: str) -> str:
    """Validate HH:MM time format.

    Raises:
        ValidationError if format is invalid.
    """
    pattern = r"^\d{1,2}:\d{2}$"
    if not re.match(pattern, time_str):
        raise ValidationError(
            "time",
            f"Invalid time format: {time_str!r}. Expected HH:MM (e.g., 09:00, 14:30)"
        )
    parts = time_str.split(":")
    hour, minute = int(parts[0]), int(parts[1])
    if not (0 <= hour <= 23):
        raise ValidationError("time", f"Invalid hour: {hour} (must be 0-23)")
    if not (0 <= minute <= 59):
        raise ValidationError("time", f"Invalid minute: {minute} (must be 0-59)")
    # Normalize to HH:MM
    return f"{hour:02d}:{minute:02d}"


def validate_date_format(date_str: str) -> str:
    """Validate YYYY-MM-DD date format.

    Raises:
        ValidationError if format is invalid.
    """
    pattern = r"^\d{4}-\d{2}-\d{2}$"
    if not re.match(pattern, date_str):
        raise ValidationError(
            "date",
            f"Invalid date format: {date_str!r}. Expected YYYY-MM-DD"
        )
    # Try parsing to validate actual date
    from datetime import datetime
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        raise ValidationError("date", f"Invalid date: {date_str!r}")
    return date_str


def validate_minutes(value: Any) -> int:
    """Validate and convert to minutes (positive integer).

    Raises:
        ValidationError if value is not a valid positive integer.
    """
    try:
        minutes = int(value)
    except (TypeError, ValueError):
        raise ValidationError(
            "duration",
            f"Invalid duration: {value!r}. Must be a positive number of minutes"
        )
    if minutes < 0:
        raise ValidationError("duration", "Duration cannot be negative")
    if minutes > 1440:  # 24 hours
        raise ValidationError("duration", "Duration cannot exceed 24 hours (1440 minutes)")
    return minutes


def validate_port(value: Any) -> int:
    """Validate a port number."""
    try:
        port = int(value)
    except (TypeError, ValueError):
        raise ValidationError("port", f"Invalid port: {value!r}")
    if not (1 <= port <= 65535):
        raise ValidationError("port", f"Port must be between 1 and 65535, got {port}")
    return port


def validate_opacity(value: Any) -> float:
    """Validate opacity value (0.0 to 1.0)."""
    try:
        opacity = float(value)
    except (TypeError, ValueError):
        raise ValidationError("opacity", f"Invalid opacity: {value!r}")
    if not (0.0 <= opacity <= 1.0):
        raise ValidationError("opacity", f"Opacity must be between 0.0 and 1.0, got {opacity}")
    return opacity
