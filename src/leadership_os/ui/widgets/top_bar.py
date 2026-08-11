"""TopBar — global navigation bar (Flet).

Apple-style global nav: pure-black bar (44px), white nav-link typography,
right-aligned utility cluster (search, settings, command palette, quit).
"""

from __future__ import annotations

import flet as ft

from leadership_os.ui.theme import (
    BLACK,
    GRAY_2,
    ON_DARK,
    TINT_ERROR,
    Theme,
)


def build_top_bar(
    on_search,
    on_settings,
    on_command_palette,
    on_quit=None,
) -> ft.Container:
    """Build the global navigation bar.

    Args:
        on_search: Callback for search button.
        on_settings: Callback for settings button.
        on_command_palette: Callback for command palette button.
        on_quit: Optional callback that fully quits the application.

    Returns:
        A Container representing the top bar.
    """
    nav_height = Theme.heights["global_nav"]

    def _nav_icon(icon, tooltip: str, callback) -> ft.IconButton:
        return ft.IconButton(
            icon=icon,
            icon_size=15,
            icon_color=GRAY_2,
            hover_color=ON_DARK,
            tooltip=tooltip,
            on_click=lambda _: callback(),
        )

    return ft.Container(
        height=nav_height,
        bgcolor=BLACK,
        content=ft.Row(
            spacing=0,
            controls=[
                # Brand section (160dp, matching sidebar width)
                ft.Container(
                    width=160,
                    height=nav_height,
                    bgcolor=BLACK,
                    content=ft.Row(
                        spacing=0,
                        controls=[
                            # Accent bar — Action Blue
                            ft.Container(
                                width=3,
                                height=nav_height,
                                bgcolor=Theme.color("primary"),
                            ),
                            ft.Container(width=12),
                            ft.Text(
                                "Leadership OS",
                                color=ON_DARK,
                                size=12,
                                weight=ft.FontWeight.W_600,
                            ),
                        ],
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                ),
                # Spacer
                ft.Container(expand=True),
                # Right utility cluster (nav-link typography, ~20px spacing)
                ft.Container(
                    width=250,
                    height=nav_height,
                    bgcolor=BLACK,
                    padding=ft.Padding(8, 0, 8, 0),
                    content=ft.Row(
                        spacing=2,
                        controls=[
                            _nav_icon(ft.Icons.SEARCH, "Search (Ctrl+K)", on_search),
                            _nav_icon(ft.Icons.SETTINGS, "Settings", on_settings),
                            _nav_icon(ft.Icons.KEYBOARD, "Command palette", on_command_palette),
                            ft.Container(width=6),
                            # Quit — actually exits the app (not minimize to tray)
                            ft.Container(
                                height=nav_height - 16,
                                padding=ft.Padding(2, 0, 2, 0),
                                content=ft.TextButton(
                                    content=ft.Row(
                                        spacing=4,
                                        controls=[
                                            ft.Icon(
                                                ft.Icons.POWER_SETTINGS_NEW,
                                                size=13,
                                                color=Theme.color("error"),
                                            ),
                                            ft.Text(
                                                "Quit",
                                                color=Theme.color("error"),
                                                size=12,
                                                weight=ft.FontWeight.W_600,
                                            ),
                                        ],
                                    ),
                                    on_click=lambda _: on_quit() if on_quit else None,
                                    style=ft.ButtonStyle(
                                        bgcolor=TINT_ERROR,
                                        shape=ft.RoundedRectangleBorder(radius=Theme.radius["sm"]),
                                        padding=ft.Padding(10, 4, 10, 4),
                                    ),
                                ),
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.END,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                ),
            ],
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        ),
    )
