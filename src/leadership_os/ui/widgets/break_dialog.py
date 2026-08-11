"""Break Dialog — break type selection with optional notes.

When the user starts a break, present a dialog to choose:
- Break type: Lunch, Dinner, Tea, Personal, Meeting, Custom
- Optional notes about the break

Uses Flet Chips with visual selection feedback.
"""

from __future__ import annotations

from collections.abc import Callable

import flet as ft

from leadership_os.core.enums import BreakType
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

# Human-readable labels and icons for each break type
BREAK_OPTIONS: list[dict[str, str]] = [
    {"value": BreakType.LUNCH.value, "label": "Lunch", "icon": ft.Icons.RESTAURANT},
    {"value": BreakType.DINNER.value, "label": "Dinner", "icon": ft.Icons.DINNER_DINING},
    {"value": BreakType.TEA.value, "label": "Tea / Coffee", "icon": ft.Icons.COFFEE},
    {"value": BreakType.PERSONAL.value, "label": "Personal", "icon": ft.Icons.PERSON},
    {"value": BreakType.MEETING.value, "label": "Meeting", "icon": ft.Icons.GROUPS},
    {"value": BreakType.CUSTOM.value, "label": "Custom", "icon": ft.Icons.MORE_HORIZ},
]


def build_break_dialog(
    on_confirm: Callable[[str, str], None],
    on_cancel: Callable[[], None],
) -> ft.Container:
    """Build a break type selection panel with visual chip selection.

    Args:
        on_confirm: Called with (break_type, notes) when user confirms.
        on_cancel: Called when user cancels.

    Returns:
        A Container with the break selection UI.
    """
    notes_ref = ft.Ref[ft.TextField]()
    chips_ref = ft.Ref[ft.Column]()

    # Track the selected type
    selection = {"value": BreakType.PERSONAL.value}

    def _select_type(opt_value: str) -> None:
        """Update selection and rebuild chips to show visual feedback."""
        selection["value"] = opt_value
        _rebuild_chips()

    def _rebuild_chips() -> None:
        """Rebuild the chip list with the current selection highlighted."""
        if not chips_ref.current:
            return
        selected = selection["value"]
        new_chips: list[ft.Control] = []
        for opt in BREAK_OPTIONS:
            is_sel = opt["value"] == selected
            new_chips.append(
                ft.Container(
                    on_click=lambda _, o=opt: _select_type(o["value"]),
                    bgcolor=PARCHMENT if not is_sel else "#0066cc14",
                    border=ft.Border.all(
                        1.5,
                        HAIRLINE if not is_sel else PRIMARY,
                    ),
                    border_radius=Theme.radius["md"],
                    padding=ft.Padding(12, 10, 12, 10),
                    content=ft.Row(
                        spacing=8,
                        controls=[
                            ft.Icon(
                                opt["icon"], size=16,
                                color=PRIMARY if is_sel else GRAY_3,
                            ),
                            ft.Text(
                                opt["label"],
                                color=INK if is_sel else GRAY_2,
                                size=13,
                                weight=ft.FontWeight.W_600 if is_sel else ft.FontWeight.W_400,
                            ),
                        ],
                    ),
                )
            )
        chips_ref.current.controls = new_chips
        if chips_ref.current.page:
            chips_ref.current.update()

    def _handle_confirm(_):
        notes = notes_ref.current.value if notes_ref.current else ""
        on_confirm(selection["value"], notes.strip())

    # Build initial chips
    initial_chips: list[ft.Control] = []
    for opt in BREAK_OPTIONS:
        is_sel = opt["value"] == selection["value"]
        initial_chips.append(
            ft.Container(
                on_click=lambda _, o=opt: _select_type(o["value"]),
                bgcolor=PARCHMENT if not is_sel else "#0066cc14",
                border=ft.Border.all(
                    1.5,
                    HAIRLINE if not is_sel else PRIMARY,
                ),
                border_radius=Theme.radius["md"],
                padding=ft.Padding(12, 10, 12, 10),
                content=ft.Row(
                    spacing=8,
                    controls=[
                        ft.Icon(
                            opt["icon"], size=16,
                            color=PRIMARY if is_sel else GRAY_3,
                        ),
                        ft.Text(
                            opt["label"],
                            color=INK if is_sel else GRAY_2,
                            size=13,
                            weight=ft.FontWeight.W_600 if is_sel else ft.FontWeight.W_400,
                        ),
                    ],
                ),
            )
        )

    return ft.Container(
        expand=True,
        bgcolor=PARCHMENT,
        padding=ft.Padding(24, 16, 24, 12),
        content=ft.Column(
            spacing=0,
            controls=[
                # Header
                ft.Row(
                    spacing=0,
                    controls=[
                        ft.Icon(ft.Icons.COFFEE, size=20, color=Theme.color("warning")),
                        ft.Container(width=8),
                        ft.Text("Start Break", color=INK, size=18, weight=ft.FontWeight.W_700),
                    ],
                ),
                ft.Container(height=4),
                ft.Text(
                    "Taking breaks helps maintain focus. Choose a break type below.",
                    color=GRAY_2,
                    size=12,
                    height=1.4,
                ),
                ft.Container(height=20),
                # Break type label
                ft.Text("Break Type", color=GRAY_3, size=10, weight=ft.FontWeight.W_700),
                ft.Container(height=8),
                # Type chips with visual selection
                ft.Column(
                    ref=chips_ref,
                    spacing=0,
                    controls=[
                        ft.ResponsiveRow(
                            spacing=8,
                            run_spacing=8,
                            columns=12,
                            controls=[
                                ft.Column(col={"sm": 6, "md": 4}, controls=[chip])
                                for chip in initial_chips
                            ],
                        ),
                    ],
                ),
                ft.Container(height=16),
                # Notes
                ft.TextField(
                    ref=notes_ref,
                    hint_text="Optional notes about this break...",
                    multiline=True,
                    height=60,
                    min_lines=1,
                    max_lines=3,
                    border=ft.InputBorder.OUTLINE,
                    border_color=HAIRLINE,
                    focused_border_color=PRIMARY,
                    bgcolor="#ffffff",
                    text_style=ft.TextStyle(color=INK, size=13),
                    hint_style=ft.TextStyle(color=GRAY_4, size=13),
                ),
                ft.Container(height=16),
                # Action buttons
                ft.Row(
                    spacing=8,
                    controls=[
                        ft.TextButton(
                            content="Cancel",
                            on_click=lambda _: on_cancel(),
                            style=ft.ButtonStyle(color=GRAY_3),
                        ),
                        ft.Button(
                            content=ft.Text("Start Break", color=ON_PRIMARY),
                            on_click=_handle_confirm,
                            height=40,
                            bgcolor=PRIMARY,
                            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=Theme.radius["pill"])),
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.END,
                ),
            ],
        ),
    )
