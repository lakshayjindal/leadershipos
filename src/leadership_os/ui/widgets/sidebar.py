"""Sidebar — left navigation panel (Flet).

Provides primary navigation between Today, History, and Settings contexts.
Bottom section shows lightweight session information.
"""

from __future__ import annotations

import flet as ft

from leadership_os.utils.time_utils import format_duration_short

# ─── SidebarNavItem ─────────────────────────────────────────────────

SIDEBAR_WIDTH = 160


def build_nav_item(
    text: str,
    icon: str,
    active: bool,
    on_click,
) -> ft.Container:
    """Build a single navigation item."""
    bg = "#282850" if active else "transparent"
    text_color = "#E8E8F0" if active else "#9898B8"
    icon_color = "#4A6FA5" if active else "#747496"

    return ft.Container(
        height=34,
        bgcolor=bg,
        border_radius=6,
        on_click=on_click,
        content=ft.Row(
            spacing=8,
            controls=[
                # Active indicator
                ft.Container(
                    width=3,
                    height=14,
                    bgcolor="#4A6FA5" if active else "transparent",
                    border_radius=1.5,
                ),
                ft.Icon(
                    icon=icon,
                    size=15,
                    color=icon_color,
                ),
                ft.Text(
                    text,
                    color=text_color,
                    size=12,
                    weight=ft.FontWeight.W_700 if active else ft.FontWeight.W_400,
                ),
            ],
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        ),
    )


def build_sidebar(
    app_state: str,
    focus_time: int,
    completed_count: int,
    total_count: int,
    status_text: str,
    today_callback,
    history_callback,
    settings_callback,
) -> ft.Container:
    """Build the complete sidebar.

    Args:
        app_state: Current application state string.
        focus_time: Total focus seconds for today.
        completed_count: Number of completed tasks.
        total_count: Total number of tasks.
        status_text: Human-readable status ("Ready", "Focusing", etc.)
        today_callback: Callback for Today nav item.
        history_callback: Callback for History nav item.
        settings_callback: Callback for Settings nav item.

    Returns:
        A Container representing the complete sidebar.
    """
    focus_display = format_duration_short(focus_time)
    progress_text = f"{int(completed_count)}/{int(total_count)} tasks · {status_text}"

    return ft.Container(
        width=SIDEBAR_WIDTH,
        bgcolor="#14142A",
        padding=ft.Padding(8, 12, 8, 8),
        content=ft.Column(
            spacing=2,
            controls=[
                # NAVIGATION label
                ft.Container(
                    padding=ft.Padding(10, 0, 0, 0),
                    content=ft.Text(
                        "NAVIGATION",
                        color="#747496",
                        size=9,
                        weight=ft.FontWeight.W_700,
                    ),
                ),

                # Navigation items
                build_nav_item("Today", ft.Icons.CALENDAR_TODAY,
                               active=app_state in ("planning", "working", "break", "idle", "review"),
                               on_click=lambda _: today_callback()),
                build_nav_item("History", ft.Icons.HISTORY, active=False,
                               on_click=lambda _: history_callback()),
                build_nav_item("Settings", ft.Icons.SETTINGS, active=False,
                               on_click=lambda _: settings_callback()),

                # Spacer
                ft.Container(expand=True, height=0.1),

                # ── Focus Target Card ────────────────────────────
                ft.Container(
                    height=60,
                    bgcolor="#15152B",
                    border_radius=8,
                    padding=ft.Padding(10, 8, 10, 8),
                    content=ft.Column(
                        spacing=4,
                        controls=[
                            ft.Row(
                                controls=[
                                    ft.Text("FOCUS TARGET", color="#747496", size=8, weight=ft.FontWeight.W_700),
                                    ft.Text(focus_display, color="#747496", size=10, weight=ft.FontWeight.W_700),
                                ],
                                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            ),
                            # Mini progress bar
                            ft.Container(
                                height=3,
                                border_radius=1.5,
                                bgcolor="#2D2D4A",
                                content=ft.Container(
                                    height=3,
                                    border_radius=1.5,
                                    bgcolor="#4A6FA5",
                                    width=max(3, SIDEBAR_WIDTH * 0.75 * min(1.0, completed_count / max(1, total_count))),
                                ),
                            ),
                            ft.Text(progress_text, color="#5A5A80", size=9),
                        ],
                    ),
                ),

                # Spacer
                ft.Container(expand=True),

                # ── Session Stats Card ───────────────────────────
                ft.Container(
                    height=140,
                    bgcolor="#15152B",
                    border_radius=8,
                    padding=ft.Padding(10, 10, 10, 10),
                    content=ft.Column(
                        spacing=6,
                        controls=[
                            ft.Text("TODAY", color="#747496", size=9, weight=ft.FontWeight.W_700),
                            ft.Text(
                                f"{int(completed_count)} / {int(total_count)}",
                                color="#E8E8F0",
                                size=24,
                                weight=ft.FontWeight.W_700,
                            ),
                            ft.Divider(height=1, color="#2D2D4A20"),
                            ft.Row(
                                controls=[
                                    ft.Text(f"Focus {focus_display}", color="#747496", size=10),
                                    ft.Text(f"Tasks {int(total_count)}", color="#747496", size=10),
                                ],
                                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            ),
                            ft.Row(
                                spacing=6,
                                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                                controls=[
                                    ft.Icon(
                                        icon=ft.Icons.CIRCLE,
                                        size=6,
                                        color="#66A66B" if app_state == "working" else "#4A6FA5" if app_state in ("planning", "idle", "startup") else "#C45B5B",
                                    ),
                                    ft.Text(
                                        status_text,
                                        color="#E8E8F0" if app_state == "working" else "#747496",
                                        size=10,
                                        weight=ft.FontWeight.W_700 if app_state == "working" else ft.FontWeight.W_400,
                                    ),
                                ],
                            ),
                        ],
                    ),
                ),
            ],
        ),
    )
