"""StatusBar — bottom status bar (Flet).

Shows minimal session information: focus time, completed tasks.
Design: Very small, unobtrusive, parchment footer with hairline-top border.
"""

from __future__ import annotations

import flet as ft

from leadership_os.ui.theme import GRAY_3, HAIRLINE, PARCHMENT


def build_status_bar(
    focus_time_display: str,
    completed_display: str,
) -> ft.Container:
    """Build the bottom status bar.

    Args:
        focus_time_display: Formatted focus time string.
        completed_display: Number of completed tasks.

    Returns:
        A Container representing the status bar.
    """
    return ft.Container(
        height=22,
        bgcolor=PARCHMENT,
        padding=ft.Padding(16, 0, 16, 0),
        border=ft.Border(top=ft.BorderSide(1, HAIRLINE)),
        content=ft.Row(
            spacing=16,
            controls=[
                ft.Text(f"Focus {focus_time_display}", color=GRAY_3, size=9),
                ft.Text(f"Done {completed_display}", color=GRAY_3, size=9),
                ft.Container(expand=True),
            ],
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        ),
    )
