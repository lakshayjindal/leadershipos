"""Command Palette — VS Code-style command palette for Leadership OS (Flet).

Provides a floating overlay triggered by Ctrl+K for quick actions:
- Search across today's tasks
- Quick commands (Start Break, End Review, etc.)
- Navigation (Settings, History, Today)
- Fuzzy text matching on task titles

Design: Uses a Stack-based overlay that covers the entire app. When visible,
it captures keyboard focus and provides a filterable list of results.
"""

from __future__ import annotations

import logging
from typing import Any

import flet as ft

from leadership_os.core.task_engine import TaskEngine

logger = logging.getLogger(__name__)


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
) -> ft.Container:
    """Build the command palette overlay.

    Args:
        task_engine: TaskEngine for searching tasks.
        on_search_task: Called with task_id when user selects a task result.
        on_run_command: Called with command_name when user selects a command.
        on_close: Called to close/hide the palette.

    Returns:
        A Container representing the full-screen overlay.
    """
    input_ref = ft.Ref[ft.TextField]()
    results_ref = ft.Ref[ft.Column]()
    selected_index_ref = [0]  # Mutable list for closure capture

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
        {"icon": "🔍", "title": "Search All Tasks", "action": "search"},
    ]

    def _build_result_row(
        icon: str,
        title: str,
        subtitle: str = "",
        on_click=None,
        highlight: bool = False,
    ) -> ft.Container:
        """Build a single result row for the palette."""
        bg = "#282850" if highlight else "transparent"
        return ft.Container(
            height=40,
            bgcolor=bg,
            border_radius=6,
            padding=ft.Padding(12, 0, 12, 0),
            on_click=on_click,
            content=ft.Row(
                spacing=10,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Text(icon, size=14, color="#9898B8"),
                    ft.Column(
                        spacing=0,
                        expand=True,
                        controls=[
                            ft.Text(title, color="#E8E8F0", size=13, weight=ft.FontWeight.W_500),
                            ft.Text(subtitle, color="#5A5A80", size=10) if subtitle else ft.Container(),
                        ],
                    ),
                ],
            ),
        )

    def _update_results(query: str):
        """Filter and render results based on the current query."""
        if not results_ref.current:
            return

        results: list[ft.Control] = []
        idx = 0
        selected_index_ref[0] = 0
        query_stripped = query.strip()

        # Section: Commands (always shown, filtered by query if non-empty)
        command_results: list[ft.Control] = []
        if not query_stripped:
            # Show all commands when empty
            for cmd in commands:
                command_results.append(_build_result_row(
                    cmd["icon"], cmd["title"],
                    on_click=lambda _, a=cmd["action"]: _dispatch_command(a),
                    highlight=idx == selected_index_ref[0],
                ))
                idx += 1
        else:
            for cmd in commands:
                if _fuzzy_match(query_stripped, cmd["title"]):
                    command_results.append(_build_result_row(
                        cmd["icon"], cmd["title"],
                        on_click=lambda _, a=cmd["action"]: _dispatch_command(a),
                        highlight=idx == selected_index_ref[0],
                    ))
                    idx += 1

        if command_results:
            results.append(
                ft.Container(
                    padding=ft.Padding(8, 4, 8, 0),
                    content=ft.Text("COMMANDS", color="#747496", size=9, weight=ft.FontWeight.W_700),
                )
            )
            results.extend(command_results)

        # Section: Tasks (searched from engine)
        if task_engine and query_stripped:
            # Get today's tasks
            # We need a day_id; the caller provides tasks via the task_engine
            try:
                # Search all tasks from recent days
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
                            task_results.append(_build_result_row(
                                priority_icon, task.title, status,
                                on_click=lambda _, tid=task.id: _dispatch_task(tid),
                                highlight=idx == selected_index_ref[0],
                            ))
                            idx += 1
                    if task_results:
                        results.append(
                            ft.Container(
                                padding=ft.Padding(8, 12 if command_results else 4, 8, 0),
                                content=ft.Text("TASKS", color="#747496", size=9, weight=ft.FontWeight.W_700),
                            )
                        )
                        results.extend(task_results)
            except Exception as e:
                logger.debug("Task search in palette failed: %s", e)

        # Empty state
        if not results:
            results.append(
                ft.Container(
                    padding=ft.Padding(12, 20, 12, 20),
                    content=ft.Text("No results found", color="#5A5A80", size=12),
                )
            )

        results_ref.current.controls = results
        results_ref.current.update()

    def _dispatch_command(action: str):
        """Dispatch a command action and close the palette."""
        if action == "goto_today" or action == "goto_history" or action == "goto_settings":
            on_run_command(action)
        else:
            on_run_command(action)
        on_close()

    def _dispatch_task(task_id: str):
        """Dispatch a task selection and close the palette."""
        on_search_task(task_id)
        on_close()

    def _on_input_change(e: ft.ControlEvent):
        _update_results(e.control.value if e.control.value else "")

    def _on_input_submit(e: ft.ControlEvent):
        """On Enter, select the highlighted result."""
        if results_ref.current and results_ref.current.controls:
            idx = selected_index_ref[0]
            if idx < len(results_ref.current.controls):
                ctrl = results_ref.current.controls[idx]
                # Find the clickable container (skip section headers)
                if hasattr(ctrl, "content") and hasattr(ctrl, "on_click"):
                    handler = ctrl.on_click  # type: ignore[assignment]
                    if handler:
                        handler(None)

    def _on_key(e: ft.KeyboardEvent, parent_handler):
        """Handle keyboard navigation within the palette."""
        if e.key == "Arrow Down" or e.key == "Arrow Up":
            if not results_ref.current or not results_ref.current.controls:
                return
            # Find clickable items count
            clickable = [
                c for c in results_ref.current.controls
                if hasattr(c, "on_click") and c.on_click is not None
            ]
            total = len(clickable)
            if total == 0:
                return
            if e.key == "Arrow Down":
                selected_index_ref[0] = (selected_index_ref[0] + 1) % total
            else:
                selected_index_ref[0] = (selected_index_ref[0] - 1) % total

            # Re-render with new highlight
            query = input_ref.current.value if input_ref.current else ""
            _update_results(query)
        elif e.key == "Escape":
            on_close()
        elif parent_handler:
            # Pass through to the parent handler for non-navigation keys
            pass

    # ── Build the palette ───────────────────────────────────────────

    palette_card = ft.Container(
        width=520,
        bgcolor="#1A1A2E",
        border_radius=12,
        border=ft.Border.all(1, "#2D2D4A40"),
        padding=0,
        content=ft.Column(
            spacing=0,
            controls=[
                # Search input
                ft.Container(
                    padding=ft.Padding(16, 14, 16, 10),
                    border=ft.Border(bottom=ft.BorderSide(1, "#2D2D4A30")),
                    content=ft.TextField(
                        ref=input_ref,
                        hint_text="Search commands, tasks...",
                        border=ft.InputBorder.NONE,
                        autofocus=True,
                        text_size=16,
                        color="#E8E8F0",
                        hint_style=ft.TextStyle(color="#747496", size=16),
                        on_change=_on_input_change,
                        on_submit=_on_input_submit,
                    ),
                ),
                # Results list
                ft.Container(
                    height=340,
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
                            ft.Text("↑↓ Navigate", color="#5A5A80", size=10),
                            ft.Text("↵ Select", color="#5A5A80", size=10),
                            ft.Text("Esc Close", color="#5A5A80", size=10),
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

    return overlay
