"""TimerDisplay — large timer display with optional progress ring (Flet).

Shows elapsed time in large monospace font.
Optionally displays a circular progress indicator when estimated duration is set.
"""

from __future__ import annotations

import flet as ft

from leadership_os.utils.time_utils import format_duration


def build_timer_display(
    time_text: str,
    is_running: bool,
    estimated_seconds: int = 0,
) -> ft.Container:
    """Build the timer display.

    Args:
        time_text: Formatted time string (HH:MM:SS).
        is_running: Whether the timer is active.
        estimated_seconds: Estimated duration (0 = no ring).

    Returns:
        A Container representing the timer display.
    """
    timer_color = "#4A6FA5" if is_running else "#9898B8"

    content_controls = [
        ft.Container(
            height=80,
            alignment=ft.Alignment(0,0),
            content=ft.Text(
                time_text,
                color=timer_color,
                size=36,
                weight=ft.FontWeight.W_700,
                font_family="Roboto Mono",
            ),
        ),
    ]

    # Progress ring (when estimated_seconds > 0)
    if estimated_seconds > 0:
        # Parse time to get progress
        parts = time_text.split(":")
        elapsed = int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
        progress = min(1.0, elapsed / estimated_seconds)

        content_controls.append(
            ft.Container(
                height=60,
                alignment=ft.Alignment(0,0),
                content=ft.Stack(
                    width=50,
                    height=50,
                    controls=[
                        # Background circle
                        ft.Container(
                            width=50,
                            height=50,
                            border_radius=25,
                            border=ft.Border.all(3, "#33335050"),
                        ),
                        # ProgressRing overlay
                        ft.ProgressRing(
                            value=progress,
                            color="#4A6FA5",
                            bgcolor="#33335000",
                            width=50,
                            height=50,
                        ),
                    ],
                    alignment=ft.Alignment(0,0),
                ),
            ),
        )

    return ft.Container(
        height=160 if estimated_seconds else 80,
        content=ft.Column(
            spacing=8,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            controls=content_controls,
        ),
    )
