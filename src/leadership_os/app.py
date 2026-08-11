"""Leadership OS — Flet Application.

Main application class that initializes all engines, sets up the theme,
manages app state transitions, and wires together the UI layer.

Features:
- Complete Flet desktop UI (dark theme)
- System tray integration (pystray)
- Keyboard shortcuts (configurable)
- Command palette (Ctrl+K)
- Settings / History / Today navigation
- Single-instance lock
- Event-driven architecture via EventBus
"""

from __future__ import annotations

import asyncio
import logging
import sys
from datetime import datetime
from functools import partial
from typing import Any

import flet as ft

from leadership_os.core.enums import TaskStatus
from leadership_os.core.event_bus import CONFIG_CHANGED
from leadership_os.core.models import Reflection
from leadership_os.ui.theme import Theme, build_flet_theme
from leadership_os.ui.widgets.execution_panel import build_execution_panel
from leadership_os.ui.widgets.review_screen import build_review_screen
from leadership_os.ui.widgets.sidebar import build_sidebar
from leadership_os.ui.widgets.status_bar import build_status_bar
from leadership_os.ui.widgets.task_card import build_task_card
from leadership_os.ui.widgets.top_bar import build_top_bar
from leadership_os.utils.path_utils import (
    ensure_directory,
    get_app_data_dir,
    get_log_path,
)
from leadership_os.utils.time_utils import format_duration, format_duration_short

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
        self.search_engine = None

        # Runtime state
        self.page: ft.Page | None = None
        self._current_day = None
        self._active_task_id = None
        self._current_state = "startup"
        self._nav_view = "today"  # "today", "history", "settings", "carry_forward", "break_dialog"
        self._selected_task_index: int = -1  # For keyboard task navigation
        self._carry_forward_tasks: list = []  # Tasks to review on startup
        self._task_day_map: dict[str, str] = {}  # task_id -> day date for carry-forward

        # Tray & system
        self._tray = None
        self._shortcut_handler = None
        self._instance_lock = None
        self._overlay = None  # Floating overlay window (Phase 8)

        # UI References (updated during build)
        self._root_column = None  # ft.Column root of page
        self._main_row = None  # ft.Row with [sidebar, center, panel]
        self._status_bar = None  # ft.Container for status bar
        self._history_container = None  # Last-built history screen container
        self._center_ref = ft.Ref[ft.Container]()  # Ref to center workspace container
        self._overlay_ref = ft.Ref[ft.Container]()  # Ref to command palette overlay

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

        from leadership_os.config.config_manager import ConfigManager
        from leadership_os.core.database import Database
        from leadership_os.core.event_bus import EventBus
        from leadership_os.core.state_manager import StateManager

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

        from leadership_os.core.break_engine import BreakEngine
        from leadership_os.core.journal_engine import JournalEngine
        from leadership_os.core.recovery import RecoveryManager
        from leadership_os.core.task_engine import TaskEngine
        from leadership_os.core.timer_engine import TimerEngine

        self.task_engine = TaskEngine(self.db, self.event_bus, self.state)
        self.timer_engine = TimerEngine(self.db, self.event_bus, self.state)
        self.break_engine = BreakEngine(self.db, self.event_bus, self.state, self.task_engine)
        self.journal_engine = JournalEngine(self.db, self.event_bus, self.config)
        self.recovery_mgr = RecoveryManager(self.db, self.state, self.event_bus)

        from leadership_os.core.search_engine import SearchEngine
        self.search_engine = SearchEngine(self.db, self.config)

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

    def _enter_initial_view(self) -> None:
        """Enter the view appropriate for the recovered startup state."""
        if self._current_state == "review":
            self.switch_to_review()
        else:
            self.switch_to_today()

    # ─── Main Entry ─────────────────────────────────────────────────

    async def run(self, page: ft.Page) -> None:
        """Main async entry point — called by ft.app(target=...)."""
        self.page = page
        page.title = "Leadership OS"
        # Apply the active theme palette from config before building UI
        Theme.set_mode(self.config.get("ui", "theme", "light") if self.config else "light")
        page.theme = build_flet_theme()
        page.theme_mode = self._resolve_theme_mode()
        page.padding = 0
        page.bgcolor = Theme.PARCHMENT
        page.window.min_width = 900
        page.window.min_height = 600
        page.window.width = 1200
        page.window.height = 800

        # ── Single-instance lock ──────────────────────────────────
        app_dir = get_app_data_dir()
        ensure_directory(app_dir)
        from leadership_os.core.instance_lock import InstanceLock, InstanceLockError
        self._instance_lock = InstanceLock(app_dir)
        try:
            self._instance_lock.acquire()
        except InstanceLockError as e:
            logger.warning("Another instance is already running: %s", e)
            try:
                page.run_task(page.window.close)
            except Exception:
                page.window.close()
            return

        # Initialize core services and engines
        self._init_services()
        self._init_engines()
        self._run_startup()

        # ── Tray manager ──────────────────────────────────────────
        from leadership_os.tray.tray_manager import TrayManager
        self._tray = TrayManager(
            self.event_bus,
            on_show_window=self._on_tray_show_window,
            on_quit=self._on_tray_quit,
        )
        # Subscribe to tray command events
        self.event_bus.subscribe("cmd_pause_task", self._on_tray_pause)
        self.event_bus.subscribe("cmd_complete_task", self._on_tray_complete)
        self.event_bus.subscribe("cmd_start_break", self._on_tray_start_break)
        self.event_bus.subscribe("cmd_resume_task", self._on_tray_resume)
        self.event_bus.subscribe("cmd_end_break", self._on_tray_end_break)
        self.event_bus.subscribe(CONFIG_CHANGED, self._on_config_changed)
        self._tray.start()

        # ── Floating Overlay (Phase 8) ────────────────────────────
        show_overlay = self.config.get("ui", "show_overlay", True)
        if show_overlay:
            from leadership_os.ui.overlay import OverlayWindow
            self._overlay = OverlayWindow(
                on_show_main=self._on_tray_show_window,
                on_pause=self._pause_active_task,
                on_complete=self._complete_active_task,
                on_start_break=self._start_break,
                on_resume=self._resume_from_break,
                on_end_break=self._end_break,
                on_select_task=self._on_overlay_select_task,
                config=self.config.get_section("ui"),
            )
            self._overlay.start()
            logger.info("Floating overlay started")

        # ── Keyboard shortcuts ────────────────────────────────────
        from leadership_os.ui.shortcut_handler import ShortcutHandler
        action_map = {
            "create_task": self._on_shortcut_create_task,
            "complete_task": self._on_shortcut_complete_task,
            "pause_task": self._on_shortcut_pause_task,
            "start_break": self._on_shortcut_start_break,
            "end_break": self._on_shortcut_end_break,
            "end_day": self._on_shortcut_end_day,
            "command_palette": self._on_shortcut_command_palette,
            "settings": self._on_shortcut_settings,
            "escape": self._on_shortcut_escape,
        }
        # ── Keyboard ─── page.on_keyboard_event handles both shortcuts
        # and task list navigation (arrow keys). We wrap to check nav first.
        self._shortcut_handler = ShortcutHandler(self.config, action_map)
        shortcut_handle = self._shortcut_handler.handle

        def _combined_keyboard_handler(e: ft.KeyboardEvent) -> bool:
            # Command palette gets first dibs when visible (global search nav)
            if self._overlay_ref.current and self._overlay_ref.current.visible:
                palette_handler = getattr(
                    self._overlay_ref.current.content, "_lhos_handle_keyboard", None
                )
                if palette_handler and palette_handler(e):
                    return True
            # Check for task list navigation keys next
            if self._on_task_list_keyboard(e):
                return True
            # Then delegate to shortcut handler
            return shortcut_handle(e)

        page.on_keyboard_event = _combined_keyboard_handler

        # ── Prevent close → minimize to tray ──────────────────────
        minimize_to_tray = self.config.get("startup", "minimize_to_tray", True)
        if minimize_to_tray:
            page.window.prevent_close = True
            page.window.on_event = self._on_window_event

        # Build the UI
        self._build_ui()

        # Populate initial data
        self._current_day = self.db.get_or_create_today()
        self._refresh_ui()

        # Enter the view appropriate for the recovered startup state
        self._enter_initial_view()

        # Check for carry-forward tasks from previous days
        self._check_carry_forward()

        # Start periodic update via Flet's async task runner
        page.run_task(self._ui_tick_loop)
        page.update()

    # ─── UI Building ─────────────────────────────────────────────────

    def _build_top_bar(self) -> ft.Container:
        """Build the global nav bar with the current theme state."""
        return build_top_bar(
            on_search=self.show_search,
            on_settings=self.switch_to_settings,
            on_command_palette=self.show_command_palette,
            on_quit=self._on_quit,
            on_toggle_theme=self._on_toggle_theme,
            current_theme=Theme.mode(),
        )

    def _build_ui(self) -> None:
        """Build complete UI layout with Stack for overlay support."""
        self.page.controls.clear()

        # Top bar
        top_bar = self._build_top_bar()

        # Main content row
        sidebar = build_sidebar(
            app_state=self._current_state,
            focus_time=0,
            completed_count=0,
            total_count=0,
            status_text="Ready",
            active_view=self._nav_view,
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

        # Command palette overlay (hidden by default)
        command_overlay = ft.Container(
            ref=self._overlay_ref,
            visible=False,
        )

        # Store references
        self._main_row = main_content
        self._status_bar = status_bar

        app_column = ft.Column(
            spacing=0,
            controls=[top_bar, main_content, status_bar],
            expand=True,
        )

        self._root_column = app_column
        self.page.add(
            ft.Stack(
                controls=[app_column, command_overlay],
                expand=True,
            )
        )

    def _build_center_workspace(self) -> ft.Container:
        """Build the center workspace column with all sections."""
        # Empty state card (visible when no tasks)
        empty_state = ft.Container(
            ref=self._empty_state,
            height=196,
            bgcolor="#ffffff",
            border_radius=Theme.radius["lg"],
            border=ft.Border.all(1, Theme.HAIRLINE),
            padding=ft.Padding(20, 16, 20, 16),
            content=ft.Column(
                spacing=0,
                controls=[
                    ft.Icon(ft.Icons.WB_SUNNY_OUTLINED, size=26, color=Theme.GRAY_2),
                    ft.Container(height=12),
                    ft.Text("Your workspace is clear", color=Theme.INK, size=14, weight=ft.FontWeight.W_700),
                    ft.Container(height=6),
                    ft.Text(
                        "Add a task above to begin. Your focus timer and progress will appear here as you work.",
                        color=Theme.GRAY_3, size=11, height=1.5,
                    ),
                    ft.Container(height=12),
                    ft.Text("Quick tips", color=Theme.GRAY_3, size=9, weight=ft.FontWeight.W_700),
                    ft.Container(height=4),
                    ft.Text("  •  Press Enter to add a task", color=Theme.GRAY_3, size=10),
                    ft.Text("  •  Click a task to start working on it", color=Theme.GRAY_3, size=10),
                ],
            ),
        )

        # Focus card (visible when task active)
        focus_card = ft.Container(
            ref=self._focus_card,
            height=0,
            opacity=0,
            visible=False,
            bgcolor="#ffffff",
            border_radius=Theme.radius["lg"],
            border=ft.Border.all(1, Theme.HAIRLINE),
            padding=ft.Padding(14, 10, 14, 10),
            content=ft.Row(
                spacing=12,
                controls=[
                    # Accent bar
                    ft.Container(width=3, height=36, bgcolor=Theme.PRIMARY, border_radius=1.5),
                    ft.Column(
                        spacing=2,
                        expand=True,
                        controls=[
                            ft.Text("CURRENT FOCUS", color=Theme.GRAY_3, size=9, weight=ft.FontWeight.W_700),
                            ft.Text("", ref=self._focus_title, color=Theme.INK, size=16, weight=ft.FontWeight.W_700),
                        ],
                    ),
                    ft.Text("00:00", ref=self._focus_time, color=Theme.GRAY_3, size=16, weight=ft.FontWeight.W_700),
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
                    border_color=Theme.HAIRLINE,
                    focused_border_color=Theme.PRIMARY,
                    bgcolor="#ffffff",
                    text_style=ft.TextStyle(color=Theme.INK, size=13),
                    hint_style=ft.TextStyle(color=Theme.GRAY_3, size=13),
                    dense=True,
                    on_submit=lambda _: self.on_task_submit(),
                ),
                ft.Container(
                    width=36,
                    height=36,
                    bgcolor=Theme.PRIMARY,
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
                    ft.Text("TASKS", color=Theme.GRAY_2, size=9, weight=ft.FontWeight.W_700),
                    ft.Divider(height=1, color="#f0f0f0"),
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
                    ft.Text("COMPLETED", color=Theme.color("success"), size=9, weight=ft.FontWeight.W_700, opacity=0.55),
                    ft.Divider(height=1, color="#f0f0f0"),
                ],
            ),
        )

        return ft.Container(
            expand=True,
            bgcolor=Theme.PARCHMENT,
            padding=ft.Padding(24, 16, 24, 12),
            content=ft.Column(
                spacing=0,
                controls=[
                    # Date
                    ft.Text("Today, July 20", ref=self._date_label, color=Theme.GRAY_3, size=9),
                    ft.Container(height=4),
                    # Today's Plan heading + End Day action
                    ft.Row(
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        controls=[
                            ft.Text("Today's Plan", color=Theme.INK, size=18, weight=ft.FontWeight.W_700),
                            ft.Container(expand=True),
                            ft.TextButton(
                                content=ft.Row(
                                    spacing=6,
                                    controls=[
                                        ft.Icon(ft.Icons.EDIT_CALENDAR, size=16, color=Theme.PRIMARY),
                                        ft.Text("End Day", color=Theme.PRIMARY, size=12, weight=ft.FontWeight.W_600),
                                    ],
                                ),
                                on_click=lambda _: self.switch_to_review(),
                                style=ft.ButtonStyle(
                                    bgcolor="#0066cc14",
                                    shape=ft.RoundedRectangleBorder(radius=Theme.radius["pill"]),
                                    padding=ft.Padding(12, 6, 12, 6),
                                ),
                            ),
                        ],
                    ),
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

    # ─── UI Tick Loop (async, uses page.run_task) ──────────────────

    async def _ui_tick_loop(self) -> None:
        """Async loop that periodically refreshes the UI (runs via page.run_task).

        Replaces the old `while True: await asyncio.sleep(1.0)` pattern with
        Flet's proper async task mechanism. Runs every second.
        """
        try:
            while True:
                await asyncio.sleep(1.0)
                if not self.page or not self._current_day:
                    continue
                try:
                    self._ui_tick()
                    self.page.update()
                except Exception as e:
                    logger.debug("UI tick error: %s", e)
        except asyncio.CancelledError:
            logger.debug("UI tick loop cancelled")
        finally:
            self.on_stop()

    def _ui_tick(self) -> None:
        """Periodic UI update — refreshes timer, progress, and status."""
        if not self.page or not self._current_day:
            return

        day_id = self._current_day.id
        active_task_id = self.state.get_active_task_id() if self.state else None

        focus_time = 0
        if self.timer_engine:
            focus_time = self.timer_engine.get_day_focus_seconds(day_id)

        tasks = self.task_engine.get_tasks(day_id) if self.task_engine else []
        completed = sum(1 for t in tasks if t.status == TaskStatus.COMPLETED.value)
        total = len(tasks)

        # Determine status text
        status_text = self._get_status_text()

        # Update tray progress
        if self._tray:
            focus_label = format_duration_short(focus_time)
            self._tray.update_progress(focus_label, completed, total)

        # Update floating overlay (Phase 8)
        if self._overlay:
            active_id = self.state.get_active_task_id() if self.state else None
            current_task = self.task_engine.get_task(active_id) if active_id and self.task_engine else None
            overlay_data = {
                "task": current_task.title if current_task else "",
                "timer": format_duration(
                    self.timer_engine.get_elapsed(active_id) if self.timer_engine and active_id else 0
                ),
                "state": "working" if active_id else ("break" if self._current_state == "break" else "idle"),
                "state_label": self._get_status_text(),
                "priority": current_task.priority.upper() if current_task else "",
                "next_task": (tasks[0].title if tasks else "") if not active_id else (
                    (tasks[1].title if len(tasks) > 1 else "") if current_task else ""
                ),
            }
            # Compute proper next task + pending task list for the overlay
            pending = [t for t in tasks if t.status not in (
                TaskStatus.COMPLETED.value, TaskStatus.ARCHIVED.value, TaskStatus.DELETED.value
            ) and t.id != active_id]
            overlay_data["next_task"] = pending[0].title if pending else ""
            overlay_data["pending_tasks"] = [
                {"id": t.id, "title": t.title} for t in pending[:4]
            ]
            self._overlay.send_update(overlay_data)

        # Only rebuild main view when on today view
        if self._nav_view == "today":
            self._rebuild_main_view(day_id, active_task_id, focus_time, tasks, completed, total, status_text)

    def _get_status_text(self) -> str:
        """Get human-readable status based on current app state."""
        if self._current_state in ("planning", "idle", "startup"):
            return "Ready"
        elif self._current_state == "working":
            return "Focusing"
        elif self._current_state == "break":
            return "On Break"
        elif self._current_state == "review":
            return "Reviewing"
        return "Ready"

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

        # Compute break info (Phase 6)
        break_type_label = ""
        break_elapsed = ""
        if self._current_state == "break" and self.break_engine and self._current_day:
            active_break = self.break_engine.get_active_break(self._current_day.id)
            if active_break:
                break_type_label = active_break.break_type.title()
                # Calculate elapsed time for this break
                try:
                    start = datetime.fromisoformat(active_break.start_time)
                    break_seconds = int((datetime.now() - start).total_seconds())
                    break_elapsed = format_duration_short(max(0, break_seconds))
                except (ValueError, OSError):
                    break_elapsed = format_duration_short(0)

        # Build new sidebar and panel
        new_sidebar = build_sidebar(
            app_state=self._current_state,
            focus_time=focus_time,
            completed_count=completed,
            total_count=total,
            status_text=status_text,
            active_view=self._nav_view,
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
            break_type_label=break_type_label,
            break_elapsed=break_elapsed,
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

        # Build task and completed cards with keyboard selection support
        task_cards = []
        completed_cards = []
        pending_for_nav = [t for t in tasks if t.status not in (TaskStatus.COMPLETED.value, TaskStatus.ARCHIVED.value, TaskStatus.DELETED.value)]
        # Compute the selected task ID (if any) from the pending list
        selected_id = None
        if 0 <= self._selected_task_index < len(pending_for_nav):
            selected_id = pending_for_nav[self._selected_task_index].id
        for task in tasks:
            is_active = task.id == active_task_id
            is_done = task.status == TaskStatus.COMPLETED.value
            is_selected = (task.id == selected_id)
            card = build_task_card(
                task_id=task.id,
                title=task.title,
                priority=task.priority,
                status=task.status,
                is_active=is_active,
                is_completed=is_done,
                is_selected=is_selected,
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
                    ft.Text(f"Focus {focus_short}", color=Theme.GRAY_3, size=9),
                    ft.Text(f"Done {int(completed)}", color=Theme.GRAY_3, size=9),
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

    def _refresh_sidebar(self) -> None:
        """Rebuild just the sidebar so the active nav highlight tracks the
        current view (Today / History / Settings)."""
        if not self._main_row or not self._current_day:
            return
        day_id = self._current_day.id
        focus_time = self.timer_engine.get_day_focus_seconds(day_id) if self.timer_engine else 0
        tasks = self.task_engine.get_tasks(day_id) if self.task_engine else []
        completed = sum(1 for t in tasks if t.status == TaskStatus.COMPLETED.value)
        total = len(tasks)
        new_sidebar = build_sidebar(
            app_state=self._current_state,
            focus_time=focus_time,
            completed_count=completed,
            total_count=total,
            status_text=self._get_status_text(),
            active_view=self._nav_view,
            today_callback=self.switch_to_today,
            history_callback=self.switch_to_history,
            settings_callback=self.switch_to_settings,
        )
        self._main_row.controls[0] = new_sidebar

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
            # Task is created as pending — user must click Start to activate it
            self._refresh_ui()
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
        """Show break type selection dialog, then start the break."""
        if not self.break_engine or not self._current_day:
            return
        self._show_break_type_dialog()

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
        self._nav_view = "today"
        self._current_state = "planning"
        self._selected_task_index = -1
        self._show_today_workspace()
        self._refresh_ui()
        logger.info("Navigated to Today")

    def switch_to_history(self) -> None:
        """Navigate to the History view."""
        self._nav_view = "history"
        self._show_history_workspace()
        self._refresh_sidebar()
        if self.page:
            self.page.update()
        logger.info("Navigated to History")

    def switch_to_settings(self) -> None:
        """Navigate to the Settings view."""
        self._nav_view = "settings"
        self._show_settings_workspace()
        self._refresh_sidebar()
        if self.page:
            self.page.update()
        logger.info("Navigated to Settings")

    def switch_to_review(self) -> None:
        """Navigate to the End-of-Day Review view."""
        self._nav_view = "review"
        self._current_state = "review"
        self._show_review_workspace()
        self._refresh_sidebar()
        if self.page:
            self.page.update()
        logger.info("Navigated to End-of-Day Review")

    def _show_today_workspace(self) -> None:
        """Replace center workspace with the Today task list."""
        if self._main_row:
            center = self._build_center_workspace()
            self._main_row.controls[1] = center
            # Don't call page.update() here — _refresh_ui() handles it

    def _show_history_workspace(self) -> None:
        """Replace center workspace with the History screen."""
        if not self._main_row or not self.db:
            return
        from leadership_os.ui.widgets.history_screen import (
            build_history_screen,
            init_history_list,
        )
        history = build_history_screen(self.db, on_close=self.switch_to_today)
        self._history_container = history
        self._main_row.controls[1] = history
        if self.page:
            self.page.update()
            # Trigger day list load after render
            init_history_list(self.db, history)

    def _show_settings_workspace(self) -> None:
        """Replace center workspace with the Settings screen."""
        if not self._main_row or not self.config:
            return
        from leadership_os.ui.widgets.settings_screen import build_settings_screen
        settings = build_settings_screen(
            self.config,
            self.event_bus,
            on_close=self.switch_to_today,
            page=self.page,
        )
        self._main_row.controls[1] = settings
        if self.page:
            self.page.update()

    def _show_review_workspace(self) -> None:
        """Replace center workspace with the End-of-Day Review screen."""
        if not self._main_row or not self.db or not self._current_day:
            return
        day_id = self._current_day.id
        tasks = self.task_engine.get_tasks(day_id) if self.task_engine else []
        completed = sum(1 for t in tasks if t.status == TaskStatus.COMPLETED.value)
        total = len(tasks)
        focus_seconds = self.timer_engine.get_day_focus_seconds(day_id) if self.timer_engine else 0
        break_seconds = self.db.calculate_day_break_seconds(day_id) if self.db else 0
        session_count = self.db.get_session_count(day_id) if self.db else 0

        # Pending tasks for tomorrow preview
        tomorrow_tasks = [t.title for t in tasks if t.status in (
            TaskStatus.PENDING.value, TaskStatus.ACTIVE.value, TaskStatus.PAUSED.value
        )]

        # Pre-fill any existing reflection
        existing = self.db.get_reflection(day_id)
        initial = {
            "accomplishments": existing.accomplishments if existing else "",
            "challenges": existing.challenges if existing else "",
            "tomorrow_first": existing.tomorrow_first if existing else "",
            "additional_notes": existing.additional_notes if existing else "",
        } if existing else {}

        review = build_review_screen(
            focus_seconds=focus_seconds,
            completed_count=completed,
            total_count=total,
            session_count=session_count,
            break_seconds=break_seconds,
            tomorrow_tasks=tomorrow_tasks,
            initial_accomplishments=initial.get("accomplishments", ""),
            initial_challenges=initial.get("challenges", ""),
            initial_tomorrow_first=initial.get("tomorrow_first", ""),
            initial_notes=initial.get("additional_notes", ""),
            on_finalize=self._handle_review_finalize,
            on_skip=self._handle_review_skip,
            on_cancel=self.switch_to_today,
        )
        self._main_row.controls[1] = review
        if self.page:
            self.page.update()

    def show_search(self) -> None:
        """Open search (shows command palette focused on task search)."""
        self.show_command_palette()

    def show_command_palette(self) -> None:
        """Show the command palette overlay."""
        if not self.page or not self._overlay_ref.current:
            return
        from leadership_os.ui.widgets.command_palette import build_command_palette
        palette = build_command_palette(
            self.task_engine,
            on_search_task=self._on_palette_task_selected,
            on_run_command=self._on_palette_command,
            on_close=self._hide_command_palette,
            search_engine=self.search_engine,
            on_open_day=self._on_palette_open_day,
        )
        # Replace overlay content
        parent = self._overlay_ref.current
        parent.content = palette
        parent.visible = True
        self.page.update()

    def _hide_command_palette(self) -> None:
        """Hide the command palette overlay."""
        if self._overlay_ref.current:
            self._overlay_ref.current.visible = False
            if self.page:
                self.page.update()

    def _resolve_theme_mode(self) -> ft.ThemeMode:
        """Resolve the configured theme to a Flet ThemeMode.

        The design system is light-first (Apple style); the setting is
        honored when present, defaulting to light.
        """
        theme_name = (self.config.get("ui", "theme", "light") if self.config else "light").lower()
        if theme_name == "dark":
            return ft.ThemeMode.DARK
        if theme_name == "system":
            return ft.ThemeMode.SYSTEM
        return ft.ThemeMode.LIGHT

    # ─── Tray & Window Event Handlers ───────────────────────────────

    def _on_quit(self) -> None:
        """Quit the app from the in-app Quit button.

        Unlike the window close (X), which minimizes to tray, this fully
        exits the application: disables prevent_close and closes the window,
        letting on_stop run its normal shutdown sequence.
        """
        logger.info("Quit requested from UI")
        self._on_tray_quit()

    def _on_window_event(self, e: ft.WindowEvent) -> None:
        """Handle native window events (Flet 0.86).

        When the close button (X) is clicked with minimize_to_tray enabled,
        the OS close request is intercepted (prevent_close) and reported here
        as WindowEventType.CLOSE — we hide the window to tray instead of
        quitting. The tray's quit action disables prevent_close before
        requesting close, so that path still exits the app.
        """
        if (
            e.type == ft.WindowEventType.CLOSE
            and self.page
            and self.page.window
            and self.page.window.prevent_close
        ):
            logger.info("Window close requested — minimizing to tray")
            self.page.window.visible = False
            self.page.update()

    def _on_tray_show_window(self) -> None:
        """Show the main window (called from tray or overlay)."""
        if self.page and self.page.window:
            # Flet 0.86: no window.show() — use the visible property + update.
            self.page.window.visible = True
            self.page.update()
            # Bring to front (async in Flet 0.86)
            try:
                self.page.run_task(self.page.window.to_front)
            except Exception as e:
                logger.debug("Could not bring window to front: %s", e)
            # Refresh UI to show current state
            self.switch_to_today()

    def _on_tray_quit(self) -> None:
        """Quit the app (called from tray)."""
        if self.page and self.page.window:
            # Allow close: disable prevent_close so window actually closes
            self.page.window.prevent_close = False
            # close() is async in Flet 0.86 — must be awaited via run_task.
            try:
                self.page.run_task(self.page.window.close)
            except Exception as e:
                logger.warning("Error closing window: %s", e)

    def _on_tray_pause(self, event: str, data: dict[str, Any]) -> None:
        self._pause_active_task()

    def _on_tray_complete(self, event: str, data: dict[str, Any]) -> None:
        self._complete_active_task()

    def _on_tray_start_break(self, event: str, data: dict[str, Any]) -> None:
        self._start_break()

    def _on_tray_resume(self, event: str, data: dict[str, Any]) -> None:
        self._resume_from_break()

    def _on_tray_end_break(self, event: str, data: dict[str, Any]) -> None:
        self._end_break()

    def _on_overlay_select_task(self, task_id: str) -> None:
        """Start a pending task selected from the floating overlay."""
        logger.info("Overlay task selected: %s", task_id)
        try:
            self._activate_task(task_id)
        except Exception as e:
            logger.error("Failed to start task from overlay: %s", e)

    def _on_config_changed(self, event: str, data: dict[str, Any]) -> None:
        """Reload shortcuts and apply theme when config changes."""
        if self._shortcut_handler:
            self._shortcut_handler.reload_shortcuts()
        self._apply_theme()
        logger.info("Configuration change detected, shortcuts + theme reloaded")

    def _on_toggle_theme(self) -> None:
        """Toggle between light and dark theme from the top bar.

        Persists the new mode to config (so it survives restarts and the
        Settings dropdown stays in sync), then re-applies the theme.
        """
        if not self.config:
            return
        current = (self.config.get("ui", "theme", "light") or "light").lower()
        new_theme = "dark" if current != "dark" else "light"
        self.config.set("ui", "theme", new_theme)
        self.config.save()
        logger.info("Theme toggled to %s from top bar", new_theme)
        if self.event_bus:
            self.event_bus.emit(CONFIG_CHANGED, {"source": "top_bar"})
        else:
            self._on_config_changed(CONFIG_CHANGED, {"source": "top_bar"})

    def _apply_theme(self) -> None:
        """Apply the configured theme (light/dark) and rebuild the UI so all
        widget colors re-resolve from the active palette."""
        if not self.page:
            return
        theme_name = (self.config.get("ui", "theme", "light") if self.config else "light").lower()
        Theme.set_mode(theme_name)
        self.page.theme = build_flet_theme()
        self.page.theme_mode = self._resolve_theme_mode()
        self.page.bgcolor = Theme.PARCHMENT

        # Rebuild the top bar so the toggle icon + nav colors re-resolve.
        if self._root_column:
            self._root_column.controls[0] = self._build_top_bar()

        # Rebuild the correct center workspace for the current view with the
        # new palette, then refresh chrome (sidebar + panel) and populate data.
        view = self._nav_view
        if view == "history":
            self._show_history_workspace()
        elif view == "settings":
            self._show_settings_workspace()
        elif view == "review":
            self._show_review_workspace()
        elif view == "carry_forward":
            self._show_carry_forward_workspace()
        elif view == "break_dialog":
            self._show_break_type_dialog()
        else:
            # Today (and today-context views) — rebuild the center container
            # so its build-time colors re-resolve, then repopulate the refs.
            self._show_today_workspace()
            self._refresh_ui()
        self._refresh_sidebar()
        if self.page:
            self.page.update()

    # ─── Palette Callbacks ──────────────────────────────────────────

    def _on_palette_task_selected(self, task_id: str) -> None:
        """A task was selected in the command palette."""
        self.switch_to_today()
        self._activate_task(task_id)

    def _on_palette_open_day(self, day_id: str) -> None:
        """Open a journal/session result — navigate to History and select the day."""
        self.switch_to_history()

        async def _select() -> None:
            history = getattr(self, "_history_container", None)
            select_day = getattr(history, "_lhos_select_day", None)
            if select_day is not None:
                try:
                    select_day(day_id)
                except Exception as e:
                    logger.debug("Could not select day %s in history: %s", day_id, e)

        if self.page:
            self.page.run_task(_select)

    def _on_palette_command(self, command: str) -> None:
        """A command was selected in the command palette."""
        cmd_map: dict[str, Any] = {
            "pause_task": self._pause_active_task,
            "complete_task": self._complete_active_task,
            "start_break": self._start_break,
            "end_break": self._end_break,
            "end_day": self._on_shortcut_end_day,
            "goto_today": self.switch_to_today,
            "goto_history": self.switch_to_history,
            "goto_settings": self.switch_to_settings,
            "search": self.show_command_palette,
        }
        action = cmd_map.get(command)
        if action:
            action()

    # ─── Shortcut Callbacks ─────────────────────────────────────────

    def _on_shortcut_create_task(self) -> None:
        if self._task_input.current:
            self._task_input.current.focus()

    def _on_shortcut_complete_task(self) -> None:
        self._complete_active_task()

    def _on_shortcut_pause_task(self) -> None:
        self._pause_active_task()

    def _on_shortcut_start_break(self) -> None:
        self._start_break()

    def _on_shortcut_end_break(self) -> None:
        self._end_break()

    def _on_shortcut_end_day(self) -> None:
        """Open the End-of-Day Review screen."""
        self.switch_to_review()

    def _handle_review_finalize(self, data: dict[str, str]) -> None:
        """Save reflection, generate journal, and end the day."""
        if not self._current_day or not self.db or not self.journal_engine:
            return

        day_id = self._current_day.id
        reflection = Reflection(
            day_id=day_id,
            accomplishments=data.get("accomplishments", ""),
            challenges=data.get("challenges", ""),
            tomorrow_first=data.get("tomorrow_first", ""),
            additional_notes=data.get("additional_notes", ""),
        )

        # Persist reflection
        try:
            self.db.save_reflection(reflection)
        except Exception as e:
            logger.error("Failed to save reflection: %s", e, exc_info=True)
            if self.page:
                self.page.snack_bar = ft.SnackBar(
                    content=ft.Text("Failed to save reflection.", color="white", size=13),
                    bgcolor=Theme.color("error"),
                    duration=3000,
                )
                self.page.snack_bar.open = True
                self.page.update()
            return

        # Generate journal
        try:
            summary = self.journal_engine.generate_journal(day_id)
        except Exception as e:
            logger.error("Failed to generate journal: %s", e, exc_info=True)
            if self.page:
                self.page.snack_bar = ft.SnackBar(
                    content=ft.Text("Failed to generate journal.", color="white", size=13),
                    bgcolor=Theme.color("error"),
                    duration=3000,
                )
                self.page.snack_bar.open = True
                self.page.update()
            return

        # Mark day complete
        try:
            self.db.end_day(self._current_day)
        except Exception as e:
            logger.error("Failed to end day: %s", e, exc_info=True)
            if self.page:
                self.page.snack_bar = ft.SnackBar(
                    content=ft.Text("Failed to close the day.", color="white", size=13),
                    bgcolor=Theme.color("error"),
                    duration=3000,
                )
                self.page.snack_bar.open = True
                self.page.update()
            return

        if self.state:
            self.state.set_needs_review(False)

        # Show a brief snackbar with the absolute journal path
        if self.page:
            journal_path = str(get_app_data_dir() / summary.journal_rel_path)
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text(f"Journal saved: {journal_path}", color="white", size=13),
                bgcolor=Theme.color("success"),
                duration=3000,
            )
            self.page.snack_bar.open = True
            self.page.update()

        # Create a fresh day and return to today view
        self._current_day = self.db.get_or_create_today()
        self.switch_to_today()
        logger.info("End-of-day review finalized for %s", day_id)

    def _handle_review_skip(self) -> None:
        """Skip reflection but still end the day and generate a journal."""
        self._handle_review_finalize({
            "accomplishments": "",
            "challenges": "",
            "tomorrow_first": "",
            "additional_notes": "",
        })

    def _on_shortcut_command_palette(self) -> None:
        self.show_command_palette()

    def _on_shortcut_settings(self) -> None:
        self.switch_to_settings()

    def _on_shortcut_escape(self) -> None:
        self._hide_command_palette()

    # ─── Carry Forward (Phase 4) ────────────────────────────────────

    def _check_carry_forward(self) -> None:
        """Check for unfinished tasks from previous days and show dialog if needed."""
        if not self.db or not self._current_day:
            return

        # Get previous days that have incomplete tasks
        previous_days = self.db.get_previous_days(limit=5)
        incomplete: list = []
        day_map: dict[str, str] = {}
        for prev_day in previous_days:
            if prev_day.id == self._current_day.id:
                continue
            tasks = self.db.get_tasks_by_day(prev_day.id)
            for t in tasks:
                if t.status in (TaskStatus.PENDING.value, TaskStatus.ACTIVE.value, TaskStatus.PAUSED.value, TaskStatus.CARRIED_FORWARD.value):
                    incomplete.append(t)
                    day_map[t.id] = prev_day.date

        if incomplete:
            self._carry_forward_tasks = incomplete
            self._task_day_map = day_map
            self._show_carry_forward_workspace()
        else:
            self._carry_forward_tasks = []
            self._task_day_map = {}

    def _show_carry_forward_workspace(self) -> None:
        """Replace center workspace with the carry-forward review screen."""
        if not self._main_row:
            return
        from leadership_os.ui.widgets.carry_forward_dialog import (
            build_carry_forward_dialog,
        )

        dialog = build_carry_forward_dialog(
            tasks=self._carry_forward_tasks,
            task_day_map=self._task_day_map,
            on_continue=self._on_carry_continue,
            on_archive=self._on_carry_archive,
            on_delete=self._on_carry_delete,
            on_done=self._on_carry_done,
        )
        self._nav_view = "carry_forward"
        self._main_row.controls[1] = dialog
        if self.page:
            self.page.update()

    def _on_carry_continue(self, task_id: str) -> None:
        """Carry a task forward into today's plan using the engine."""
        if not self.task_engine or not self._current_day:
            return
        try:
            task = self.task_engine.get_task(task_id)
            if task:
                # Use the engine's carry_forward_tasks method
                self.task_engine.carry_forward_tasks(task.day_id, self._current_day.id)
            # Remove from local list and refresh
            self._carry_forward_tasks = [t for t in self._carry_forward_tasks if t.id != task_id]
            if not self._carry_forward_tasks:
                self._on_carry_done()
            else:
                self._show_carry_forward_workspace()
        except Exception as e:
            logger.error("Failed to carry forward task: %s", e)

    def _on_carry_archive(self, task_id: str) -> None:
        """Archive a task instead of carrying it forward."""
        try:
            if self.task_engine:
                self.task_engine.archive_task(task_id)
            self._carry_forward_tasks = [t for t in self._carry_forward_tasks if t.id != task_id]
            if not self._carry_forward_tasks:
                self._on_carry_done()
            else:
                self._show_carry_forward_workspace()
        except Exception as e:
            logger.error("Failed to archive task: %s", e)

    def _on_carry_delete(self, task_id: str) -> None:
        """Delete a task permanently."""
        try:
            if self.task_engine:
                self.task_engine.delete_task(task_id)
            self._carry_forward_tasks = [t for t in self._carry_forward_tasks if t.id != task_id]
            if not self._carry_forward_tasks:
                self._on_carry_done()
            else:
                self._show_carry_forward_workspace()
        except Exception as e:
            logger.error("Failed to delete task: %s", e)

    def _on_carry_done(self) -> None:
        """Carry-forward review complete — switch to today view."""
        self._carry_forward_tasks = []
        self._task_day_map = {}
        self.switch_to_today()

    # ─── Break Dialog (Phase 6) ──────────────────────────────────────

    def _show_break_type_dialog(self) -> None:
        """Show break type selection dialog in center workspace."""
        if not self._main_row:
            return
        from leadership_os.ui.widgets.break_dialog import build_break_dialog

        dialog = build_break_dialog(
            on_confirm=self._on_break_confirm,
            on_cancel=self._on_break_cancel,
        )
        self._nav_view = "break_dialog"
        self._main_row.controls[1] = dialog
        if self.page:
            self.page.update()

    def _on_break_confirm(self, break_type: str, notes: str) -> None:
        """User confirmed break type — start the break."""
        if not self.break_engine or not self._current_day:
            return
        try:
            self.break_engine.start_break(
                day_id=self._current_day.id,
                break_type=break_type,
                notes=notes,
            )
            self._current_state = "break"
            self._show_today_workspace()
            self._refresh_ui()
            logger.info("Break started: %s", break_type)
        except Exception as e:
            logger.error("Failed to start break: %s", e)
            self._show_today_workspace()

    def _on_break_cancel(self) -> None:
        """User cancelled break dialog."""
        self._show_today_workspace()
        self._refresh_ui()

    # ─── Keyboard Task Navigation (Phase 5) ──────────────────────────

    def _on_task_list_keyboard(self, e: ft.KeyboardEvent) -> bool:
        """Handle arrow key navigation in the task list.

        Returns True if the event was handled.
        """
        if self._nav_view != "today":
            return False

        if not self._current_day:
            return False

        tasks = self.task_engine.get_tasks(self._current_day.id) if self.task_engine else []
        pending = [t for t in tasks if t.status not in (TaskStatus.COMPLETED.value, TaskStatus.ARCHIVED.value, TaskStatus.DELETED.value)]

        if not pending:
            return False

        # Ctrl+Up / Ctrl+Down: reorder
        if e.ctrl and e.key in ("Arrow Up", "Arrow Down"):
            if 0 <= self._selected_task_index < len(pending):
                if e.key == "Arrow Up" and self._selected_task_index > 0:
                    pending[self._selected_task_index], pending[self._selected_task_index - 1] = \
                        pending[self._selected_task_index - 1], pending[self._selected_task_index]
                    self._selected_task_index -= 1
                elif e.key == "Arrow Down" and self._selected_task_index < len(pending) - 1:
                    pending[self._selected_task_index], pending[self._selected_task_index + 1] = \
                        pending[self._selected_task_index + 1], pending[self._selected_task_index]
                    self._selected_task_index += 1
                else:
                    return False

                self.task_engine.reorder_tasks(
                    self._current_day.id,
                    [t.id for t in pending],
                )
                self._refresh_ui()
                return True
            return False

        # Up/Down: navigate selection
        if e.key == "Arrow Down":
            self._selected_task_index = min(self._selected_task_index + 1, len(pending) - 1)
            self._refresh_ui()
            return True
        if e.key == "Arrow Up":
            self._selected_task_index = max(self._selected_task_index - 1, 0)
            self._refresh_ui()
            return True
        if e.key == "Enter" and self._selected_task_index >= 0:
            selected = pending[self._selected_task_index]
            self._activate_task(selected.id)
            return True

        return False

    # ─── Lifecycle ────────────────────────────────────────────────────

    def on_stop(self) -> None:
        """Save state on shutdown."""
        logger.info("Leadership OS shutting down")

        # Stop overlay and save position
        if self._overlay:
            try:
                pos_x, pos_y = self._overlay.get_position()
                self.config.set("ui", "overlay_position_x", pos_x)
                self.config.set("ui", "overlay_position_y", pos_y)
                self.config.save()
                self._overlay.stop()
            except Exception as e:
                logger.warning("Error stopping overlay: %s", e)

        # Stop tray
        if self._tray:
            try:
                self._tray.stop()
            except Exception as e:
                logger.warning("Error stopping tray: %s", e)

        # Save state
        if self.state:
            try:
                self.state.set_needs_review(True)
                self.state.set_app_state(self._current_state)
                self.state.save()
            except Exception as e:
                logger.warning("Error saving state: %s", e)

        # Close database
        if self.db:
            try:
                self.db.close()
            except Exception as e:
                logger.warning("Error closing database: %s", e)

        # Release instance lock
        if self._instance_lock:
            try:
                self._instance_lock.release()
            except Exception as e:
                logger.warning("Error releasing instance lock: %s", e)

        logger.info("Leadership OS shutdown complete")



def main() -> None:
    """Main entry point for Leadership OS (Flet).

    Handles graceful startup including:
    - Logging setup
    - Single-instance enforcement
    - Engine initialization
    - Flet app launch
    """
    setup_logging()
    _logger = logging.getLogger(__name__)
    _logger.info("Leadership OS v%s starting...", __import__('leadership_os').__version__)

    try:
        app_instance = LeadershipOSApp()
        ft.app(target=app_instance.run)
    except Exception as e:
        _logger.error("Fatal error: %s", e, exc_info=True)
        print(f"\n❌ Fatal Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
