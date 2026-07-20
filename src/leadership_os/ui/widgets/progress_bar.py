"""ProgressBar — daily progress indicator (Flet).

Shows task completion progress with a horizontal bar.
"""

from __future__ import annotations

import flet as ft


def build_progress_bar(
    value: int,
    max_value: int,
    bar_height: int = 6,
) -> ft.Container:
    """Build a horizontal progress bar.

    Args:
        value: Completed count.
        max_value: Total count.
        bar_height: Height of the bar in pixels.

    Returns:
        A Container with a progress bar.
    """
    progress = min(1.0, value / max_value) if max_value > 0 else 0.0

    # Color based on progress
    if progress < 0.4:
        color = "#C4A35A"  # Warm amber
    elif progress < 0.75:
        color = "#4A6FA5"  # Calm blue
    else:
        color = "#66A66B"  # Muted green

    return ft.Stack(
        controls=[
            # Background track
            ft.Container(
                height=bar_height,
                border_radius=bar_height / 2,
                bgcolor="#33335050",
            ),
            # Filled progress
            ft.Container(
                height=bar_height,
                border_radius=bar_height / 2,
                bgcolor=color,
                width=max(bar_height, progress * 100.0) if progress < 1.0 else None,
                expand=progress >= 1.0,
            ),
        ],
        height=bar_height,
    )
