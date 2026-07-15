"""Task Engine — manages the lifecycle of tasks.

Responsibilities:
- Create, update, delete tasks
- Validate state transitions (delegates to Task model)
- Enforce one-active-task rule
- Handle carry-forward logic
- Maintain task ordering
- Emit domain events via EventBus

Design principle: The TaskEngine orchestrates business rules on top of
the raw Database CRUD. It is the single source of truth for task lifecycle.
"""

from __future__ import annotations

import logging
from typing import Any

from leadership_os.core.database import Database
from leadership_os.core.event_bus import (
    EventBus,
    TASK_CREATED,
    TASK_ACTIVATED,
    TASK_COMPLETED,
    TASK_PAUSED,
    TASK_ARCHIVED,
    TASK_DELETED,
    TASK_CARRIED_FORWARD,
)
from leadership_os.core.models import Task
from leadership_os.core.enums import TaskStatus
from leadership_os.core.state_manager import StateManager
from leadership_os.utils.validators import validate_task_title, validate_priority

logger = logging.getLogger(__name__)


class TaskEngine:
    """Orchestrates task lifecycle with business rule enforcement."""

    def __init__(
        self, db: Database, event_bus: EventBus, state_manager: StateManager
    ) -> None:
        self.db = db
        self.event_bus = event_bus
        self.state = state_manager

    # ─── Create ───────────────────────────────────────────────────────

    def create_task(
        self,
        day_id: str,
        title: str,
        description: str = "",
        priority: str = "medium",
        deadline: str | None = None,
        estimated_minutes: int | None = None,
        notes: str = "",
    ) -> Task:
        """Create a new task in the given day."""
        title = validate_task_title(title)
        priority = validate_priority(priority)

        # Calculate display_order: append after the highest existing order
        existing = self.db.get_tasks_by_day(day_id)
        max_order = max((t.display_order for t in existing), default=-1)
        display_order = max_order + 10

        task = Task(
            day_id=day_id,
            title=title,
            description=description,
            priority=priority,
            deadline=deadline,
            estimated_minutes=estimated_minutes,
            notes=notes,
            display_order=display_order,
        )
        created = self.db.create_task(task)
        self.event_bus.emit(
            TASK_CREATED,
            {
                "task_id": created.id,
                "day_id": day_id,
                "title": title,
                "priority": priority,
            },
        )
        logger.info("Created task: %s (%s)", title, created.id)
        return created

    # ─── Activate ─────────────────────────────────────────────────────

    def activate_task(self, task_id: str) -> Task:
        """Set a task as the active (current) task.

        Enforces one-active-task: any currently active task is paused first.
        """
        task = self.db.get_task(task_id)
        if task is None:
            raise ValueError(f"Task not found: {task_id}")

        # Deactivate any currently active task
        active = self.db.get_active_task(task.day_id)
        if active is not None and active.id != task_id:
            logger.info(
                "Pausing previously active task: %s", active.title
            )
            self._pause_task_internal(active)

        task.transition_to(TaskStatus.ACTIVE.value)
        self.db.update_task(task)
        self.state.set_active_task_id(task.id)
        self.event_bus.emit(
            TASK_ACTIVATED,
            {
                "task_id": task.id,
                "day_id": task.day_id,
                "title": task.title,
                "priority": task.priority,
            },
        )
        logger.info("Activated task: %s", task.title)
        return task

    # ─── Pause ────────────────────────────────────────────────────────

    def pause_task(self, task_id: str) -> Task:
        """Pause the active task (e.g., when starting a break)."""
        task = self.db.get_task(task_id)
        if task is None:
            raise ValueError(f"Task not found: {task_id}")
        return self._pause_task_internal(task)

    def _pause_task_internal(self, task: Task) -> Task:
        """Internal helper — pauses a task without fetching it again."""
        task.transition_to(TaskStatus.PAUSED.value)
        self.db.update_task(task)
        if self.state.get_active_task_id() == task.id:
            self.state.set_active_task_id(None)
        self.event_bus.emit(
            TASK_PAUSED,
            {
                "task_id": task.id,
                "day_id": task.day_id,
                "title": task.title,
            },
        )
        return task

    # ─── Complete ─────────────────────────────────────────────────────

    def complete_task(self, task_id: str) -> Task:
        """Mark a task as completed and record total work time.

        The TimerEngine (subscribed to TASK_COMPLETED) will stop the timer
        and update actual_seconds in the database. This method re-reads
        the task after the event is emitted to get the updated value.
        """
        task = self.db.get_task(task_id)
        if task is None:
            raise ValueError(f"Task not found: {task_id}")

        task.transition_to(TaskStatus.COMPLETED.value)
        self.db.update_task(task)
        self.state.set_active_task_id(None)

        # Emit completed event BEFORE reading sessions — this triggers
        # TimerEngine.stop_timer which ends the active session and updates
        # actual_seconds in the database.
        self.event_bus.emit(
            TASK_COMPLETED,
            {
                "task_id": task.id,
                "day_id": task.day_id,
                "title": task.title,
            },
        )

        # Re-read from DB to get actual_seconds updated by TimerEngine
        updated = self.db.get_task(task_id)
        if updated is not None:
            task = updated

        logger.info(
            "Completed task: %s (%d seconds)", task.title, task.actual_seconds
        )
        return task

    # ─── Archive ──────────────────────────────────────────────────────

    def archive_task(self, task_id: str) -> Task:
        """Archive a task — removes it from active planning, keeps history."""
        task = self.db.get_task(task_id)
        if task is None:
            raise ValueError(f"Task not found: {task_id}")

        task.transition_to(TaskStatus.ARCHIVED.value)
        self.db.update_task(task)
        if self.state.get_active_task_id() == task_id:
            self.state.set_active_task_id(None)

        self.event_bus.emit(
            TASK_ARCHIVED,
            {
                "task_id": task.id,
                "day_id": task.day_id,
                "title": task.title,
            },
        )
        return task

    # ─── Delete ───────────────────────────────────────────────────────

    def delete_task(self, task_id: str) -> None:
        """Permanently delete a task and all its work sessions."""
        task = self.db.get_task(task_id)
        if task is None:
            raise ValueError(f"Task not found: {task_id}")

        if self.state.get_active_task_id() == task_id:
            self.state.set_active_task_id(None)

        self.db.delete_task(task_id)
        self.event_bus.emit(
            TASK_DELETED,
            {
                "task_id": task_id,
                "day_id": task.day_id,
                "title": task.title,
            },
        )
        logger.info("Deleted task: %s", task.title)

    # ─── Update ───────────────────────────────────────────────────────

    def update_task(
        self,
        task_id: str,
        title: str | None = None,
        description: str | None = None,
        priority: str | None = None,
        deadline: str | None = None,
        estimated_minutes: int | None = None,
        notes: str | None = None,
    ) -> Task:
        """Update individual fields of an existing task."""
        task = self.db.get_task(task_id)
        if task is None:
            raise ValueError(f"Task not found: {task_id}")

        if title is not None:
            task.title = validate_task_title(title)
        if description is not None:
            task.description = description
        if priority is not None:
            task.priority = validate_priority(priority)
        if deadline is not None:
            task.deadline = deadline
        if estimated_minutes is not None:
            task.estimated_minutes = estimated_minutes
        if notes is not None:
            task.notes = notes

        self.db.update_task(task)
        return task

    # ─── Reorder ──────────────────────────────────────────────────────

    def reorder_tasks(self, day_id: str, task_ids: list[str]) -> list[Task]:
        """Reorder tasks by assigning sequential display_order values.

        Args:
            day_id: The day whose tasks to reorder.
            task_ids: List of task IDs in the desired order.

        Returns:
            The updated list of tasks for the day.
        """
        for index, task_id in enumerate(task_ids):
            task = self.db.get_task(task_id)
            if task is not None:
                task.display_order = (index + 1) * 10
                self.db.update_task(task)

        return self.db.get_tasks_by_day(day_id)

    # ─── Query helpers ────────────────────────────────────────────────

    def get_tasks(self, day_id: str) -> list[Task]:
        """Get all tasks for a day, ordered by display_order then priority."""
        return self.db.get_tasks_by_day(day_id)

    def get_active_task(self, day_id: str) -> Task | None:
        """Get the currently active task for a day."""
        return self.db.get_active_task(day_id)

    def get_next_pending(self, day_id: str) -> Task | None:
        """Get the next pending task for a day."""
        return self.db.get_next_pending_task(day_id)

    def get_task(self, task_id: str) -> Task | None:
        """Get a single task by ID."""
        return self.db.get_task(task_id)

    # ─── Carry Forward ────────────────────────────────────────────────

    def carry_forward_tasks(
        self, from_day_id: str, to_day_id: str
    ) -> list[Task]:
        """Carry forward incomplete tasks from one day to another.

        Tasks in pending, paused, or active status are copied to the target
        day. The originals are marked as carried_forward.

        Args:
            from_day_id: Source day (usually yesterday).
            to_day_id: Target day (usually today).

        Returns:
            List of newly created tasks in the target day.
        """
        tasks = self.db.get_tasks_by_day(from_day_id)
        carried: list[Task] = []

        for task in tasks:
            if task.status not in (
                TaskStatus.PENDING.value,
                TaskStatus.PAUSED.value,
                TaskStatus.ACTIVE.value,
                TaskStatus.CARRIED_FORWARD.value,
            ):
                continue

            # Create a fresh copy for the new day
            new_task = Task(
                day_id=to_day_id,
                title=task.title,
                description=task.description,
                priority=task.priority,
                status=TaskStatus.PENDING.value,
                deadline=task.deadline,
                estimated_minutes=task.estimated_minutes,
                notes=task.notes,
            )
            created = self.db.create_task(new_task)
            carried.append(created)

            # Mark the original as carried_forward
            try:
                task.transition_to(TaskStatus.CARRIED_FORWARD.value)
                self.db.update_task(task)
            except ValueError as e:
                logger.warning(
                    "Could not mark task '%s' as carried_forward: %s",
                    task.title, e,
                )

        if carried:
            self.event_bus.emit(
                TASK_CARRIED_FORWARD,
                {
                    "from_day_id": from_day_id,
                    "to_day_id": to_day_id,
                    "task_count": len(carried),
                    "task_ids": [t.id for t in carried],
                },
            )
            logger.info(
                "Carried forward %d tasks from %s to %s",
                len(carried),
                from_day_id,
                to_day_id,
            )

        return carried
