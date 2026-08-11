"""ExecutionPanel — right execution panel (Flet).

The heart of Leadership OS. Shows current task, focus timer, session info,
daily progress, next task, and action buttons.
"""

from __future__ import annotations

import flet as ft

from leadership_os.ui.theme import Theme
from leadership_os.utils.time_utils import format_duration_short

# ─── Card helper ────────────────────────────────────────────────────


def _card(
    content: ft.Control,
    height: int | None = None,
    padding: int = 14,
) -> ft.Container:
    """Wrap content in a consistent card container."""
    return ft.Container(
        height=height,
        bgcolor="#181830",
        border_radius=10,
        border=ft.Border.all(1, "#2D2D4A15"),
        padding=padding,
        content=content,
    )


# ─── Stat counter helper ────────────────────────────────────────────


def _stat_box(value: str, label: str, color: str, border_color: str) -> ft.Container:
    """Build a compact stat display."""
    return ft.Container(
        expand=True,
        bgcolor="#15152B",
        border_radius=6,
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
    timer_color = "#66A66B" if timer_running else "#9898B8"

    # State label
    if timer_running:
        state_label = "FOCUSING"
        state_color = "#66A66B"
    elif on_break:
        state_label = "ON BREAK"
        state_color = "#C45B5B"
    else:
        state_label = "IDLE"
        state_color = "#747496"

    return ft.Container(
        width=panel_width,
        bgcolor="#14142A",
        padding=12,
        content=ft.Column(
            spacing=8,
            controls=[
                # ── CARD: Current Task ───────────────────────────
                ft.Container(
                    height=56 if has_task else 0,
                    opacity=1 if has_task else 0,
                    visible=has_task,
                    bgcolor="#181830",
                    border_radius=10,
                    border=ft.Border.all(1, "#2D2D4A15"),
                    padding=ft.Padding(14, 10, 14, 10),
                    content=ft.Column(
                        spacing=4,
                        controls=[
                            ft.Text("CURRENT TASK", color="#747496", size=8, weight=ft.FontWeight.W_700),
                            ft.Text(current_task_title, color="#E8E8F0", size=15, weight=ft.FontWeight.W_700),
                            ft.Text(current_task_priority, color="#9898B8", size=10),
                        ],
                    ),
                ),

                # ── CARD: Empty Placeholder ──────────────────────
                ft.Container(
                    height=56 if not has_task else 0,
                    opacity=1 if not has_task else 0,
                    visible=not has_task,
                    bgcolor="#181830",
                    border_radius=10,
                    border=ft.Border.all(1, "#2D2D4A15"),
                    padding=ft.Padding(14, 14, 14, 14),
                    content=ft.Column(
                        spacing=2,
                        controls=[
                            ft.Text("No active task", color="#747496", size=13),
                            ft.Text("Start one from Today's Plan", color="#5A5A80", size=10),
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
                                alignment=ft.Alignment(0,0),
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
                                color="#C45B5B" if on_break else "#5A5A80",
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
                                    ft.Text("TODAY'S PROGRESS", color="#747496", size=8, weight=ft.FontWeight.W_700),
                                    ft.Text(progress_status, color="#9898B8", size=10),
                                ],
                                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            ),
                            # Progress bar
                            ft.Container(
                                height=4,
                                border_radius=2,
                                bgcolor="#2D2D4A35",
                                content=ft.Container(
                                    height=4,
                                    border_radius=2,
                                    bgcolor="#66A66B" if total_count > 0 and completed_count >= total_count else "#4A6FA5",
                                    width=max(4, panel_width * 0.75 * min(1.0, completed_count / max(1, total_count))),
                                ),
                            ),
                            # Stat counters
                            ft.Row(
                                spacing=6,
                                controls=[
                                    _stat_box(str(int(completed_count)), "Done", "#66A66B", "#66A66B20"),
                                    _stat_box(str(int(max(0, total_count - completed_count))), "Left", "#4A6FA5", "#4A6FA520"),
                                    _stat_box(focus_time_display, "Focus", "#9898B8", "#9898B818"),
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
                            ft.Text("NEXT UP", color="#747496", size=8, weight=ft.FontWeight.W_700),
                            ft.Text(
                                next_task_title if next_task_title else "—",
                                color="#9898B8" if next_task_title else "#4A4A70",
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
                            ft.Text("ACTIONS", color="#747496", size=8, weight=ft.FontWeight.W_700),
                            ft.Container(height=2),

                            # Complete — PRIMARY
                            ft.Button(
                                content=ft.Text("✓  Complete Task", color="white"),
                                disabled=not has_task,
                                on_click=lambda _: on_complete(),
                                height=40,
                                bgcolor="#4A6FA5" if has_task else "#4A6FA540",
                                style=ft.ButtonStyle(
                                    shape=ft.RoundedRectangleBorder(radius=8),
                                ),
                            ),

                            # Pause
                            ft.TextButton(
                                content="II  Pause",
                                disabled=not has_task,
                                on_click=lambda _: on_pause(),
                                height=34,
                                style=ft.ButtonStyle(
                                    color="#9898B8" if has_task else "#9898B840",
                                    bgcolor="#2D2D4A25" if has_task else "#2D2D4A15",
                                    shape=ft.RoundedRectangleBorder(radius=6),
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
                                    color="#9898B8B0" if has_task else "#9898B840",
                                    bgcolor="#2D2D4A1A" if has_task else "#2D2D4A0D",
                                    shape=ft.RoundedRectangleBorder(radius=6),
                                ),
                            ),

                            # Separator — only between the two button groups
                            ft.Divider(height=1, color="#2D2D4A0D", visible=on_break),

                            # Resume — BREAK PRIMARY (only while on break)
                            ft.Button(
                                content=ft.Text("▶  Resume Work", color="white"),
                                visible=on_break,
                                on_click=lambda _: on_resume(),
                                height=40,
                                bgcolor="#66A66B",
                                style=ft.ButtonStyle(
                                    shape=ft.RoundedRectangleBorder(radius=8),
                                ),
                            ),

                            # End Break — only while on a break
                            ft.TextButton(
                                content="■  End Break",
                                visible=on_break,
                                on_click=lambda _: on_end_break(),
                                height=30,
                                style=ft.ButtonStyle(
                                    color="#9898B8B0",
                                    bgcolor="#2D2D4A1A",
                                    shape=ft.RoundedRectangleBorder(radius=6),
                                ),
                            ),
                        ],
                    ),
                ),
            ],
        ),
    )
