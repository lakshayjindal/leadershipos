"""TaskForm — task creation and editing form (Flet).

Minimal form that initially shows only the title field.
Advanced options (priority, deadline, estimated time, notes) expand on request.
Apple-style light: white inputs, hairline borders, Action Blue focus.
"""

from __future__ import annotations

import flet as ft

from leadership_os.ui.theme import (
    GRAY_2,
    GRAY_3,
    GRAY_4,
    HAIRLINE,
    INK,
    ON_PRIMARY,
    PARCHMENT,
    PRIMARY,
    Theme,
)

# Chip fill — soft parchment tint
PARCHMENT_CHIP = PARCHMENT


def _field(
    value: str,
    hint_text: str,
    on_change,
    height: int = 48,
    keyboard_type=None,
    multiline: bool = False,
    min_lines: int = 1,
    max_lines: int = 1,
) -> ft.TextField:
    """Build a consistently styled Apple-like input field."""
    return ft.TextField(
        value=value,
        hint_text=hint_text,
        on_change=on_change,
        height=height,
        max_length=200,
        border=ft.InputBorder.OUTLINE,
        border_color=HAIRLINE,
        focused_border_color=PRIMARY,
        bgcolor="#ffffff",
        text_style=ft.TextStyle(color=INK, size=13),
        hint_style=ft.TextStyle(color=GRAY_4, size=13),
        keyboard_type=keyboard_type,
        multiline=multiline,
        min_lines=min_lines,
        max_lines=max_lines,
    )


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
            _field(
                title,
                "Task title...",
                lambda e: on_title_change(e.control.value),
            ),
            # Advanced toggle
            ft.TextButton(
                content="Advanced options" if not advanced_visible else "Hide options",
                on_click=lambda _: on_toggle_advanced(),
                style=ft.ButtonStyle(
                    color=GRAY_2,
                ),
            ),
            # Advanced fields
            ft.Column(
                spacing=8,
                visible=advanced_visible,
                controls=[
                    _field(
                        str(estimated_minutes) if estimated_minutes else "",
                        "Estimated minutes (optional)",
                        lambda e: on_estimated_change(int(e.control.value) if e.control.value.isdigit() else 0),
                        keyboard_type=ft.KeyboardType.NUMBER,
                    ),
                    _field(
                        deadline,
                        "Deadline — e.g. 17:00 or Before Lunch",
                        lambda e: on_deadline_change(e.control.value),
                    ),
                    ft.Row(
                        spacing=4,
                        controls=[
                            ft.Chip(
                                label=ft.Text("Before Lunch", size=10),
                                on_select=lambda _: on_deadline_change("Before Lunch"),
                                bgcolor=PARCHMENT_CHIP,
                                selected_color=PRIMARY,
                            ),
                            ft.Chip(
                                label=ft.Text("Before Dinner", size=10),
                                on_select=lambda _: on_deadline_change("Before Dinner"),
                                bgcolor=PARCHMENT_CHIP,
                                selected_color=PRIMARY,
                            ),
                            ft.Chip(
                                label=ft.Text("End of Day", size=10),
                                on_select=lambda _: on_deadline_change("End of Day"),
                                bgcolor=PARCHMENT_CHIP,
                                selected_color=PRIMARY,
                            ),
                        ],
                    ),
                    _field(
                        notes,
                        "Notes (optional)",
                        lambda e: on_notes_change(e.control.value),
                        height=80,
                        multiline=True,
                        min_lines=2,
                        max_lines=4,
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
                        style=ft.ButtonStyle(color=GRAY_3),
                    ),
                    ft.Button(
                        content=ft.Text("Save" if is_edit_mode else "Create", color=ON_PRIMARY),
                        on_click=lambda _: on_submit(),
                        bgcolor=PRIMARY,
                        style=ft.ButtonStyle(
                            shape=ft.RoundedRectangleBorder(radius=Theme.radius["pill"]),
                        ),
                    ),
                ],
            ),
        ],
    )
