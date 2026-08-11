"""Command Palette — VS Code-style command palette for Leadership OS (Flet).

Provides a floating overlay triggered by Ctrl+K for quick actions:
- Global search across tasks, journals, and sessions (SearchEngine)
- Quick commands (Start Break, End Review, etc.)
- Navigation (Settings, History, Today)
- Recent searches
- Fuzzy text matching with term highlighting

Design: Uses a Stack-based overlay that covers the entire app. When visible,
it captures keyboard focus and provides a filterable list of grouped results.
"""

from __future__ import annotations

import logging
from typing import Any

import flet as ft

from leadership_os.core.task_engine import TaskEngine
from leadership_os.ui.theme import (
    CANVAS,
    DIVIDER_SOFT,
    GRAY_3,
    GRAY_4,
    HAIRLINE,
    INK,
    PARCHMENT,
    PRIMARY,
    Theme,
)

logger = logging.getLogger(__name__)

# Result categories shown as section headers
_SECTION_LABELS = {
    "task": "TASKS",
    "journal": "JOURNAL ENTRIES",
    "session": "SESSIONS",
}


# ─── Fuzzy matching ───────────────────────────────────────────────────


def _fuzzy_match(query: str, text: str) -> bool:
    """Simple fuzzy match — all chars of query must appear in order in text."""
    if not query:
        return True
    query_lower = query.lower()
    text_lower = text.lower()
    idx = 0
    for ch in query_lower:
        idx = text_lower.find(ch, idx)
        if idx == -1:
            return False
        idx += 1
    return True


# ─── Main Builder ─────────────────────────────────────────────────────


def build_command_palette(
    task_engine: TaskEngine,
    on_search_task,
    on_run_command,
    on_close,
    search_engine=None,
    on_open_day=None,
) -> ft.Container:
    """Build the command palette overlay.

    Args:
        task_engine: TaskEngine for searching today's tasks (fallback).
        on_search_task: Called with task_id when user selects a task result.
        on_run_command: Called with command_name when user selects a command.
        on_close: Called to close/hide the palette.
        search_engine: Optional SearchEngine for global grouped search.
            When provided, results are grouped into Tasks / Journal Entries /
            Sessions with term highlighting and recent searches.
        on_open_day: Optional callable accepting a day_id — invoked when a
            journal entry or session result is selected (navigates to History).

    Returns:
        A Container representing the full-screen overlay.
    """
    input_ref = ft.Ref[ft.TextField]()
    results_ref = ft.Ref[ft.Column]()
    selected_index_ref = [0]  # Mutable list for closure capture
    clickable_handlers: list = []  # Parallel list of click callbacks
    row_containers: list = []  # Parallel list of row Containers for highlight updates

    # Predefined commands
    commands: list[dict[str, Any]] = [
        {"icon": "⏸", "title": "Pause Current Task", "action": "pause_task"},
        {"icon": "✓", "title": "Complete Current Task", "action": "complete_task"},
        {"icon": "☕", "title": "Start Break", "action": "start_break"},
        {"icon": "▶", "title": "End Break / Resume", "action": "end_break"},
        {"icon": "📝", "title": "End-of-Day Review", "action": "end_day"},
        {"icon": "📋", "title": "Go to Today", "action": "goto_today"},
        {"icon": "📚", "title": "Go to History", "action": "goto_history"},
        {"icon": "⚙", "title": "Open Settings", "action": "goto_settings"},
        {"icon": "🔍", "title": "Search All", "action": "search"},
    ]

    def _build_result_row(
        icon: str,
        title: str,
        subtitle: str = "",
        on_click=None,
        highlight: bool = False,
        title_spans: list | None = None,
    ) -> ft.Container:
        """Build a single result row for the palette."""
        bg = PARCHMENT if highlight else "transparent"
        title_control = (
            ft.Text(spans=title_spans, size=13)
            if title_spans
            else ft.Text(title, color=INK, size=13, weight=ft.FontWeight.W_500)
        )
        return ft.Container(
            height=40,
            bgcolor=bg,
            border_radius=Theme.radius["sm"],
            padding=ft.Padding(12, 0, 12, 0),
            on_click=on_click,
            content=ft.Row(
                spacing=10,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Text(icon, size=14, color=GRAY_3),
                    ft.Column(
                        spacing=0,
                        expand=True,
                        controls=[
                            title_control,
                            ft.Text(subtitle, color=GRAY_4, size=10) if subtitle else ft.Container(),
                        ],
                    ),
                ],
            ),
        )

    def _section_header(text: str, top_pad: int = 0) -> ft.Container:
        """Build a section header row."""
        return ft.Container(
            padding=ft.Padding(8, top_pad, 8, 0),
            content=ft.Text(text, color=GRAY_3, size=9, weight=ft.FontWeight.W_700),
        )

    def _highlight_spans(text: str, query: str) -> list:
        """Build TextSpans with the query highlighted."""
        from leadership_os.core.search_engine import highlight_segments

        spans: list[ft.TextSpan] = []
        for segment, is_match in highlight_segments(text, query):
            spans.append(ft.TextSpan(
                segment,
                style=ft.TextStyle(
                    color=PRIMARY if is_match else INK,
                    weight=ft.FontWeight.W_700 if is_match else ft.FontWeight.W_500,
                ),
            ))
        return spans

    def _reset_clickable() -> None:
        clickable_handlers.clear()
        row_containers.clear()

    def _apply_highlight() -> None:
        """Update the selected row's background without rebuilding the list."""
        selected = selected_index_ref[0]
        for i, container in enumerate(row_containers):
            container.bgcolor = PARCHMENT if i == selected else "transparent"
        if results_ref.current:
            results_ref.current.update()

    def _add_result_row(icon: str, title: str, subtitle: str, handler, title_spans=None):
        """Track a clickable row and its container, keeping handler/index aligned."""
        clickable_handlers.append(handler)
        row = _build_result_row(
            icon, title, subtitle,
            on_click=lambda _, h=handler: h(),
            highlight=False,
            title_spans=title_spans,
        )
        row_containers.append(row)
        return row

    def _update_results(query: str):
        """Filter and render results based on the current query.

        Selection index is preserved across re-renders; it is only reset
        here because callers reset it explicitly before re-rendering.
        """
        if not results_ref.current:
            return

        _reset_clickable()
        results: list[ft.Control] = []
        query_stripped = query.strip()

        # ── Recent searches (shown when the query is empty) ─────────
        if not query_stripped and search_engine is not None:
            recent = search_engine.get_recent_searches()
            if recent:
                results.append(_section_header("RECENT SEARCHES", top_pad=0))
                for term in recent:
                    def _fill_recent(t=term):
                        if input_ref.current:
                            input_ref.current.value = t
                            selected_index_ref[0] = 0
                            _update_results(t)
                            if input_ref.current:
                                input_ref.current.focus()
                    results.append(_add_result_row(
                        "🕘", term, "Search again", _fill_recent,
                    ))

        # ── Commands section ────────────────────────────────────────
        command_results: list[ft.Control] = []
        if not query_stripped:
            for cmd in commands:
                command_results.append(_add_result_row(
                    cmd["icon"], cmd["title"], "",
                    lambda a=cmd["action"]: _dispatch_command(a),
                ))
        else:
            for cmd in commands:
                if _fuzzy_match(query_stripped, cmd["title"]):
                    command_results.append(_add_result_row(
                        cmd["icon"], cmd["title"], "",
                        lambda a=cmd["action"]: _dispatch_command(a),
                    ))

        if command_results:
            results.append(_section_header("COMMANDS", top_pad=0 if not results else 10))
            results.extend(command_results)

        # ── Global search sections (SearchEngine) ───────────────────
        if query_stripped and search_engine is not None:
            try:
                hits = search_engine.search(query_stripped, limit_per_category=8)
                # Group by category preserving engine order
                grouped: dict[str, list] = {}
                for hit in hits:
                    grouped.setdefault(hit.category, []).append(hit)

                for category in ("task", "journal", "session"):
                    category_hits = grouped.get(category, [])
                    if not category_hits:
                        continue
                    label = _SECTION_LABELS.get(category, category.upper())
                    results.append(_section_header(f"{label} ({len(category_hits)})", top_pad=10))
                    for hit in category_hits:
                        icon = {"task": "📋", "journal": "📄", "session": "⏱"}.get(category, "•")
                        if category == "task":
                            results.append(_add_result_row(
                                icon, hit.title, hit.subtitle,
                                lambda hit_id=hit.id: _dispatch_task(hit_id),
                                title_spans=_highlight_spans(hit.title, query_stripped),
                            ))
                        else:
                            results.append(_add_result_row(
                                icon, hit.title, hit.subtitle,
                                lambda hit_day=hit.day_id: _dispatch_day(hit_day),
                                title_spans=_highlight_spans(hit.title, query_stripped),
                            ))
            except Exception as e:
                logger.debug("Global search in palette failed: %s", e)

        # ── Fallback: task-only search via task_engine ──────────────
        if query_stripped and search_engine is None and task_engine:
            try:
                from datetime import date
                today = date.today().isoformat()
                day = task_engine.db.get_day_by_date(today)  # type: ignore[attr-defined]
                if day:
                    tasks = task_engine.get_tasks(day.id)
                    task_results: list[ft.Control] = []
                    for task in tasks:
                        if _fuzzy_match(query_stripped, task.title):
                            priority_icon = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "⚪"}.get(
                                task.priority, "⚪"
                            )
                            status = task.status.replace("_", " ").title()
                            task_results.append(_add_result_row(
                                priority_icon, task.title, status,
                                lambda tid=task.id: _dispatch_task(tid),
                            ))
                    if task_results:
                        results.append(_section_header("TASKS", top_pad=10))
                        results.extend(task_results)
            except Exception as e:
                logger.debug("Task search in palette failed: %s", e)

        # Empty state
        if not results:
            results.append(
                ft.Container(
                    padding=ft.Padding(12, 20, 12, 20),
                    content=ft.Text("No results found", color=GRAY_4, size=12),
                )
            )

        results_ref.current.controls = results
        selected_index_ref[0] = 0
        _apply_highlight()

    def _dispatch_command(action: str):
        """Dispatch a command action and close the palette."""
        if search_engine is not None and input_ref.current and input_ref.current.value:
            search_engine.add_recent_search(input_ref.current.value)
        on_run_command(action)
        on_close()

    def _dispatch_task(task_id: str):
        """Dispatch a task selection and close the palette."""
        if search_engine is not None and input_ref.current and input_ref.current.value:
            search_engine.add_recent_search(input_ref.current.value)
        on_search_task(task_id)
        on_close()

    def _dispatch_day(day_id: str):
        """Open a journal/session result by navigating to its day."""
        if search_engine is not None and input_ref.current and input_ref.current.value:
            search_engine.add_recent_search(input_ref.current.value)
        if on_open_day:
            on_open_day(day_id)
        on_close()

    def _on_input_change(e: ft.ControlEvent):
        _update_results(e.control.value if e.control.value else "")

    def _on_key(e: ft.KeyboardEvent) -> bool:
        """Handle keyboard navigation within the palette.

        Flet 0.86 only supports on_keyboard_event at the Page level, so the
        app wires this handler into the page's combined keyboard handler.

        Returns True if the key was consumed by the palette.
        """
        if e.key == "Arrow Down" or e.key == "Arrow Up":
            total = len(clickable_handlers)
            if total > 0:
                if e.key == "Arrow Down":
                    selected_index_ref[0] = (selected_index_ref[0] + 1) % total
                else:
                    selected_index_ref[0] = (selected_index_ref[0] - 1) % total
                _apply_highlight()
            # Always consume arrows while the palette is visible so they
            # never fall through to task-list navigation behind the overlay.
            return True
        elif e.key == "Enter":
            if clickable_handlers:
                idx = selected_index_ref[0]
                if 0 <= idx < len(clickable_handlers):
                    clickable_handlers[idx]()
            # Always consume Enter while the palette is visible.
            return True
        elif e.key == "Escape":
            on_close()
            return True
        return False

    # ── Build the palette ───────────────────────────────────────────

    palette_card = ft.Container(
        width=560,
        bgcolor=CANVAS,
        border_radius=Theme.radius["lg"],
        border=ft.Border.all(1, HAIRLINE),
        padding=0,
        content=ft.Column(
            spacing=0,
            controls=[
                # Search input
                ft.Container(
                    padding=ft.Padding(16, 14, 16, 10),
                    border=ft.Border(bottom=ft.BorderSide(1, DIVIDER_SOFT)),
                    content=ft.TextField(
                        ref=input_ref,
                        hint_text="Search tasks, journals, sessions, commands...",
                        border=ft.InputBorder.NONE,
                        autofocus=True,
                        text_size=16,
                        color=INK,
                        hint_style=ft.TextStyle(color=GRAY_4, size=16),
                        on_change=_on_input_change,
                    ),
                ),
                # Results list
                ft.Container(
                    height=360,
                    padding=ft.Padding(8, 8, 8, 8),
                    content=ft.Column(
                        ref=results_ref,
                        spacing=2,
                        scroll=ft.ScrollMode.AUTO,
                    ),
                ),
                # Footer hint
                ft.Container(
                    padding=ft.Padding(16, 8, 16, 12),
                    content=ft.Row(
                        spacing=14,
                        controls=[
                            ft.Text("↑↓ Navigate", color=GRAY_4, size=10),
                            ft.Text("↵ Select", color=GRAY_4, size=10),
                            ft.Text("Esc Close", color=GRAY_4, size=10),
                        ],
                    ),
                ),
            ],
        ),
    )

    # Full-screen overlay
    overlay = ft.Container(
        expand=True,
        bgcolor="#00000060",
        alignment=ft.Alignment(0, -0.3),
        on_click=lambda _: on_close(),
        content=palette_card,
    )

    # Prevent click on palette card from closing
    palette_card.on_click = lambda _: None  # type: ignore[method-assign]

    # Expose the keyboard handler so the page-level combined handler can
    # delegate arrow/enter/escape keys to the palette when it is visible.
    overlay._lhos_handle_keyboard = _on_key  # type: ignore[attr-defined]

    return overlay
