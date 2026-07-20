"""Leadership OS — Flet Application.

Main application class that initializes all engines, sets up the theme,
manages app state transitions, and wires together the UI layer.

Complete Flet migration from KivyMD.
"""

from __future__ import annotations

import asyncio
import logging
import sys
from functools import partial
from pathlib import Path

import flet as ft

from leadership_os.ui.theme import Theme, build_flet_theme
from leadership_os.ui.widgets.top_bar import build_top_bar
from leadership_os.ui.widgets.sidebar import build_sidebar
from leadership_os.ui.widgets.execution_panel import build_execution_panel
from leadership_os.ui.widgets.status_bar import build_status_bar
from leadership_os.ui.widgets.task_card import build_task_card
from leadership_os.utils.path_utils import get_app_data_dir, ensure_directory, get_log_path
from leadership_os.utils.time_utils import format_duration, format_duration_short
from leadership_os.core.enums import TaskStatus

logger = logging.getLogger(__name__)


def setup_logging() -> None:
    """Configure logging for the application."""
    log_path = get_log_path()
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[
            logging.FileHandler(log_path),
            logging.StreamHandler(sys.stdout),
        ],
    )


class LeadershipOSApp:
    """Primary application class for Leadership OS (Flet).

    Manages:
    - App lifecycle (startup, build, on_stop)
    - Theme initialization
    - Engine initialization and wiring
    - App state transitions
    - UI building and periodic updates
    """

    def __init__(self) -> None:
        self.title = "Leadership OS"
        self._initialized = False

        # Core services (initialized in run)
        self.db = None
        self.config = None
        self.state = None
        self.event_bus = None

        # Engines (initialized in run)
        self.task_engine = None
        self.timer_engine = None
        self.break_engine = None
        self.journal_engine = None
        self.recovery_mgr = None

        # Runtime state
        self.page: ft.Page | None = None
        self._current_day = None
        self._active_task_id = None
        self._current_state = "startup"
        self._update_task = None  # For periodic update scheduling

        # UI References (updated during build)
        self._main_row = None  # ft.Row with [sidebar, center, panel]
        self._status_bar = None  # ft.Container for status bar

        # Center workspace refs (set during _build_center_workspace)
        self._date_label = ft.Ref[ft.Text]()
        self._focus_card = ft.Ref[ft.Container]()
        self._focus_title = ft.Ref[ft.Text]()
        self._focus_time = ft.Ref[ft.Text]()
        self._empty_state = ft.Ref[ft.Container]()
        self._section_pending = ft.Ref[ft.Container]()
        self._section_completed = ft.Ref[ft.Container]()
        self._task_list = ft.Ref[ft.Column]()
        self._completed_list = ft.Ref[ft.Column]()
        self._task_input = ft.Ref[ft.TextField]()

    # ─── Initialization ──────────────────────────────────────────────

    def _init_services(self) -> None:
        """Initialize database, config, state, and event bus."""
        app_dir = get_app_data_dir()
        ensure_directory(app_dir)
        logger.info("App data directory: %s", app_dir)

        from leadership_os.core.database import Database
        from leadership_os.config.config_manager import ConfigManager
        from leadership_os.core.state_manager import StateManager
        from leadership_os.core.event_bus import EventBus

        self.db = Database(app_dir / "leadership_os.db")
        self.db.initialize()
        logger.info("Database initialized")

        self.config = ConfigManager(app_dir / "config.toml")
        self.config.load()
        logger.info("Configuration loaded")

        self.state = StateManager(app_dir / "state.json")
        self.state.load()
        logger.info("State loaded")

        self.event_bus = EventBus()
        self.event_bus.subscribe("app_state_changed", self._on_app_state_changed)

    def _init_engines(self) -> None:
        """Initialize all business logic engines."""
        if not all([self.db, self.config, self.state, self.event_bus]):
            logger.error("Cannot initialize engines: core services not ready")
            return

        from leadership_os.core.task_engine import TaskEngine
        from leadership_os.core.timer_engine import TimerEngine
        from leadership_os.core.break_engine import BreakEngine
        from leadership_os.core.journal_engine import JournalEngine
        from leadership_os.core.recovery import RecoveryManager

        self.task_engine = TaskEngine(self.db, self.event_bus, self.state)
        self.timer_engine = TimerEngine(self.db, self.event_bus, self.state)
        self.break_engine = BreakEngine(self.db, self.event_bus, self.state, self.task_engine)
        self.journal_engine = JournalEngine(self.db, self.event_bus, self.config)
        self.recovery_mgr = RecoveryManager(self.db, self.state, self.event_bus)

        logger.info("All engines initialized")
        self._initialized = True

    def _run_startup(self) -> None:
        """Perform startup recovery and set the initial app state."""
        if not self.recovery_mgr:
            return

        recovery = self.recovery_mgr.check_recovery_needed()
        logger.info("Recovery check: needs_review=%s, state=%s",
                    recovery.needs_review, recovery.suggested_state)

        if recovery.needs_recovery:
            self.recovery_mgr.perform_recovery(recovery)

        self._current_state = recovery.suggested_state
        logger.info("Startup state: %s", self._current_state)

    # ─── Main Entry ─────────────────────────────────────────────────

    async def run(self, page: ft.Page) -> None:
        """Main async entry point — called by ft.app(target=...)."""
        self.page = page
        page.title = "Leadership OS"
        page.theme = build_flet_theme()
        page.theme_mode = ft.ThemeMode.DARK
        page.padding = 0
        page.bgcolor = "#0D0D1A"
        page.window.min_width = 900
        page.window.min_height = 600
        page.window.width = 1200
        page.window.height = 800

        # Initialize core services and engines
        self._init_services()
        self._init_engines()
        self._run_startup()

        # Build the UI
        self._build_ui()

        # Wire up the page
        page.update()

        # Populate initial data
        self._current_day = self.db.get_or_create_today()
        self._refresh_ui()

        # Start periodic update (1 second interval)
        try:
            while True:
                await asyncio.sleep(1.0)
                self._ui_tick()
                page.update()
        finally:
            self.on_stop()

    # ─── UI Building ─────────────────────────────────────────────────

    def _build_ui(self) -> None:
        """Build complete UI layout."""
        self.page.controls.clear()

        # Top bar
        top_bar = build_top_bar(
            on_search=self.show_search,
            on_settings=self.switch_to_settings,
            on_command_palette=self.show_command_palette,
        )

        # Main content row
        sidebar = build_sidebar(
            app_state=self._current_state,
            focus_time=0,
            completed_count=0,
            total_count=0,
            status_text="Ready",
            today_callback=self.switch_to_today,
            history_callback=self.switch_to_history,
            settings_callback=self.switch_to_settings,
        )

        center = self._build_center_workspace()

        panel = build_execution_panel(
            current_task_title="No active task",
            current_task_priority="",
            timer_display="00:00:00",
            timer_running=False,
            panel_state="idle",
            session_elapsed="00:00",
            session_estimated="--:--",
            completed_count=0,
            total_count=0,
            progress_status="No tasks yet",
            focus_time_display="0m",
            next_task_title="",
            on_pause=self._pause_active_task,
            on_complete=self._complete_active_task,
            on_start_break=self._start_break,
            on_resume=self._resume_from_break,
            on_end_break=self._end_break,
        )

        main_content = ft.Row(
            spacing=0,
            controls=[sidebar, center, panel],
            expand=True,
        )

        # Status bar
        status_bar = build_status_bar(
            focus_time_display="0m",
            completed_display="0",
        )

        # Store references for efficient updates
        self._main_row = main_content
        self._status_bar = status_bar

        self.page.add(
            ft.Column(
                spacing=0,
                controls=[top_bar, main_content, status_bar],
                expand=True,
            )
        )

    def _build_center_workspace(self) -> ft.Container:
        """Build the center workspace column with all sections."""
        # Empty state card (visible when no tasks)
        empty_state = ft.Container(
            ref=self._empty_state,
            height=196,
            bgcolor="#15152B",
            border_radius=10,
            border=ft.Border.all(1, "#2D2D4A20"),
            padding=ft.Padding(20, 16, 20, 16),
            content=ft.Column(
                spacing=0,
                controls=[
                    ft.Icon(ft.Icons.WB_SUNNY_OUTLINED, size=26, color="#9898B8"),
                    ft.Container(height=12),
                    ft.Text("Your workspace is clear", color="#9898B8", size=14, weight=ft.FontWeight.W_700),
                    ft.Container(height=6),
                    ft.Text(
                        "Add a task above to begin. Your focus timer and progress will appear here as you work.",
                        color="#747496", size=11, height=1.5,
                    ),
                    ft.Container(height=12),
                    ft.Text("Quick tips", color="#5A5A80", size=9, weight=ft.FontWeight.W_700),
                    ft.Container(height=4),
                    ft.Text("  •  Press Enter to add a task", color="#5A5A80", size=10),
                    ft.Text("  •  Click a task to start working on it", color="#5A5A80", size=10),
                ],
            ),
        )

        # Focus card (visible when task active)
        focus_card = ft.Container(
            ref=self._focus_card,
            height=0,
            opacity=0,
            visible=False,
            bgcolor="#1A1A2E",
            border_radius=10,
            padding=ft.Padding(14, 10, 14, 10),
            content=ft.Row(
                spacing=12,
                controls=[
                    # Accent bar
                    ft.Container(width=3, height=36, bgcolor="#4A6FA5", border_radius=1.5),
                    ft.Column(
                        spacing=2,
                        expand=True,
                        controls=[
                            ft.Text("CURRENT FOCUS", color="#9898B8", size=9, weight=ft.FontWeight.W_700),
                            ft.Text("", ref=self._focus_title, color="#E8E8F0", size=16, weight=ft.FontWeight.W_700),
                        ],
                    ),
                    ft.Text("00:00", ref=self._focus_time, color="#9898B8", size=16, weight=ft.FontWeight.W_700),
                ],
            ),
        )

        # Task input row
        task_input_row = ft.Row(
            spacing=0,
            controls=[
                ft.TextField(
                    ref=self._task_input,
                    hint_text="Write a task...",
                    width=320,
                    height=36,
                    border=ft.InputBorder.OUTLINE,
                    border_color="#2D2D4A6B",
                    focused_border_color="#4A6FA5",
                    bgcolor="#1A1A2E",
                    text_style=ft.TextStyle(color="#E8E8F0", size=13),
                    hint_style=ft.TextStyle(color="#747496", size=13),
                    dense=True,
                    on_submit=lambda _: self.on_task_submit(),
                ),
                ft.Container(
                    width=36,
                    height=36,
                    bgcolor="#4A6FA5",
                    border_radius=ft.BorderRadius(top_left=0, top_right=8, bottom_right=8, bottom_left=0),
                    alignment=ft.Alignment(0,0),
                    on_click=lambda _: self.on_task_submit(),
                    content=ft.Text("+", color="white", size=16, weight=ft.FontWeight.W_700),
                ),
            ],
        )

        # Task list scroll area
        task_list = ft.Column(
            ref=self._task_list,
            spacing=6,
            scroll=ft.ScrollMode.AUTO,
        )
        completed_list = ft.Column(
            ref=self._completed_list,
            spacing=4,
        )

        # Pending section header
        section_pending = ft.Container(
            ref=self._section_pending,
            height=20,
            opacity=0,
            visible=False,
            content=ft.Row(
                spacing=8,
                controls=[
                    ft.Text("TASKS", color="#9898B8", size=9, weight=ft.FontWeight.W_700),
                    ft.Divider(height=1, color="#2D2D4A15"),
                ],
            ),
        )

        # Completed section header
        section_completed = ft.Container(
            ref=self._section_completed,
            height=20,
            opacity=0,
            visible=False,
            content=ft.Row(
                spacing=8,
                controls=[
                    ft.Text("COMPLETED", color="#66A66B8C", size=9, weight=ft.FontWeight.W_700),
                    ft.Divider(height=1, color="#2D2D4A0D"),
                ],
            ),
        )

        return ft.Container(
            expand=True,
            bgcolor="#0D0D1A",
            padding=ft.Padding(24, 16, 24, 12),
            content=ft.Column(
                spacing=0,
                controls=[
                    # Date
                    ft.Text("Today, July 20", ref=self._date_label, color="#5A5A80", size=9),
                    ft.Container(height=4),
                    # Today's Plan heading
                    ft.Text("Today's Plan", color="#E8E8F0", size=18, weight=ft.FontWeight.W_700),
                    ft.Container(height=12),
                    # Task input
                    task_input_row,
                    ft.Container(height=8),
                    # Focus card
                    focus_card,
                    ft.Container(height=8),
                    # Empty state
                    empty_state,
                    # Section divider
                    ft.Container(height=8),
                    # Tasks header
                    section_pending,
                    # Task list
                    ft.Container(
                        expand=True,
                        content=ft.Column(
                            spacing=6,
                            controls=[task_list],
                            scroll=ft.ScrollMode.AUTO,
                        ),
                    ),
                    # Completed header
                    section_completed,
                    ft.Container(
                        content=completed_list,
                    ),
                ],
            ),
        )

    # ─── UI Updates (called every second) ────────────────────────────

    def _ui_tick(self) -> None:
        """Periodic UI update — refreshes timer, progress, and status."""
        if not self.page or not self._current_day:
            return

        try:
            day_id = self._current_day.id
            active_task_id = self.state.get_active_task_id() if self.state else None

            # Build updated sidebar state
            focus_time = 0
            if self.timer_engine:
                focus_time = self.timer_engine.get_day_focus_seconds(day_id)

            tasks = self.task_engine.get_tasks(day_id) if self.task_engine else []
            completed = sum(1 for t in tasks if t.status == TaskStatus.COMPLETED.value)
            total = len(tasks)

            # Determine status text
            if self._current_state in ("planning", "idle", "startup"):
                status_text = "Ready"
            elif self._current_state == "working":
                status_text = "Focusing"
            elif self._current_state == "break":
                status_text = "On Break"
            elif self._current_state == "review":
                status_text = "Reviewing"
            else:
                status_text = "Ready"

            # Rebuild sidebar (cleanest way in Flet for complex state)
            # In a production app, use individual controls refs for perf
            # For now, rebuild the entire three-column layout
            self._rebuild_main_view(day_id, active_task_id, focus_time, tasks, completed, total, status_text)

        except Exception as e:
            logger.debug("UI tick error: %s", e)

    def _rebuild_main_view(
        self, day_id: str, active_task_id: str | None,
        focus_time: int, tasks: list, completed: int, total: int,
        status_text: str,
    ) -> None:
        """Rebuild the main content area with fresh data.

        Uses stored references (self._main_row, refs) instead of fragile
        index-based lookups.
        """
        if not self.page or not self._main_row:
            return

        # ── Compute timer/panel state ────────────────────────────────
        elapsed = 0
        timer_running = False
        session_estimated = "--:--"
        if active_task_id:
            elapsed = self.timer_engine.get_elapsed(active_task_id)
            timer_running = self.timer_engine.is_timer_running(active_task_id)
            active_task = self.task_engine.get_task(active_task_id) if self.task_engine else None
            if active_task and active_task.estimated_minutes:
                session_estimated = format_duration_short(active_task.estimated_minutes * 60)

        timer_display = format_duration(elapsed)
        session_elapsed = format_duration_short(elapsed)
        focus_short = format_duration_short(focus_time)

        progress_status = "No tasks yet"
        if total > 0:
            progress_status = "All done!" if completed == total else f"{total - completed} remaining"

        current_title = "No active task"
        current_priority = ""
        panel_state = "working" if active_task_id else "idle"
        if self._current_state == "break":
            panel_state = "break"
        if active_task_id:
            task = self.task_engine.get_task(active_task_id)
            if task:
                current_title = task.title
                current_priority = task.priority.upper()

        pending = [t for t in tasks if t.status in (
            TaskStatus.PENDING.value, TaskStatus.ACTIVE.value, TaskStatus.PAUSED.value
        )]
        next_title = pending[0].title if pending else ""

        # ── Build new sidebar and panel ──────────────────────────────
        new_sidebar = build_sidebar(
            app_state=self._current_state,
            focus_time=focus_time,
            completed_count=completed,
            total_count=total,
            status_text=status_text,
            today_callback=self.switch_to_today,
            history_callback=self.switch_to_history,
            settings_callback=self.switch_to_settings,
        )
        new_panel = build_execution_panel(
            current_task_title=current_title,
            current_task_priority=current_priority,
            timer_display=timer_display,
            timer_running=timer_running,
            panel_state=panel_state,
            session_elapsed=session_elapsed,
            session_estimated=session_estimated,
            completed_count=completed,
            total_count=total,
            progress_status=progress_status,
            focus_time_display=focus_short,
            next_task_title=next_title,
            on_pause=self._pause_active_task,
            on_complete=self._complete_active_task,
            on_start_break=self._start_break,
            on_resume=self._resume_from_break,
            on_end_break=self._end_break,
        )

        # Replace sidebar (index 0) and panel (index 2) in the main row
        self._main_row.controls[0] = new_sidebar
        self._main_row.controls[2] = new_panel

        # ── Update center workspace via Refs ─────────────────────────
        has_tasks = total > 0
        has_completed = completed > 0

        # Empty state
        if self._empty_state.current:
            self._empty_state.current.visible = not has_tasks
            self._empty_state.current.opacity = 1 if not has_tasks else 0

        # Section headers
        if self._section_pending.current:
            self._section_pending.current.visible = has_tasks
        if self._section_completed.current:
            self._section_completed.current.visible = has_completed

        # Build task and completed cards
        task_cards = []
        completed_cards = []
        for task in tasks:
            is_active = task.id == active_task_id
            is_done = task.status == TaskStatus.COMPLETED.value
            card = build_task_card(
                task_id=task.id,
                title=task.title,
                priority=task.priority,
                status=task.status,
                is_active=is_active,
                is_completed=is_done,
                deadline=task.deadline or "",
                estimated_minutes=task.estimated_minutes or 0,
                actual_seconds=task.actual_seconds or 0,
                on_activate=partial(self._activate_task, task.id),
                on_complete=partial(self._complete_task_from_card, task.id),
                on_edit=partial(self._edit_task, task.id),
                on_delete=partial(self._delete_task, task.id),
            )
            if is_done:
                completed_cards.append(card)
            else:
                task_cards.append(card)

        # Update task lists via Ref
        if self._task_list.current:
            self._task_list.current.controls = task_cards
        if self._completed_list.current:
            self._completed_list.current.controls = completed_cards

        # ── Update status bar via Refs ───────────────────────────────
        if self._status_bar and self._status_bar.content:
            row = self._status_bar.content
            if isinstance(row, ft.Row):
                row.controls = [
                    ft.Text(f"Focus {focus_short}", color="#5A5A80", size=9),
                    ft.Text(f"Done {int(completed)}", color="#5A5A80", size=9),
                    ft.Container(expand=True),
                ]

        self.page.update()

    # ─── Refresh Full UI ─────────────────────────────────────────────

    def _refresh_ui(self) -> None:
        """Full refresh of UI data (used after task lifecycle events)."""
        if not self.page or not self._current_day:
            return

        day_id = self._current_day.id
        active_task_id = self.state.get_active_task_id() if self.state else None
        focus_time = self.timer_engine.get_day_focus_seconds(day_id) if self.timer_engine else 0
        tasks = self.task_engine.get_tasks(day_id) if self.task_engine else []
        completed = sum(1 for t in tasks if t.status == TaskStatus.COMPLETED.value)
        total = len(tasks)

        # Determine status text
        if self._current_state in ("planning", "idle", "startup"):
            status_text = "Ready"
        elif self._current_state == "working":
            status_text = "Focusing"
        elif self._current_state == "break":
            status_text = "On Break"
        elif self._current_state == "review":
            status_text = "Reviewing"
        else:
            status_text = "Ready"

        self._rebuild_main_view(day_id, active_task_id, focus_time, tasks, completed, total, status_text)

    # ─── Event Handler ───────────────────────────────────────────────

    def _on_app_state_changed(self, event: str, data: dict) -> None:
        """React to application state changes."""
        new_state = data.get("state", "")
        if new_state:
            self._current_state = new_state

    # ─── Task Lifecycle ───────────────────────────────────────────────

    def on_task_submit(self) -> None:
        """Called when user submits a new task title."""
        if not self.page or not self._current_day:
            return

        title_input = self._task_input.current
        if not title_input:
            return

        title = title_input.value.strip()
        if not title:
            return

        try:
            task = self.task_engine.create_task(
                day_id=self._current_day.id,
                title=title,
            )
            title_input.value = ""
            logger.info("Task created: %s (id=%s)", task.title, task.id)
            self._activate_task(task.id)
        except Exception as e:
            logger.error("Failed to create task: %s", e, exc_info=True)

    def _activate_task(self, task_id: str) -> None:
        """Activate a task — starts the timer."""
        if not self.task_engine:
            return
        try:
            task = self.task_engine.activate_task(task_id)
            self._active_task_id = task.id
            self._current_state = "working"
            self._sync_active_task(task)
            self._refresh_ui()
            logger.info("Activated task: %s", task.title)
        except Exception as e:
            logger.error("Failed to activate task: %s", e)

    def _complete_active_task(self) -> None:
        """Complete the currently active task."""
        active_id = self.state.get_active_task_id() if self.state else None
        if not active_id or not self.task_engine:
            return
        try:
            task = self.task_engine.complete_task(active_id)
            self._active_task_id = None
            self._sync_active_task(None)
            self._current_state = "planning"
            self._refresh_ui()
            logger.info("Completed task: %s", task.title)
        except Exception as e:
            logger.error("Failed to complete task: %s", e)

    def _pause_active_task(self) -> None:
        """Pause the currently active task."""
        active_id = self.state.get_active_task_id() if self.state else None
        if not active_id or not self.task_engine:
            return
        try:
            task = self.task_engine.pause_task(active_id)
            self._sync_active_task(None)
            self._current_state = "planning"
            self._refresh_ui()
            logger.info("Paused task: %s", task.title)
        except Exception as e:
            logger.error("Failed to pause task: %s", e)

    def _start_break(self) -> None:
        """Start a break — pauses active task."""
        if not self.break_engine or not self._current_day:
            return
        try:
            self.break_engine.start_break(day_id=self._current_day.id)
            self._current_state = "break"
            self._refresh_ui()
            logger.info("Break started")
        except Exception as e:
            logger.error("Failed to start break: %s", e)

    def _resume_from_break(self) -> None:
        """Resume work from break."""
        self._end_break()

    def _end_break(self) -> None:
        """End break — resumes the paused task."""
        if not self.break_engine or not self._current_day:
            return
        try:
            self.break_engine.end_break(day_id=self._current_day.id)
            active_id = self.state.get_active_task_id() if self.state else None
            if active_id:
                task = self.task_engine.get_task(active_id)
                self._sync_active_task(task)
                self._current_state = "working"
            else:
                self._current_state = "planning"
            self._refresh_ui()
            logger.info("Break ended")
        except Exception as e:
            logger.error("Failed to end break: %s", e)

    def _sync_active_task(self, task) -> None:
        """Update focus card UI for active task state."""
        # Handled by _rebuild_main_view during next tick
        pass

    def _complete_task_from_card(self, task_id: str) -> None:
        """Complete a task from the task card button."""
        if not self.task_engine:
            return
        try:
            was_active = (self.state.get_active_task_id() == task_id) if self.state else False
            self.task_engine.complete_task(task_id)
            if was_active:
                self._sync_active_task(None)
            self._refresh_ui()
            logger.info("Task completed from card: %s", task_id)
        except Exception as e:
            logger.error("Failed to complete task from card: %s", e)

    def _edit_task(self, task_id: str) -> None:
        """Placeholder for editing a task."""
        logger.info("Edit task: %s", task_id)

    def _delete_task(self, task_id: str) -> None:
        """Delete a task from the card."""
        if not self.task_engine:
            return
        try:
            was_active = (self.state.get_active_task_id() == task_id) if self.state else False
            self.task_engine.delete_task(task_id)
            if was_active:
                self._sync_active_task(None)
                self._current_state = "planning"
            self._refresh_ui()
            logger.info("Task deleted: %s", task_id)
        except Exception as e:
            logger.error("Failed to delete task: %s", e)

    # ─── Navigation Methods ───────────────────────────────────────────

    def switch_to_today(self) -> None:
        """Navigate to the Today/Planning view."""
        self._current_state = "planning"
        self._refresh_ui()
        logger.info("Navigated to Today")

    def switch_to_history(self) -> None:
        """Navigate to the History view."""
        logger.info("Navigated to History")

    def switch_to_settings(self) -> None:
        """Navigate to the Settings view."""
        logger.info("Navigated to Settings")

    def show_search(self) -> None:
        """Open the search dialog."""
        logger.info("Search requested")

    def show_command_palette(self) -> None:
        """Open the command palette."""
        logger.info("Command palette requested")

    # ─── Lifecycle ────────────────────────────────────────────────────

    def on_stop(self) -> None:
        """Save state on shutdown."""
        logger.info("Leadership OS shutting down")

        if self.state:
            self.state.set_needs_review(True)
            self.state.set_app_state(self._current_state)
            self.state.save()

        if self.db:
            self.db.close()

        logger.info("Leadership OS shutdown complete")



def main() -> None:
    """Main entry point for Leadership OS (Flet)."""
    setup_logging()
    _logger = logging.getLogger(__name__)
    _logger.info("Leadership OS starting...")

    try:
        app_instance = LeadershipOSApp()
        ft.app(target=app_instance.run)
    except Exception as e:
        _logger.error("Fatal error: %s", e, exc_info=True)
        print(f"\n❌ Fatal Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
