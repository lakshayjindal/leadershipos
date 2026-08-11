"""TopBar — global navigation bar (Flet).

Apple-style global nav: pure-black bar (44px), white nav-link typography,
right-aligned utility cluster (search, theme toggle, settings, command
palette, quit).
"""

from __future__ import annotations

import flet as ft

from leadership_os.ui.theme import Theme


def build_top_bar(
    on_search,
    on_settings,
    on_command_palette,
    on_quit=None,
    on_toggle_theme=None,
    current_theme="light",
) -> ft.Container:
    """Build the global navigation bar.

    Args:
        on_search: Callback for search button.
        on_settings: Callback for settings button.
        on_command_palette: Callback for command palette button.
        on_quit: Optional callback that fully quits the application.
        on_toggle_theme: Optional callback that flips light/dark theme.
        current_theme: Active theme mode ("light" or "dark") — drives which
            toggle icon is shown (moon when light, sun when dark).

    Returns:
        A Container representing the top bar.
    """
    nav_height = Theme.heights["global_nav"]

    def _nav_icon(icon, tooltip: str, callback) -> ft.IconButton:
        return ft.IconButton(
            icon=icon,
            icon_size=15,
            # Icons sit on the pure-black global nav (stable in BOTH modes),
            # so they must always be light — white nav-link type per DESIGN.md.
            icon_color=Theme.ON_DARK,
            hover_color=Theme.GRAY_4,
            tooltip=tooltip,
            on_click=lambda _: callback(),
        )

    # ── Theme toggle — quick dark/light switch without opening Settings ──
    is_dark = str(current_theme).lower() == "dark"
    toggle_icon = ft.Icons.LIGHT_MODE if is_dark else ft.Icons.DARK_MODE
    toggle_tooltip = "Switch to light mode" if is_dark else "Switch to dark mode"
    toggle_btn = _nav_icon(toggle_icon, toggle_tooltip, on_toggle_theme or (lambda: None))

    return ft.Container(
        height=nav_height,
        bgcolor=Theme.BLACK,
        content=ft.Row(
            spacing=0,
            controls=[
                # Brand section (160dp, matching sidebar width)
                ft.Container(
                    width=160,
                    height=nav_height,
                    bgcolor=Theme.BLACK,
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
                                color=Theme.ON_DARK,
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
                    width=290,
                    height=nav_height,
                    bgcolor=Theme.BLACK,
                    padding=ft.Padding(8, 0, 8, 0),
                    content=ft.Row(
                        spacing=2,
                        controls=[
                            _nav_icon(ft.Icons.SEARCH, "Search (Ctrl+K)", on_search),
                            _nav_icon(ft.Icons.SETTINGS, "Settings", on_settings),
                            _nav_icon(ft.Icons.KEYBOARD, "Command palette", on_command_palette),
                            toggle_btn,
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
                                        bgcolor=Theme.TINT_ERROR,
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
