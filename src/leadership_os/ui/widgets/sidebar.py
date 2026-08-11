"""Sidebar — left navigation panel (Flet).

Provides primary navigation between Today, History, and Settings contexts.
Apple-style light surface: white sidebar with hairline right border,
ink text, Action Blue active states, pearl stat cards.
"""

from __future__ import annotations

import flet as ft

from leadership_os.ui.theme import Theme
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
    bg = Theme.PARCHMENT if active else "transparent"
    text_color = Theme.INK if active else Theme.GRAY_2
    icon_color = Theme.PRIMARY if active else Theme.GRAY_3

    return ft.Container(
        height=34,
        bgcolor=bg,
        border_radius=Theme.radius["sm"],
        on_click=on_click,
        content=ft.Row(
            spacing=8,
            controls=[
                # Active indicator
                ft.Container(
                    width=3,
                    height=14,
                    bgcolor=Theme.PRIMARY if active else "transparent",
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
                    weight=ft.FontWeight.W_600 if active else ft.FontWeight.W_400,
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
    active_view: str = "today",
    today_callback=None,
    history_callback=None,
    settings_callback=None,
) -> ft.Container:
    """Build the complete sidebar.

    Args:
        app_state: Current application state string.
        focus_time: Total focus seconds for today.
        completed_count: Number of completed tasks.
        total_count: Total number of tasks.
        status_text: Human-readable status ("Ready", "Focusing", etc.)
        active_view: Which nav item is highlighted — one of "today",
            "history", or "settings". Today-context views ("review",
            "carry_forward", "break_dialog") keep Today highlighted.
        today_callback: Callback for Today nav item.
        history_callback: Callback for History nav item.
        settings_callback: Callback for Settings nav item.

    Returns:
        A Container representing the complete sidebar.
    """
    focus_display = format_duration_short(focus_time)
    progress_text = f"{int(completed_count)}/{int(total_count)} tasks · {status_text}"

    today_active = active_view in ("today", "review", "carry_forward", "break_dialog")
    history_active = active_view == "history"
    settings_active = active_view == "settings"

    return ft.Container(
        width=SIDEBAR_WIDTH,
        bgcolor=Theme.INK,
        padding=ft.Padding(8, 12, 8, 8),
        content=ft.Column(
            spacing=2,
            controls=[
                # NAVIGATION label
                ft.Container(
                    padding=ft.Padding(10, 0, 0, 0),
                    content=ft.Text(
                        "NAVIGATION",
                        color=Theme.GRAY_3,
                        size=9,
                        weight=ft.FontWeight.W_700,
                    ),
                ),

                # Navigation items
                build_nav_item("Today", ft.Icons.CALENDAR_TODAY,
                               active=today_active,
                               on_click=lambda _: today_callback() if today_callback else None),
                build_nav_item("History", ft.Icons.HISTORY, active=history_active,
                               on_click=lambda _: history_callback() if history_callback else None),
                build_nav_item("Settings", ft.Icons.SETTINGS, active=settings_active,
                               on_click=lambda _: settings_callback() if settings_callback else None),

                # Spacer
                ft.Container(expand=True, height=0.1),

                # ── Focus Target Card ────────────────────────────
                ft.Container(
                    height=60,
                    bgcolor=Theme.PEARL,
                    border_radius=Theme.radius["sm"],
                    border=ft.Border.all(1, Theme.HAIRLINE),
                    padding=ft.Padding(10, 8, 10, 8),
                    content=ft.Column(
                        spacing=4,
                        controls=[
                            ft.Row(
                                controls=[
                                    ft.Text("FOCUS TARGET", color=Theme.GRAY_3, size=8, weight=ft.FontWeight.W_700),
                                    ft.Text(focus_display, color=Theme.GRAY_2, size=10, weight=ft.FontWeight.W_700),
                                ],
                                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            ),
                            # Mini progress bar
                            ft.Container(
                                height=3,
                                border_radius=1.5,
                                bgcolor=Theme.GRAY_5,
                                content=ft.Container(
                                    height=3,
                                    border_radius=1.5,
                                    bgcolor=Theme.PRIMARY,
                                    width=max(3, SIDEBAR_WIDTH * 0.75 * min(1.0, completed_count / max(1, total_count))),
                                ),
                            ),
                            ft.Text(progress_text, color=Theme.GRAY_3, size=9),
                        ],
                    ),
                ),

                # Spacer
                ft.Container(expand=True),

                # ── Session Stats Card ───────────────────────────
                ft.Container(
                    height=140,
                    bgcolor=Theme.PEARL,
                    border_radius=Theme.radius["sm"],
                    border=ft.Border.all(1, Theme.HAIRLINE),
                    padding=ft.Padding(10, 10, 10, 10),
                    content=ft.Column(
                        spacing=6,
                        controls=[
                            ft.Text("TODAY", color=Theme.GRAY_3, size=9, weight=ft.FontWeight.W_700),
                            ft.Text(
                                f"{int(completed_count)} / {int(total_count)}",
                                color=Theme.INK,
                                size=24,
                                weight=ft.FontWeight.W_700,
                            ),
                            ft.Divider(height=1, color=Theme.HAIRLINE),
                            ft.Row(
                                controls=[
                                    ft.Text(f"Focus {focus_display}", color=Theme.GRAY_2, size=10),
                                    ft.Text(f"Tasks {int(total_count)}", color=Theme.GRAY_2, size=10),
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
                                        color=Theme.color("success") if app_state == "working" else Theme.PRIMARY if app_state in ("planning", "idle", "startup") else Theme.color("error"),
                                    ),
                                    ft.Text(
                                        status_text,
                                        color=Theme.INK if app_state == "working" else Theme.GRAY_2,
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
