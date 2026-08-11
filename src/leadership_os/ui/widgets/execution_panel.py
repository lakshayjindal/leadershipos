"""ExecutionPanel — right execution panel (Flet).

The heart of Leadership OS. Shows current task, focus timer, session info,
daily progress, next task, and action buttons.

Apple-style light design: white utility cards on parchment canvas with
hairline borders, Action Blue pill primary buttons.
"""

from __future__ import annotations

import flet as ft

from leadership_os.ui.theme import (
    GRAY_2,
    GRAY_3,
    GRAY_4,
    GRAY_5,
    HAIRLINE,
    INK,
    ON_PRIMARY,
    PARCHMENT,
    PEARL,
    PRIMARY,
    Theme,
)

# ─── Card helper ────────────────────────────────────────────────────


def _card(
    content: ft.Control,
    height: int | None = None,
    padding: int = 14,
) -> ft.Container:
    """Wrap content in a consistent white utility card."""
    return ft.Container(
        height=height,
        bgcolor=PEARL,
        border_radius=Theme.radius["lg"],
        border=ft.Border.all(1, HAIRLINE),
        padding=padding,
        content=content,
    )


# ─── Stat counter helper ────────────────────────────────────────────


def _stat_box(value: str, label: str, color: str, border_color: str) -> ft.Container:
    """Build a compact stat display."""
    return ft.Container(
        expand=True,
        bgcolor=PARCHMENT,
        border_radius=Theme.radius["sm"],
        border=ft.Border.all(1, border_color),
        padding=ft.Padding(0, 6, 0, 2),
        content=ft.Column(
            spacing=0,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Text(value, color=color, size=22, weight=ft.FontWeight.W_700),
                ft.Text(label, color=color, size=8, opacity=0.5),
            ],
        ),
    )


# ─── Build Execution Panel ──────────────────────────────────────────


def build_execution_panel(
    # Task info
    current_task_title: str,
    current_task_priority: str,
    # Timer
    timer_display: str,
    timer_running: bool,
    panel_state: str,  # idle, working, break
    session_elapsed: str,
    session_estimated: str,
    # Progress
    completed_count: int,
    total_count: int,
    progress_status: str,
    focus_time_display: str,
    # Next up
    next_task_title: str,
    # Break info (Phase 6)
    break_type_label: str = "",
    break_elapsed: str = "",
    # Callbacks
    on_pause=None,
    on_complete=None,
    on_start_break=None,
    on_resume=None,
    on_end_break=None,
) -> ft.Container:
    """Build the right execution panel."""
    panel_width = 280
    has_task = current_task_title != "No active task"
    on_break = panel_state == "break"

    # Timer color
    timer_color = Theme.color("success") if timer_running else GRAY_2

    # State label
    if timer_running:
        state_label = "FOCUSING"
        state_color = Theme.color("success")
    elif on_break:
        state_label = "ON BREAK"
        state_color = Theme.color("error")
    else:
        state_label = "IDLE"
        state_color = GRAY_3

    return ft.Container(
        width=panel_width,
        bgcolor=PARCHMENT,
        padding=12,
        content=ft.Column(
            spacing=8,
            controls=[
                # ── CARD: Current Task ───────────────────────────
                ft.Container(
                    height=56 if has_task else 0,
                    opacity=1 if has_task else 0,
                    visible=has_task,
                    bgcolor=PEARL,
                    border_radius=Theme.radius["lg"],
                    border=ft.Border.all(1, HAIRLINE),
                    padding=ft.Padding(14, 10, 14, 10),
                    content=ft.Column(
                        spacing=4,
                        controls=[
                            ft.Text("CURRENT TASK", color=GRAY_3, size=8, weight=ft.FontWeight.W_700),
                            ft.Text(current_task_title, color=INK, size=15, weight=ft.FontWeight.W_700),
                            ft.Text(current_task_priority, color=GRAY_2, size=10),
                        ],
                    ),
                ),

                # ── CARD: Empty Placeholder ──────────────────────
                ft.Container(
                    height=56 if not has_task else 0,
                    opacity=1 if not has_task else 0,
                    visible=not has_task,
                    bgcolor=PEARL,
                    border_radius=Theme.radius["lg"],
                    border=ft.Border.all(1, HAIRLINE),
                    padding=ft.Padding(14, 14, 14, 14),
                    content=ft.Column(
                        spacing=2,
                        controls=[
                            ft.Text("No active task", color=GRAY_3, size=13),
                            ft.Text("Start one from Today's Plan", color=GRAY_4, size=10),
                        ],
                    ),
                ),

                # ── CARD: Timer (focal point) ────────────
                _card(
                    height=140 if on_break else 120,
                    padding=14,
                    content=ft.Column(
                        spacing=0,
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        controls=[
                            # Large timer
                            ft.Container(
                                height=72,
                                alignment=ft.Alignment(0, 0),
                                content=ft.Text(
                                    timer_display,
                                    color=timer_color,
                                    size=56,
                                    weight=ft.FontWeight.W_700,
                                    font_family="Roboto Mono",
                                ),
                            ),
                            # State label
                            ft.Text(
                                state_label,
                                color=state_color,
                                size=10,
                                weight=ft.FontWeight.W_700,
                            ),
                            # Sub-label
                            ft.Text(
                                f"{break_type_label}  ·  {break_elapsed}" if on_break and break_type_label else (
                                    f"Elapsed {session_elapsed}  ·  Remain {session_estimated}"
                                ),
                                color=Theme.color("error") if on_break else GRAY_3,
                                size=9,
                            ),
                        ],
                    ),
                ),

                # ── CARD: Progress ───────────────────────────────
                _card(
                    height=96,
                    padding=14,
                    content=ft.Column(
                        spacing=6,
                        controls=[
                            # Header row
                            ft.Row(
                                controls=[
                                    ft.Text("TODAY'S PROGRESS", color=GRAY_3, size=8, weight=ft.FontWeight.W_700),
                                    ft.Text(progress_status, color=GRAY_2, size=10),
                                ],
                                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            ),
                            # Progress bar
                            ft.Container(
                                height=4,
                                border_radius=2,
                                bgcolor=GRAY_5,
                                content=ft.Container(
                                    height=4,
                                    border_radius=2,
                                    bgcolor=Theme.color("success") if total_count > 0 and completed_count >= total_count else PRIMARY,
                                    width=max(4, panel_width * 0.75 * min(1.0, completed_count / max(1, total_count))),
                                ),
                            ),
                            # Stat counters
                            ft.Row(
                                spacing=6,
                                controls=[
                                    _stat_box(str(int(completed_count)), "Done", Theme.color("success"), "#34c75940"),
                                    _stat_box(str(int(max(0, total_count - completed_count))), "Left", PRIMARY, "#0066cc40"),
                                    _stat_box(focus_time_display, "Focus", GRAY_2, "#6e6e7340"),
                                ],
                            ),
                        ],
                    ),
                ),

                # ── CARD: Next Up ────────────────────────────────
                _card(
                    height=42,
                    padding=14,
                    content=ft.Column(
                        spacing=2,
                        controls=[
                            ft.Text("NEXT UP", color=GRAY_3, size=8, weight=ft.FontWeight.W_700),
                            ft.Text(
                                next_task_title if next_task_title else "—",
                                color=GRAY_2 if next_task_title else GRAY_5,
                                size=13,
                                italic=not next_task_title,
                            ),
                        ],
                    ),
                ),

                # ── Spacer ───────────────────────────────────────
                ft.Container(expand=True),

                # ── CARD: Actions ────────────────────────────────
                _card(
                    height=160,
                    padding=14,
                    content=ft.Column(
                        spacing=4,
                        controls=[
                            ft.Text("ACTIONS", color=GRAY_3, size=8, weight=ft.FontWeight.W_700),
                            ft.Container(height=2),

                            # Complete — PRIMARY (blue pill)
                            ft.Button(
                                content=ft.Text("✓  Complete Task", color=ON_PRIMARY),
                                disabled=not has_task,
                                on_click=lambda _: on_complete(),
                                height=40,
                                bgcolor=PRIMARY if has_task else "#0066cc40",
                                style=ft.ButtonStyle(
                                    shape=ft.RoundedRectangleBorder(radius=Theme.radius["pill"]),
                                ),
                            ),

                            # Pause
                            ft.TextButton(
                                content="II  Pause",
                                disabled=not has_task,
                                on_click=lambda _: on_pause(),
                                height=34,
                                style=ft.ButtonStyle(
                                    color=GRAY_2 if has_task else "#6e6e7340",
                                    bgcolor=PARCHMENT if has_task else "#f5f5f720",
                                    shape=ft.RoundedRectangleBorder(radius=Theme.radius["sm"]),
                                ),
                            ),

                            # Start Break — only when NOT on a break
                            ft.TextButton(
                                content="☕  Start Break",
                                disabled=not has_task,
                                visible=not on_break,
                                on_click=lambda _: on_start_break(),
                                height=30,
                                style=ft.ButtonStyle(
                                    color="#0066cc" if has_task else "#0066cc40",
                                    bgcolor="#0066cc14" if has_task else "#0066cc0a",
                                    shape=ft.RoundedRectangleBorder(radius=Theme.radius["sm"]),
                                ),
                            ),

                            # Separator — only between the two button groups
                            ft.Divider(height=1, color="#f0f0f0", visible=on_break),

                            # Resume — BREAK PRIMARY (only while on break)
                            ft.Button(
                                content=ft.Text("▶  Resume Work", color=ON_PRIMARY),
                                visible=on_break,
                                on_click=lambda _: on_resume(),
                                height=40,
                                bgcolor=Theme.color("success"),
                                style=ft.ButtonStyle(
                                    shape=ft.RoundedRectangleBorder(radius=Theme.radius["pill"]),
                                ),
                            ),

                            # End Break — only while on a break
                            ft.TextButton(
                                content="■  End Break",
                                visible=on_break,
                                on_click=lambda _: on_end_break(),
                                height=30,
                                style=ft.ButtonStyle(
                                    color=Theme.color("error"),
                                    bgcolor="#ff3b3014",
                                    shape=ft.RoundedRectangleBorder(radius=Theme.radius["sm"]),
                                ),
                            ),
                        ],
                    ),
                ),
            ],
        ),
    )
