"""TaskCard — displays a single task in the task list (Flet).

Shows title, priority indicator, deadline, estimated time, and status.
"""

from __future__ import annotations

import flet as ft

from leadership_os.ui.theme import PRIORITY_RGBA, PRIORITY_LABELS
from leadership_os.utils.time_utils import format_duration_short


def build_task_card(
    task_id: str,
    title: str,
    priority: str,
    status: str,
    is_active: bool,
    is_completed: bool,
    deadline: str,
    estimated_minutes: int,
    actual_seconds: int,
    on_activate,
    on_complete,
    on_edit,
    on_delete,
) -> ft.Container:
    """Build a single task card.

    Args:
        task_id: Unique task identifier.
        title: Task title text.
        priority: Priority level string.
        status: Task status string.
        is_active: Whether this is the currently active task.
        is_completed: Whether this task is completed.
        deadline: Deadline string or empty.
        estimated_minutes: Estimated duration in minutes.
        actual_seconds: Actual time spent in seconds.
        on_activate: Called when task is clicked to activate.
        on_complete: Called when checkbox is clicked to complete.
        on_edit: Called when edit icon is clicked.
        on_delete: Called when delete icon is clicked.

    Returns:
        A Container representing the task card.
    """
    priority_rgba = PRIORITY_RGBA.get(priority, (0.408, 0.408, 0.627, 1))
    priority_label = PRIORITY_LABELS.get(priority, "MEDIUM")
    accent_color = f"rgba({int(priority_rgba[0]*255)},{int(priority_rgba[1]*255)},{int(priority_rgba[2]*255)},{priority_rgba[3]})"

    # Status icon
    if is_active:
        status_icon = ft.Icons.PLAY_CIRCLE
        status_color = "#4A6FA5"
    elif is_completed:
        status_icon = ft.Icons.CHECK_CIRCLE
        status_color = "#66A66B"
    elif status == "paused":
        status_icon = ft.Icons.PAUSE_CIRCLE
        status_color = "#6868A0"
    else:
        status_icon = ft.Icons.RADIO_BUTTON_UNCHECKED
        status_color = "#9898B8"

    # Time display
    if actual_seconds > 0:
        time_text = format_duration_short(actual_seconds)
    elif estimated_minutes > 0:
        time_text = f"est. {estimated_minutes}m"
    else:
        time_text = ""

    # Title color
    title_color = "#E8E8F0" if not is_completed else "#9898B8"
    title_opacity = 0.6 if is_completed else 1.0

    return ft.Container(
        height=48,
        bgcolor="#15152B",
        border_radius=8,
        border=ft.Border.all(1, "#2D2D4A2E"),
        padding=0,
        content=ft.Row(
            spacing=0,
            controls=[
                # Left accent strip
                ft.Container(
                    width=3,
                    height=36,
                    margin=ft.Margin(0, 6, 0, 6),
                    bgcolor=accent_color,
                    border_radius=1.5,
                ),
                ft.Container(width=8),
                # Status icon (checkbox)
                ft.IconButton(
                    icon=status_icon,
                    icon_size=16,
                    icon_color=status_color,
                    width=28,
                    height=28,
                    on_click=lambda _: on_activate() if not is_active else on_complete(),
                ),
                ft.Container(width=6),
                # Content
                ft.Container(
                    expand=True,
                    padding=ft.Padding(0, 6, 0, 6),
                    content=ft.Column(
                        spacing=2,
                        controls=[
                            # Title
                            ft.Text(
                                title,
                                color=title_color,
                                opacity=title_opacity,
                                size=12,
                                weight=ft.FontWeight.W_700 if is_active else ft.FontWeight.W_400,
                            ),
                            # Meta row
                            ft.Row(
                                spacing=6,
                                controls=[
                                    # Priority badge
                                    ft.Container(
                                        width=58,
                                        height=16,
                                        bgcolor=f"rgba({int(priority_rgba[0]*255)},{int(priority_rgba[1]*255)},{int(priority_rgba[2]*255)},50)",
                                        border_radius=8,
                                        alignment=ft.Alignment(0,0),
                                        content=ft.Text(
                                            priority_label,
                                            color=accent_color,
                                            size=8,
                                            weight=ft.FontWeight.W_700,
                                        ),
                                    ),
                                    # Time
                                    ft.Text(
                                        time_text,
                                        color="#9898B8" if time_text else "transparent",
                                        size=10,
                                        visible=bool(time_text),
                                    ),
                                    # Deadline
                                    ft.Text(
                                        deadline,
                                        color="#C45B5B" if deadline else "transparent",
                                        size=10,
                                        visible=bool(deadline),
                                    ),
                                ],
                            ),
                        ],
                    ),
                ),
                # Action icons
                ft.Row(
                    spacing=0,
                    controls=[
                        ft.IconButton(
                            icon=ft.Icons.EDIT,
                            icon_size=13,
                            icon_color="#4A4A70",
                            width=22,
                            height=22,
                            on_click=lambda _: on_edit(),
                        ),
                        ft.IconButton(
                            icon=ft.Icons.DELETE_OUTLINE,
                            icon_size=13,
                            icon_color="#4A4A70",
                            width=22,
                            height=22,
                            on_click=lambda _: on_delete(),
                        ),
                    ],
                ),
                ft.Container(width=6),
            ],
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        ),
    )
