"""Carry Forward Dialog — morning planning step for unfinished tasks.

Shows incomplete tasks from previous working days and lets the user decide:
- Continue Today: carry the task forward into today's plan
- Reschedule: mark as carried_forward but don't copy to today
- Archive: remove from active planning, keep in history
- Delete: permanently remove

Design: compact cards with priority badges, one-click actions per task.
"""

from __future__ import annotations

from collections.abc import Callable

import flet as ft

from leadership_os.core.models import Task
from leadership_os.ui.theme import (
    GRAY_2,
    GRAY_3,
    HAIRLINE,
    INK,
    ON_PRIMARY,
    PARCHMENT,
    PEARL,
    PRIMARY,
    Theme,
)


def build_carry_forward_dialog(
    tasks: list[Task],
    task_day_map: dict[str, str] | None = None,
    on_continue: Callable[[str], None] = None,
    on_archive: Callable[[str], None] = None,
    on_delete: Callable[[str], None] = None,
    on_done: Callable[[], None] = None,
) -> ft.Container:
    """Build a carry-forward review panel for unfinished tasks.

    Args:
        tasks: List of incomplete tasks from previous days.
        task_day_map: Optional dict mapping task_id -> day date string for display.
        on_continue: Called with task_id when user chooses "Continue Today".
        on_archive: Called with task_id when user chooses "Archive".
        on_delete: Called with task_id when user chooses "Delete".
        on_done: Called when user finishes reviewing all tasks.

    Returns:
        A Container with the carry-forward UI.
    """
    if task_day_map is None:
        task_day_map = {}
    if not tasks:
        return ft.Container(
            expand=True,
            bgcolor=PARCHMENT,
            padding=ft.Padding(24, 16, 24, 12),
            content=ft.Column(
                spacing=12,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Container(height=40),
                    ft.Icon(ft.Icons.CHECK_CIRCLE_OUTLINE, size=36, color=Theme.color("success")),
                    ft.Text("No unfinished tasks from yesterday", color=GRAY_2, size=15, weight=ft.FontWeight.W_700),
                    ft.Text("You're all caught up! Start fresh today.", color=GRAY_3, size=12),
                    ft.Container(height=16),
                    ft.Button(
                        content=ft.Text("Begin Today", color=ON_PRIMARY),
                        on_click=lambda _: on_done(),
                        bgcolor=PRIMARY,
                        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=Theme.radius["pill"])),
                    ),
                ],
            ),
        )

    # Priority colors
    priority_colors = {
        "critical": Theme.color("error"),
        "high": Theme.color("warning"),
        "medium": PRIMARY,
        "low": GRAY_3,
    }

    task_rows: list[ft.Control] = []

    for task in tasks:
        pri_color = priority_colors.get(task.priority, GRAY_3)
        day_date = task_day_map.get(task.id, "")
        day_label = f" · {day_date}" if day_date else ""

        task_rows.append(
            ft.Container(
                bgcolor=PEARL,
                border_radius=Theme.radius["lg"],
                border=ft.Border.all(1, HAIRLINE),
                padding=ft.Padding(12, 10, 12, 10),
                content=ft.Column(
                    spacing=8,
                    controls=[
                        # Task title row
                        ft.Row(
                            spacing=8,
                            controls=[
                                ft.Container(
                                    width=6,
                                    height=6,
                                    border_radius=3,
                                    bgcolor=pri_color,
                                ),
                                ft.Text(task.title, color=INK, size=14, weight=ft.FontWeight.W_600, expand=True),
                                ft.Text(
                                    task.priority.upper() + day_label,
                                    color=GRAY_3,
                                    size=10,
                                ),
                            ],
                        ),
                        # Action buttons
                        ft.Row(
                            spacing=6,
                            controls=[
                                ft.Button(
                                    content=ft.Text("Continue Today", size=11, color=ON_PRIMARY),
                                    on_click=lambda _, t=task: on_continue(t.id),
                                    height=30,
                                    bgcolor=PRIMARY,
                                    style=ft.ButtonStyle(
                                        shape=ft.RoundedRectangleBorder(radius=Theme.radius["pill"]),
                                        padding=ft.Padding(10, 0, 10, 0),
                                    ),
                                ),
                                ft.TextButton(
                                    content=ft.Text("Archive", size=11),
                                    on_click=lambda _, t=task: on_archive(t.id),
                                    height=30,
                                    style=ft.ButtonStyle(
                                        color=GRAY_2,
                                        shape=ft.RoundedRectangleBorder(radius=Theme.radius["sm"]),
                                        padding=ft.Padding(8, 0, 8, 0),
                                    ),
                                ),
                                ft.TextButton(
                                    content=ft.Text("Delete", size=11),
                                    on_click=lambda _, t=task: on_delete(t.id),
                                    height=30,
                                    style=ft.ButtonStyle(
                                        color=Theme.color("error"),
                                        shape=ft.RoundedRectangleBorder(radius=Theme.radius["sm"]),
                                        padding=ft.Padding(8, 0, 8, 0),
                                    ),
                                ),
                            ],
                        ),
                    ],
                ),
            )
        )

    return ft.Container(
        expand=True,
        bgcolor=PARCHMENT,
        padding=ft.Padding(24, 16, 24, 12),
        content=ft.Column(
            spacing=0,
            controls=[
                # Header
                ft.Row(
                    spacing=0,
                    controls=[
                        ft.Icon(ft.Icons.ARROW_FORWARD, size=20, color=Theme.color("warning")),
                        ft.Container(width=8),
                        ft.Text("Carry Forward", color=INK, size=18, weight=ft.FontWeight.W_700),
                    ],
                ),
                ft.Container(height=4),
                ft.Text(
                    f"You have {len(tasks)} unfinished task{'s' if len(tasks) != 1 else ''} from previous days. "
                    "Decide what to do with each one.",
                    color=GRAY_2,
                    size=12,
                    height=1.4,
                ),
                ft.Container(height=16),
                # Task list
                ft.Container(
                    expand=True,
                    content=ft.Column(
                        spacing=8,
                        controls=task_rows,
                        scroll=ft.ScrollMode.AUTO,
                    ),
                ),
                # Done button
                ft.Container(height=12),
                ft.Row(
                    spacing=0,
                    controls=[
                        ft.Container(expand=True),
                        ft.Button(
                            content=ft.Text("Done — Begin Today", color=ON_PRIMARY),
                            on_click=lambda _: on_done(),
                            height=40,
                            bgcolor=PRIMARY,
                            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=Theme.radius["pill"])),
                        ),
                    ],
                ),
            ],
        ),
    )
