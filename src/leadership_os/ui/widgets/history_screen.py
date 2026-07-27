"""HistoryScreen — day history browser for Leadership OS (Flet).

Provides a scrollable list of past days with task summaries, focus time,
and journal previews. Click a day to view its full journal in a preview pane.
"""

from __future__ import annotations

from collections.abc import Callable

import flet as ft

from leadership_os.core.database import Database
from leadership_os.core.enums import TaskStatus
from leadership_os.utils.time_utils import format_duration_short


def _stat_badge(value: str, label: str, color: str) -> ft.Container:
    return ft.Container(
        padding=ft.Padding(8, 4, 8, 4),
        bgcolor="#15152B",
        border_radius=6,
        content=ft.Column(
            spacing=0,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Text(value, color=color, size=16, weight=ft.FontWeight.W_700),
                ft.Text(label, color="#5A5A80", size=8),
            ],
        ),
    )


def _format_date_heading(date_str: str) -> str:
    from datetime import datetime
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        return dt.strftime("%A, %B %d, %Y")
    except ValueError:
        return date_str


def build_history_screen(db: Database, on_close: Callable[[], None]) -> ft.Container:
    """Build the history screen with day list and journal preview.

    Returns a Container that can be placed in the main layout. After the
    container is added to the page, call init_history_list(db, container)
    to populate the day list.

    The returned container exposes two internal attributes for initialization:
      - _lhos_day_list_ref: Ref[ft.Column] for the day list column
      - _lhos_select_day: callable accepting a day_id string
    """

    day_list_ref = ft.Ref[ft.Column]()
    preview_ref = ft.Ref[ft.Container]()

    def select_day(day_id: str):
        if not preview_ref.current:
            return
        day = db.get_day(day_id)
        if day is None:
            preview_ref.current.content = ft.Text("Day not found", color="#747496", size=13)
            preview_ref.current.update()
            return

        summary = db.get_summary(day_id)
        tasks = db.get_tasks_by_day(day_id)
        reflection = db.get_reflection(day_id)

        completed = [t for t in tasks if t.status == TaskStatus.COMPLETED.value]
        pending = [t for t in tasks if t.status in (
            TaskStatus.PENDING.value, TaskStatus.ACTIVE.value, TaskStatus.PAUSED.value
        )]
        carried = [t for t in tasks if t.status == TaskStatus.CARRIED_FORWARD.value]
        focus_seconds = summary.total_focus_seconds if summary else db.calculate_day_focus_seconds(day_id)
        break_seconds = summary.total_break_seconds if summary else db.calculate_day_break_seconds(day_id)

        parts: list[ft.Control] = [
            ft.Text(_format_date_heading(day.date), color="#E8E8F0", size=18, weight=ft.FontWeight.W_700),
            ft.Container(height=8),
            ft.Row(spacing=6, wrap=True, run_spacing=4, controls=[
                _stat_badge(str(len(completed)), "Done", "#66A66B"),
                _stat_badge(str(len(pending)), "Left", "#4A6FA5"),
                _stat_badge(format_duration_short(focus_seconds), "Focus", "#9898B8"),
                _stat_badge(format_duration_short(break_seconds), "Break", "#9898B8"),
            ]),
            ft.Container(height=12),
            ft.Divider(height=1, color="#2D2D4A25"),
            ft.Container(height=12),
        ]

        if completed:
            parts.append(ft.Text("Completed", color="#747496", size=10, weight=ft.FontWeight.W_700))
            for t in completed:
                time_str = f" ({format_duration_short(t.actual_seconds)})" if t.actual_seconds else ""
                parts.append(ft.Text(f"  ✓  {t.title}{time_str}", color="#9898B8", size=12))
            parts.append(ft.Container(height=8))

        if pending:
            parts.append(ft.Text("Incomplete", color="#747496", size=10, weight=ft.FontWeight.W_700))
            for t in pending:
                parts.append(ft.Text(f"  ○  {t.title}", color="#9898B8", size=12))
            parts.append(ft.Container(height=8))

        if carried:
            parts.append(ft.Text("Carried Forward", color="#747496", size=10, weight=ft.FontWeight.W_700))
            for t in carried:
                parts.append(ft.Text(f"  →  {t.title}", color="#9898B8", size=12))
            parts.append(ft.Container(height=8))

        if reflection and reflection.has_content:
            parts.append(ft.Text("Reflection", color="#747496", size=10, weight=ft.FontWeight.W_700))
            acc = reflection.accomplishments.strip()
            if acc:
                parts.append(ft.Text(f"  ✓ {acc[:150]}{'...' if len(acc) > 150 else ''}", color="#9898B8", size=11))
            parts.append(ft.Container(height=8))

        if summary and summary.journal_rel_path:
            parts.append(ft.Text(f"📄 {summary.journal_rel_path}", color="#5A5A80", size=9, italic=True))

        preview_ref.current.content = ft.Column(spacing=2, controls=parts, scroll=ft.ScrollMode.AUTO)
        preview_ref.current.update()

    day_list_column = ft.Column(ref=day_list_ref, spacing=4, scroll=ft.ScrollMode.AUTO)

    container = ft.Container(
        expand=True, bgcolor="#0D0D1A", padding=0,
        content=ft.Column(spacing=0, controls=[
            ft.Container(height=52, padding=ft.Padding(20, 0, 16, 0), content=ft.Row(
                vertical_alignment=ft.CrossAxisAlignment.CENTER, controls=[
                    ft.Text("History", color="#E8E8F0", size=18, weight=ft.FontWeight.W_700),
                    ft.Container(expand=True),
                    ft.IconButton(icon=ft.Icons.CLOSE, icon_size=18, icon_color="#747496", on_click=lambda _: on_close()),
                ],
            )),
            ft.Container(expand=True, padding=ft.Padding(16, 8, 16, 16), content=ft.Row(spacing=12, controls=[
                ft.Container(width=260, expand=True, bgcolor="#14142A", border_radius=10, padding=ft.Padding(8, 8, 8, 8),
                    content=ft.Column(spacing=0, controls=[
                        ft.Container(padding=ft.Padding(4, 0, 4, 8),
                            content=ft.Text("RECENT DAYS", color="#747496", size=9, weight=ft.FontWeight.W_700)),
                        ft.Container(expand=True, content=day_list_column),
                    ])),
                ft.Container(expand=True, bgcolor="#14142A", border_radius=10, padding=ft.Padding(16, 16, 16, 16),
                    content=ft.Container(ref=preview_ref, expand=True,
                        content=ft.Column(spacing=0, horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            alignment=ft.MainAxisAlignment.CENTER, controls=[
                                ft.Icon(ft.Icons.ARROW_BACK, size=24, color="#3A3A5C"),
                                ft.Container(height=8),
                                ft.Text("Select a day to preview", color="#5A5A80", size=12),
                            ]))),
            ])),
        ]),
    )

    # Expose internal handles so init_history_list doesn't need to walk the
    # widget tree. Prefixed with _lhos to avoid collisions with Flet internals.
    container._lhos_select_day = select_day  # type: ignore[attr-defined]
    container._lhos_day_list_ref = day_list_ref  # type: ignore[attr-defined]
    return container


def init_history_list(db: Database, container: ft.Container) -> None:
    """Initialize the history screen's day list after the container is added to the page.

    Must be called after the container returned by build_history_screen is rendered.

    Args:
        db: Database instance for querying historical data.
        container: The Container returned by build_history_screen.
    """
    select_day = getattr(container, "_lhos_select_day", None)
    if select_day is None:
        import logging
        logging.getLogger(__name__).warning("History screen missing _lhos_select_day callback")
        return

    day_list_ref = getattr(container, "_lhos_day_list_ref", None)
    if day_list_ref is None or day_list_ref.current is None:
        import logging
        logging.getLogger(__name__).warning("History screen missing day list ref")
        return

    _populate_day_list(db, day_list_ref.current, select_day)


def _populate_day_list(
    db: Database,
    day_list: ft.Column,
    select_day: Callable[[str], None],
) -> None:
    """Populate the day list Column with historical day entries.

    Each entry has an on_click handler that calls select_day(day_id)
    to show the day's details in the preview pane.
    """
    from datetime import date

    previous = db.get_previous_days(limit=30)
    if not previous:
        day_list.controls = [
            ft.Container(padding=ft.Padding(12, 20, 12, 20), content=ft.Column(
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Icon(ft.Icons.HISTORY, size=28, color="#4A4A7040"),
                    ft.Container(height=8),
                    ft.Text("No history yet", color="#747496", size=12, weight=ft.FontWeight.W_700),
                    ft.Text("Your completed days will appear here", color="#5A5A80", size=11),
                ],
            )),
        ]
        day_list.update()
        return

    entries: list[ft.Control] = []
    for day in previous:
        summary = db.get_summary(day.id)
        completed = summary.completed if summary else 0
        total = summary.total_planned if summary else 0
        focus = summary.total_focus_seconds if summary else 0
        try:
            dt = date.fromisoformat(day.date)
            date_label = dt.strftime("%a, %b %d")
        except ValueError:
            date_label = day.date
        pct = (completed / total * 100) if total > 0 else 0
        status_color = (
            "#66A66B" if pct >= 75
            else "#4A6FA5" if pct >= 40
            else "#C4A35A" if total > 0
            else "#747496"
        )
        completion_text = f"{completed}/{total} tasks" if total > 0 else "No tasks"

        entries.append(ft.Container(
            height=56, bgcolor="#15152B", border_radius=8,
            border=ft.Border.all(1, "#2D2D4A20"), padding=ft.Padding(10, 8, 10, 8),
            on_click=lambda _, did=day.id: select_day(did),
            content=ft.Row(spacing=0, vertical_alignment=ft.CrossAxisAlignment.CENTER, controls=[
                ft.Container(width=3, height=40, bgcolor=status_color, border_radius=1.5),
                ft.Container(width=10),
                ft.Column(spacing=2, expand=True, controls=[
                    ft.Text(date_label, color="#E8E8F0", size=13, weight=ft.FontWeight.W_600),
                    ft.Row(spacing=8, controls=[
                        ft.Text(completion_text, color="#9898B8", size=10),
                        ft.Text(f"Focus {format_duration_short(focus)}", color="#5A5A80", size=10),
                    ]),
                ]),
            ]),
        ))
    day_list.controls = entries
    day_list.update()
