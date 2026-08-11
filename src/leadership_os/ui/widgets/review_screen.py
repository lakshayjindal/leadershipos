"""End-of-Day Review screen for Leadership OS (Flet).

Presents the day's summary and three reflection questions, plus an optional
additional-notes field. The user can finalize the day (saves reflection,
generates the journal, and marks the day complete), skip the review, or
cancel and return to the plan.
"""

from __future__ import annotations

from collections.abc import Callable

import flet as ft

from leadership_os.ui.theme import Theme
from leadership_os.utils.time_utils import format_duration_short

# Forward declarations for type hints
OnFinalize = Callable[[dict[str, str]], None]
OnSkip = Callable[[], None]
OnCancel = Callable[[], None]


def _stat_card(label: str, value: str, color: str = Theme.INK) -> ft.Container:
    """Build a compact summary stat card."""
    return ft.Container(
        expand=True,
        height=70,
        bgcolor=Theme.PEARL,
        border_radius=Theme.radius["lg"],
        border=ft.Border.all(1, Theme.HAIRLINE),
        padding=ft.Padding(10, 10, 10, 10),
        content=ft.Column(
            spacing=4,
            alignment=ft.MainAxisAlignment.CENTER,
            controls=[
                ft.Text(value, color=color, size=22, weight=ft.FontWeight.W_700),
                ft.Text(label, color=Theme.GRAY_3, size=9, weight=ft.FontWeight.W_700),
            ],
        ),
    )


def _section_header(title: str) -> ft.Container:
    """Build a small uppercase section header."""
    return ft.Container(
        padding=ft.Padding(0, 16, 0, 8),
        content=ft.Text(title, color=Theme.GRAY_3, size=10, weight=ft.FontWeight.W_700),
    )


def _set_button_disabled(button: ft.Button | None, disabled: bool) -> None:
    """Set the disabled state of a button, updating only if mounted on a page.

    Avoids RuntimeError when the button is built but not yet added to a page
    (common in unit tests).
    """
    if not button or button.disabled == disabled:
        return
    button.disabled = disabled
    try:
        if button.page is not None:
            button.update()
    except RuntimeError:
        # Swallow the expected "control not mounted" error from unit tests.
        pass


def _text_field(
    ref: ft.Ref[ft.TextField],
    label: str,
    value: str,
    hint: str,
    height: int = 80,
) -> ft.TextField:
    """Build a reflection text field with consistent styling."""
    return ft.TextField(
        ref=ref,
        value=value,
        label=label,
        hint_text=hint,
        multiline=True,
        min_lines=2,
        max_lines=4,
        height=height,
        border=ft.InputBorder.OUTLINE,
        border_color=Theme.HAIRLINE,
        focused_border_color=Theme.PRIMARY,
        bgcolor=Theme.CANVAS,
        color=Theme.INK,
        hint_style=ft.TextStyle(color=Theme.GRAY_4, size=12),
        label_style=ft.TextStyle(color=Theme.GRAY_3, size=12),
    )


def build_review_screen(
    focus_seconds: int,
    completed_count: int,
    total_count: int,
    session_count: int,
    break_seconds: int,
    tomorrow_tasks: list[str],
    initial_accomplishments: str = "",
    initial_challenges: str = "",
    initial_tomorrow_first: str = "",
    initial_notes: str = "",
    on_finalize: OnFinalize | None = None,
    on_skip: OnSkip | None = None,
    on_cancel: OnCancel | None = None,
) -> ft.Container:
    """Build the End-of-Day review screen.

    Args:
        focus_seconds: Total focus time for the day.
        completed_count: Number of completed tasks.
        total_count: Total number of tasks.
        session_count: Number of work sessions.
        break_seconds: Total break time for the day.
        tomorrow_tasks: Titles of tasks planned for tomorrow.
        initial_*: Initial values for reflection text fields.
        on_finalize: Called with reflection data dict when user finalizes.
        on_skip: Called when user skips the review.
        on_cancel: Called when user cancels.

    Returns:
        A Container representing the review screen.
    """
    accomplishments_ref = ft.Ref[ft.TextField]()
    challenges_ref = ft.Ref[ft.TextField]()
    tomorrow_first_ref = ft.Ref[ft.TextField]()
    notes_ref = ft.Ref[ft.TextField]()
    finalize_button_ref = ft.Ref[ft.Button]()
    _finalizing = False

    def _handle_finalize(_):
        nonlocal _finalizing
        if _finalizing:
            return
        _finalizing = True
        _set_button_disabled(finalize_button_ref.current, True)

        try:
            data = {
                "accomplishments": accomplishments_ref.current.value or "",
                "challenges": challenges_ref.current.value or "",
                "tomorrow_first": tomorrow_first_ref.current.value or "",
                "additional_notes": notes_ref.current.value or "",
            }
            if on_finalize:
                on_finalize(data)
        finally:
            # Re-enable if the callback did not navigate away (failure path).
            _finalizing = False
            _set_button_disabled(finalize_button_ref.current, False)

    # Summary stat cards
    remaining = max(0, total_count - completed_count)
    summary_row = ft.Row(
        spacing=8,
        controls=[
            _stat_card("Focus Time", format_duration_short(focus_seconds)),
            _stat_card("Completed", str(int(completed_count))),
            _stat_card("Remaining", str(int(remaining))),
            _stat_card("Sessions", str(int(session_count))),
        ],
    )

    # Reflection fields
    reflection_fields = ft.Column(
        spacing=12,
        controls=[
            _text_field(
                accomplishments_ref,
                "What went well?",
                initial_accomplishments,
                "e.g. Finished the notification system...",
            ),
            _text_field(
                challenges_ref,
                "What went wrong?",
                initial_challenges,
                "e.g. Spent too long debugging...",
            ),
            _text_field(
                tomorrow_first_ref,
                "What can be improved?",
                initial_tomorrow_first,
                "e.g. Plan larger tasks more carefully...",
            ),
            _text_field(
                notes_ref,
                "Additional notes",
                initial_notes,
                "Anything else worth recording...",
                height=60,
            ),
        ],
    )

    # Tomorrow preview
    tomorrow_controls: list[ft.Control] = []
    if tomorrow_tasks:
        for title in tomorrow_tasks:
            tomorrow_controls.append(
                ft.Text(f"  •  {title}", color=Theme.GRAY_2, size=12)
            )
    else:
        tomorrow_controls.append(
            ft.Text("No pending tasks for tomorrow.", color=Theme.GRAY_4, size=12, italic=True)
        )

    return ft.Container(
        expand=True,
        bgcolor=Theme.PARCHMENT,
        padding=ft.Padding(24, 16, 24, 12),
        content=ft.Column(
            spacing=0,
            controls=[
                # Header
                ft.Row(
                    controls=[
                        ft.Text("End-of-Day Review", color=Theme.INK, size=18, weight=ft.FontWeight.W_700),
                        ft.Container(expand=True),
                    ],
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                ft.Container(height=4),
                ft.Text(
                    "Reflect on today before you close out. Your answers become part of the daily journal.",
                    color=Theme.GRAY_3, size=11,
                ),
                # Summary
                _section_header("TODAY'S SUMMARY"),
                summary_row,
                # Reflection
                _section_header("REFLECTION"),
                reflection_fields,
                # Tomorrow preview
                _section_header("TOMORROW"),
                ft.Container(
                    bgcolor=Theme.PEARL,
                    border_radius=Theme.radius["lg"],
                    border=ft.Border.all(1, Theme.HAIRLINE),
                    padding=ft.Padding(12, 10, 12, 10),
                    content=ft.Column(spacing=4, controls=tomorrow_controls),
                ),
                # Action buttons
                ft.Container(height=16),
                ft.Row(
                    spacing=8,
                    controls=[
                        ft.TextButton(
                            content=ft.Text("Cancel", color=Theme.GRAY_3),
                            on_click=lambda _: on_cancel() if on_cancel else None,
                        ),
                        ft.TextButton(
                            content=ft.Text("Skip Review", color=Theme.color("error")),
                            on_click=lambda _: on_skip() if on_skip else None,
                        ),
                        ft.Container(expand=True),
                        ft.Button(
                            ref=finalize_button_ref,
                            content=ft.Text("Finalize Day", color=Theme.ON_PRIMARY),
                            bgcolor=Theme.PRIMARY,
                            on_click=_handle_finalize,
                            style=ft.ButtonStyle(
                                shape=ft.RoundedRectangleBorder(radius=Theme.radius["pill"]),
                            ),
                        ),
                    ],
                ),
            ],
            scroll=ft.ScrollMode.AUTO,
        ),
    )
