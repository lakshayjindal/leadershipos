"""TopBar — top navigation bar (Flet).

Displays the Leadership OS brand, and right-side action buttons
(search, settings, command palette).
"""

from __future__ import annotations

import flet as ft

from leadership_os.ui.theme import Theme


def build_top_bar(
    on_search,
    on_settings,
    on_command_palette,
) -> ft.Container:
    """Build the top navigation bar.

    Args:
        on_search: Callback for search button.
        on_settings: Callback for settings button.
        on_command_palette: Callback for command palette button.

    Returns:
        A Container representing the top bar.
    """
    return ft.Container(
        height=48,
        bgcolor="#14142A",
        content=ft.Row(
            spacing=0,
            controls=[
                # Brand section (160dp, matching sidebar width)
                ft.Container(
                    width=160,
                    height=48,
                    bgcolor="#14142A",
                    content=ft.Row(
                        spacing=0,
                        controls=[
                            # Accent bar
                            ft.Container(
                                width=3,
                                height=48,
                                bgcolor="#4A6FA5",
                            ),
                            ft.Container(width=12),
                            ft.Text(
                                "Leadership OS",
                                color="#E8E8F0",
                                size=11,
                                weight=ft.FontWeight.W_700,
                            ),
                        ],
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                ),
                # Spacer
                ft.Container(expand=True),
                # Right action buttons
                ft.Container(
                    width=140,
                    height=48,
                    bgcolor="#14142A",
                    padding=ft.Padding(4, 0, 4, 0),
                    content=ft.Row(
                        spacing=2,
                        controls=[
                            ft.IconButton(
                                icon=ft.Icons.SEARCH,
                                icon_size=17,
                                icon_color="#747496",
                                on_click=lambda _: on_search(),
                            ),
                            ft.IconButton(
                                icon=ft.Icons.SETTINGS,
                                icon_size=17,
                                icon_color="#747496",
                                on_click=lambda _: on_settings(),
                            ),
                            ft.IconButton(
                                icon=ft.Icons.KEYBOARD,
                                icon_size=17,
                                icon_color="#747496",
                                on_click=lambda _: on_command_palette(),
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.END,
                    ),
                ),
            ],
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        ),
    )
