"""Time utilities for Leadership OS.

Responsibilities:
- Format durations in human-readable format
- Parse time strings
- Calculate elapsed time
- Handle time-of-day operations
"""

from __future__ import annotations

from datetime import datetime, timedelta


def format_duration(total_seconds: int) -> str:
    """Format seconds into HH:MM:SS display.

    Examples:
        0 → "00:00:00"
        65 → "00:01:05"
        3661 → "01:01:01"
    """
    if total_seconds < 0:
        total_seconds = 0
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


def format_duration_compact(total_seconds: int) -> str:
    """Format seconds into compact human-readable format.

    Examples:
        0 → "0s"
        45 → "45s"
        300 → "5m"
        3661 → "1h 1m"
    """
    if total_seconds < 0:
        total_seconds = 0
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60
    if hours > 0:
        return f"{hours}h {minutes}m"
    elif minutes > 0:
        return f"{minutes}m"
    else:
        return f"{seconds}s"


def format_duration_short(total_seconds: int) -> str:
    """Format seconds into short duration (for status bar).

    Examples:
        0 → "0m"
        65 → "1m"
        3600 → "1h"
        5400 → "1h 30m"
    """
    if total_seconds < 0:
        total_seconds = 0
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    if hours > 0 and minutes > 0:
        return f"{hours}h {minutes}m"
    elif hours > 0:
        return f"{hours}h"
    elif total_seconds > 0 and minutes == 0:
        # Round up: show at least 1m for any non-zero work
        return "1m"
    else:
        return f"{minutes}m"


def parse_time_string(time_str: str) -> tuple[int, int]:
    """Parse HH:MM time string into (hour, minute).

    Raises:
        ValueError: If the format is invalid
    """
    parts = time_str.strip().split(":")
    if len(parts) != 2:
        raise ValueError(f"Invalid time format: {time_str!r}. Expected HH:MM")
    hour = int(parts[0])
    minute = int(parts[1])
    if not (0 <= hour <= 23 and 0 <= minute <= 59):
        raise ValueError(f"Invalid time values: {time_str!r}")
    return (hour, minute)


def get_time_of_day() -> str:
    """Get current time as HH:MM string."""
    return datetime.now().strftime("%H:%M")


def get_timestamp() -> str:
    """Get current timestamp as ISO string."""
    return datetime.now().isoformat()


def calculate_elapsed(start_time: str) -> int:
    """Calculate elapsed seconds from an ISO timestamp to now.

    Uses absolute timestamps for accuracy (survives sleep/hibernate).
    """
    try:
        start = datetime.fromisoformat(start_time)
        now = datetime.now()
        elapsed = (now - start).total_seconds()
        return max(0, int(elapsed))
    except ValueError:
        return 0


def is_work_time(start_time_str: str, end_time_str: str) -> bool:
    """Check if current time is within working hours."""
    try:
        now = datetime.now()
        start_hour, start_minute = parse_time_string(start_time_str)
        end_hour, end_minute = parse_time_string(end_time_str)

        current_minutes = now.hour * 60 + now.minute
        start_minutes = start_hour * 60 + start_minute
        end_minutes = end_hour * 60 + end_minute

        return start_minutes <= current_minutes <= end_minutes
    except ValueError:
        return False


def seconds_until_time(target_time_str: str) -> int:
    """Calculate seconds until a target time today.

    Returns negative if the time has already passed.
    """
    try:
        now = datetime.now()
        target_hour, target_minute = parse_time_string(target_time_str)
        target = now.replace(hour=target_hour, minute=target_minute, second=0, microsecond=0)
        diff = (target - now).total_seconds()
        return int(diff)
    except ValueError:
        return 0


def format_time_display(time_str: str | None) -> str:
    """Format a time string for display, returning '--:--' if None."""
    if time_str is None:
        return "--:--"
    try:
        # Parse ISO timestamp and extract time
        dt = datetime.fromisoformat(time_str)
        return dt.strftime("%H:%M")
    except ValueError:
        return time_str
