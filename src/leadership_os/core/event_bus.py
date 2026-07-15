"""Event bus for Leadership OS.

Responsibilities:
- Allow modules to communicate without direct dependencies
- Publish/subscribe pattern for application events
- Event logging for debugging

Design principle: Instead of calling each module directly,
the Application Core emits events. Modules subscribe only to events they care about.
"""

from __future__ import annotations

import logging
from collections import defaultdict
from typing import Any, Callable

logger = logging.getLogger(__name__)

# ─── Event Names ──────────────────────────────────────────────────────

# Task events
TASK_CREATED = "task_created"
TASK_ACTIVATED = "task_activated"
TASK_COMPLETED = "task_completed"
TASK_PAUSED = "task_paused"
TASK_ARCHIVED = "task_archived"
TASK_DELETED = "task_deleted"
TASK_CARRIED_FORWARD = "task_carried_forward"

# Timer events
TIMER_STARTED = "timer_started"
TIMER_PAUSED = "timer_paused"
TIMER_STOPPED = "timer_stopped"
TIMER_RESUMED = "timer_resumed"

# Break events
BREAK_STARTED = "break_started"
BREAK_ENDED = "break_ended"

# Day events
DAY_STARTED = "day_started"
DAY_ENDED = "day_ended"

# Journal events
JOURNAL_GENERATED = "journal_generated"

# Config events
CONFIG_CHANGED = "config_changed"

# App state events
APP_STATE_CHANGED = "app_state_changed"


# ─── Event Bus ────────────────────────────────────────────────────────


class EventBus:
    """Simple observer pattern event bus.

    Usage:
        bus = EventBus()

        def on_task_completed(event: str, data: dict) -> None:
            print(f"Task completed: {data}")

        bus.subscribe(TASK_COMPLETED, on_task_completed)
        bus.emit(TASK_COMPLETED, {"task_id": "123", "title": "My Task"})
    """

    def __init__(self) -> None:
        self._subscribers: dict[str, list[Callable[[str, dict[str, Any]], None]]] = defaultdict(list)
        self._history: list[tuple[str, dict[str, Any]]] = []

    def subscribe(
        self, event: str, callback: Callable[[str, dict[str, Any]], None]
    ) -> None:
        """Subscribe to an event type."""
        self._subscribers[event].append(callback)
        logger.debug("Subscribed to %s", event)

    def unsubscribe(
        self, event: str, callback: Callable[[str, dict[str, Any]], None]
    ) -> None:
        """Unsubscribe from an event type."""
        if event in self._subscribers:
            self._subscribers[event] = [
                cb for cb in self._subscribers[event] if cb != callback
            ]

    def emit(self, event: str, data: dict[str, Any] | None = None) -> None:
        """Emit an event to all subscribers."""
        if data is None:
            data = {}

        # Store in history for debugging
        self._history.append((event, data))
        if len(self._history) > 100:
            self._history = self._history[-100:]

        logger.debug("Emitting event: %s with data: %s", event, data)

        # Notify all subscribers
        for callback in self._subscribers.get(event, []):
            try:
                callback(event, data)
            except Exception as e:
                logger.error(
                    "Error in event handler for %s: %s", event, e, exc_info=True
                )

    def clear(self) -> None:
        """Clear all subscribers."""
        self._subscribers.clear()

    def get_history(self, limit: int = 50) -> list[tuple[str, dict[str, Any]]]:
        """Get recent event history for debugging."""
        return self._history[-limit:]

    def subscriber_count(self, event: str) -> int:
        """Get the number of subscribers for an event type."""
        return len(self._subscribers.get(event, []))
