"""TaskForm — task creation and editing form (Flet).

Minimal form that initially shows only the title field.
Advanced options (priority, deadline, estimated time, notes) expand on request.
"""

from __future__ import annotations

import flet as ft


def build_task_form(
    title: str,
    is_edit_mode: bool,
    advanced_visible: bool,
    estimated_minutes: int,
    deadline: str,
    notes: str,
    on_title_change,
    on_submit,
    on_cancel,
    on_toggle_advanced,
    on_estimated_change,
    on_deadline_change,
    on_notes_change,
) -> ft.Column:
    """Build the task form.

    Args:
        title: Current title value.
        is_edit_mode: Whether editing existing task.
        advanced_visible: Whether advanced fields are shown.
        estimated_minutes: Current estimated minutes.
        deadline: Current deadline string.
        notes: Current notes string.
        on_title_change: Called when title changes.
        on_submit: Called to submit the form.
        on_cancel: Called to cancel.
        on_toggle_advanced: Toggle advanced fields visibility.
        on_estimated_change: Called when estimated minutes changes.
        on_deadline_change: Called when deadline changes.
        on_notes_change: Called when notes changes.

    Returns:
        A Column containing the form.
    """
    return ft.Column(
        spacing=8,
        controls=[
            # Title input
            ft.TextField(
                value=title,
                hint_text="Task title...",
                on_change=lambda e: on_title_change(e.control.value),
                height=48,
                max_length=200,
                border=ft.InputBorder.OUTLINE,
                border_color="#2D2D4A",
                focused_border_color="#4A6FA5",
                bgcolor="#1A1A2E",
                text_style=ft.TextStyle(color="#E8E8F0", size=13),
                hint_style=ft.TextStyle(color="#747496", size=13),
            ),
            # Advanced toggle
            ft.TextButton(
                content="Advanced options" if not advanced_visible else "Hide options",
                on_click=lambda _: on_toggle_advanced(),
                style=ft.ButtonStyle(
                    color="#9898B8",
                ),
            ),
            # Advanced fields
            ft.Column(
                spacing=8,
                visible=advanced_visible,
                controls=[
                    ft.TextField(
                        value=str(estimated_minutes) if estimated_minutes else "",
                        hint_text="Estimated minutes (optional)",
                        on_change=lambda e: on_estimated_change(int(e.control.value) if e.control.value.isdigit() else 0),
                        height=48,
                        border=ft.InputBorder.OUTLINE,
                        border_color="#2D2D4A",
                        focused_border_color="#4A6FA5",
                        bgcolor="#1A1A2E",
                        keyboard_type=ft.KeyboardType.NUMBER,
                        text_style=ft.TextStyle(color="#E8E8F0", size=13),
                        hint_style=ft.TextStyle(color="#747496", size=13),
                    ),
                    ft.TextField(
                        value=deadline,
                        hint_text="Deadline (optional)",
                        on_change=lambda e: on_deadline_change(e.control.value),
                        height=48,
                        border=ft.InputBorder.OUTLINE,
                        border_color="#2D2D4A",
                        focused_border_color="#4A6FA5",
                        bgcolor="#1A1A2E",
                        text_style=ft.TextStyle(color="#E8E8F0", size=13),
                        hint_style=ft.TextStyle(color="#747496", size=13),
                    ),
                    ft.TextField(
                        value=notes,
                        hint_text="Notes (optional)",
                        on_change=lambda e: on_notes_change(e.control.value),
                        multiline=True,
                        height=80,
                        min_lines=2,
                        max_lines=4,
                        border=ft.InputBorder.OUTLINE,
                        border_color="#2D2D4A",
                        focused_border_color="#4A6FA5",
                        bgcolor="#1A1A2E",
                        text_style=ft.TextStyle(color="#E8E8F0", size=13),
                        hint_style=ft.TextStyle(color="#747496", size=13),
                    ),
                ],
            ),
            # Action buttons
            ft.Row(
                spacing=8,
                controls=[
                    ft.Container(expand=True),
                    ft.TextButton(
                        content="Cancel",
                        on_click=lambda _: on_cancel(),
                    ),
                    ft.ElevatedButton(
                        content="Save" if is_edit_mode else "Create",
                        on_click=lambda _: on_submit(),
                        bgcolor="#4A6FA5",
                        color="white",
                        style=ft.ButtonStyle(
                            shape=ft.RoundedRectangleBorder(radius=8),
                        ),
                    ),
                ],
            ),
        ],
    )
