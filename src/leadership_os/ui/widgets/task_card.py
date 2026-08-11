"""TaskCard — displays a single task in the task list (Flet).

Apple-style light card: white surface, hairline border, ink text,
priority pill badges, Action Blue active state.
"""

from __future__ import annotations

import flet as ft

from leadership_os.ui.theme import (
    GRAY_2,
    GRAY_3,
    GRAY_5,
    HAIRLINE,
    INK,
    PEARL,
    PRIMARY,
    PRIORITY_LABELS,
    PRIORITY_RGBA,
    Theme,
)
from leadership_os.utils.time_utils import format_duration_short


def build_task_card(
    task_id: str,
    title: str,
    priority: str,
    status: str,
    is_active: bool,
    is_completed: bool,
    is_selected: bool = False,
    deadline: str = "",
    estimated_minutes: int = 0,
    actual_seconds: int = 0,
    on_activate=None,
    on_complete=None,
    on_edit=None,
    on_delete=None,
) -> ft.Container:
    """Build a single task card.

    Args:
        task_id: Unique task identifier.
        title: Task title text.
        priority: Priority level string.
        status: Task status string.
        is_active: Whether this is the currently active task.
        is_completed: Whether this task is completed.
        is_selected: Whether this task is selected via keyboard navigation.
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
    priority_rgba = PRIORITY_RGBA.get(priority, (0.525, 0.525, 0.545, 1))
    priority_label = PRIORITY_LABELS.get(priority, "MEDIUM")
    accent_color = f"rgba({int(priority_rgba[0]*255)},{int(priority_rgba[1]*255)},{int(priority_rgba[2]*255)},{priority_rgba[3]})"

    # Status icon
    if is_active:
        status_icon = ft.Icons.PLAY_CIRCLE
        status_color = PRIMARY
    elif is_completed:
        status_icon = ft.Icons.CHECK_CIRCLE
        status_color = Theme.color("success")
    elif status == "paused":
        status_icon = ft.Icons.PAUSE_CIRCLE
        status_color = GRAY_3
    else:
        status_icon = ft.Icons.RADIO_BUTTON_UNCHECKED
        status_color = GRAY_2

    # Time display
    if actual_seconds > 0:
        time_text = format_duration_short(actual_seconds)
    elif estimated_minutes > 0:
        time_text = f"est. {estimated_minutes}m"
    else:
        time_text = ""

    # Title color
    title_color = INK if not is_completed else GRAY_3
    title_opacity = 0.6 if is_completed else 1.0

    return ft.Container(
        height=48,
        bgcolor=PEARL if is_selected else "#ffffff",
        border_radius=Theme.radius["sm"],
        border=ft.Border.all(
            2 if is_selected else 1,
            PRIMARY if is_selected else HAIRLINE,
        ),
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
                                        alignment=ft.Alignment(0, 0),
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
                                        color=GRAY_3 if time_text else "transparent",
                                        size=10,
                                        visible=bool(time_text),
                                    ),
                                    # Deadline
                                    ft.Text(
                                        deadline,
                                        color=Theme.color("error") if deadline else "transparent",
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
                            icon_color=GRAY_5,
                            width=22,
                            height=22,
                            on_click=lambda _: on_edit(),
                        ),
                        ft.IconButton(
                            icon=ft.Icons.DELETE_OUTLINE,
                            icon_size=13,
                            icon_color=GRAY_5,
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
