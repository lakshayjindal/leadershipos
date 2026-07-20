"""Leadership OS — KivyMD Application.

Main application class that initializes all engines, sets up the theme,
manages app state transitions, and wires together the UI layer.

This module is the entry point for the KivyMD GUI version.
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

from kivy.lang import Builder
from kivy.properties import StringProperty
from kivy.core.window import Window
from kivy.clock import Clock
from kivy.uix.boxlayout import BoxLayout

from kivymd.app import MDApp
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.textfield import MDTextField

from leadership_os.ui.theme import theme
from leadership_os.ui.widgets.task_card import TaskCard
from leadership_os.utils.path_utils import get_app_data_dir, ensure_directory, get_log_path
from leadership_os.utils.time_utils import format_duration, format_duration_short
from leadership_os.core.enums import TaskStatus

# Import all widget classes to register them with Kivy's Factory
# (required before MainLayout is created, since main.kv references them)
from leadership_os.ui.widgets.sidebar import Sidebar  # noqa: F401
from leadership_os.ui.widgets.status_bar import StatusBar  # noqa: F401
from leadership_os.ui.widgets.execution_panel import ExecutionPanel  # noqa: F401
from leadership_os.ui.widgets.task_card import TaskCard  # noqa: F401
from leadership_os.ui.widgets.timer_display import TimerDisplay, ProgressRing  # noqa: F401
from leadership_os.ui.widgets.progress_bar import ProgressBar  # noqa: F401
from leadership_os.ui.widgets.task_form import TaskForm  # noqa: F401
from leadership_os.ui.widgets.top_bar import TopBar  # noqa: F401

# Load the root KV layout (after all widget classes are registered)
_kv_dir = Path(__file__).resolve().parent / "ui" / "kv"
_main_kv = _kv_dir / "main.kv"
if _main_kv.exists():
    Builder.load_file(str(_main_kv))

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


class MainLayout(MDBoxLayout):
    """Root layout widget — the top-level container for all UI regions."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "vertical"


class LeadershipOSApp(MDApp):
    """Primary application class for Leadership OS.

    Manages:
    - App lifecycle (startup, build, on_stop)
    - Theme initialization
    - Engine initialization and wiring
    - App state transitions
    - Screen navigation
    """

    current_state = StringProperty("startup")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.title = "Leadership OS"
        self._initialized = False

        # Core services (initialized in build)
        self.db = None
        self.config = None
        self.state = None
        self.event_bus = None

        # Engines (initialized in build)
        self.task_engine = None
        self.timer_engine = None
        self.break_engine = None
        self.journal_engine = None
        self.recovery_mgr = None

        # Runtime state
        self.main_layout = None
        self._current_day = None
        self._active_task_id = None

    def build(self):
        """Build the application UI and initialize all services.

        This is called by KivyMD when the app starts.
        """
        # 1. Set window properties
        Window.set_title("Leadership OS")
        Window.minimum_width = 900
        Window.minimum_height = 600
        Window.size_hint = (0.8, 0.8)

        # 2. Initialize the theme for KivyMD 2.0
        theme.apply_to_app(self)

        # 3. Initialize core services (KV files are loaded by individual widget modules)
        self._init_services()

        # 4. Initialize engines
        self._init_engines()

        # 5. Run startup recovery
        self._run_startup()

        # 6. Return the main layout
        main = MainLayout()
        Clock.schedule_once(lambda dt: self._on_build_complete(main), 0)
        return main

    def _init_services(self) -> None:
        """Initialize database, config, state, and event bus."""
        app_dir = get_app_data_dir()
        ensure_directory(app_dir)
        logger.info("App data directory: %s", app_dir)

        from leadership_os.core.database import Database
        from leadership_os.config.config_manager import ConfigManager
        from leadership_os.core.state_manager import StateManager
        from leadership_os.core.event_bus import EventBus

        # Database
        self.db = Database(app_dir / "leadership_os.db")
        self.db.initialize()
        logger.info("Database initialized")

        # Config
        self.config = ConfigManager(app_dir / "config.toml")
        self.config.load()
        logger.info("Configuration loaded")

        # State
        self.state = StateManager(app_dir / "state.json")
        self.state.load()
        logger.info("State loaded")

        # Event bus
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

        self.current_state = recovery.suggested_state
        logger.info("Startup state: %s", self.current_state)

    def _on_build_complete(self, main: MainLayout) -> None:
        """Called after the UI is fully built — wires engines to UI widgets."""
        self.main_layout = main

        # Wire sidebar navigation callbacks
        sidebar = main.ids.sidebar
        sidebar.today_callback = self.switch_to_today
        sidebar.history_callback = self.switch_to_history
        sidebar.settings_callback = self.switch_to_settings

        # Wire execution panel callbacks
        panel = main.ids.execution_panel
        panel.on_pause = self._pause_active_task
        panel.on_complete = self._complete_active_task
        panel.on_start_break = self._start_break
        panel.on_resume = self._resume_from_break
        panel.on_end_break = self._end_break

        # Get today's day record
        self._current_day = self.db.get_or_create_today()

        # Load initial task list
        self._refresh_task_list()

        # Start periodic update tick (1x per second for timer, 5x for progress)
        Clock.schedule_interval(self._ui_tick, 1.0)

        # Set the date label
        from datetime import date
        today = date.today()
        main.ids.date_label.text = today.strftime("Today, %B %d")

        logger.info("Leadership OS UI ready — engines wired")

    def _on_app_state_changed(self, event: str, data: dict) -> None:
        """React to application state changes."""
        new_state = data.get("state", "")
        if new_state:
            self.current_state = new_state

    # ─── Periodic UI Update ───────────────────────────────────────────

    def _ui_tick(self, dt: float) -> None:
        """Periodic UI update — refreshes timer, progress, and status."""
        main = self.main_layout
        if not main or not self._current_day:
            return

        panel = main.ids.execution_panel
        status_bar = main.ids.status_bar
        sidebar = main.ids.sidebar

        try:
            day_id = self._current_day.id
            active_task_id = self.state.get_active_task_id() if self.state else None

            # Update timer display
            if active_task_id:
                elapsed = self.timer_engine.get_elapsed(active_task_id)
                panel.timer_display = format_duration(elapsed)
                panel.session_elapsed = format_duration_short(elapsed)
                panel.timer_running = self.timer_engine.is_timer_running(active_task_id)
                # Update estimated time from the active task
                active_task = self.task_engine.get_task(active_task_id) if self.task_engine else None
                if active_task and active_task.estimated_minutes:
                    panel.session_estimated = format_duration_short(active_task.estimated_minutes * 60)
                else:
                    panel.session_estimated = "--:--"

            # Update progress from task list
            tasks = self.task_engine.get_tasks(day_id) if self.task_engine else []
            completed = sum(1 for t in tasks if t.status == TaskStatus.COMPLETED.value)
            total = len(tasks)
            panel.completed_count = completed
            panel.total_count = total
            sidebar.completed_count = completed
            sidebar.total_count = total

            # Update progress status text
            if total == 0:
                panel.progress_status = "No tasks yet"
            elif completed == total:
                panel.progress_status = "All done!"
            else:
                panel.progress_status = f"{total - completed} remaining"

            # Update sidebar session info
            sidebar.app_state = self.current_state

            # Update focus time displays
            if self.timer_engine:
                day_focus = self.timer_engine.get_day_focus_seconds(day_id)
                status_bar.update_focus(day_focus)
                sidebar.focus_time = day_focus
                panel.focus_time_display = format_duration_short(day_focus)
            status_bar.update_completed(completed)

            # Update focus card
            focus_card = main.ids.focus_card
            focus_title = main.ids.focus_task_title
            focus_time = main.ids.focus_time_badge
            if active_task_id:
                active_task = self.task_engine.get_task(active_task_id)
                if active_task:
                    focus_title.text = active_task.title
                    focus_time.text = format_duration_short(
                        self.timer_engine.get_elapsed(active_task_id)
                    )
                focus_card.height = "56dp"
                focus_card.opacity = 1
                focus_card.disabled = False
            else:
                focus_title.text = "No active task"
                focus_time.text = "00:00"
                focus_card.height = "0dp"
                focus_card.opacity = 0
                focus_card.disabled = True

            # Update visibility of empty state and section labels
            has_tasks = total > 0
            has_completed = completed > 0
            main.ids.empty_state_box.height = "196dp" if not has_tasks else "0dp"
            main.ids.empty_state_box.opacity = 1 if not has_tasks else 0
            main.ids.empty_state_box.disabled = has_tasks
            main.ids.section_pending_header.height = "20dp" if has_tasks else "0dp"
            main.ids.section_pending_header.opacity = 1 if has_tasks else 0
            main.ids.section_completed_header.height = "20dp" if has_completed else "0dp"
            main.ids.section_completed_header.opacity = 0.6 if has_completed else 0
            main.ids.section_completed_header.disabled = not has_completed

            # Update section divider visibility
            # Divider is before the task section headers

        except Exception as e:
            logger.debug("UI tick error: %s", e)

    # ─── Task Lifecycle ───────────────────────────────────────────────

    def on_task_submit(self) -> None:
        """Called when user submits a new task title."""
        logger.info("on_task_submit called")
        if not self.main_layout:
            logger.warning("on_task_submit: main_layout is None")
            return
        if not self._current_day:
            logger.warning("on_task_submit: _current_day is None")
            return

        title_input = self.main_layout.ids.task_title_input
        title = title_input.text.strip()
        if not title:
            logger.debug("on_task_submit: empty title")
            return

        try:
            task = self.task_engine.create_task(
                day_id=self._current_day.id,
                title=title,
            )
            title_input.text = ""
            logger.info("Task created: %s (id=%s)", task.title, task.id)

            # Auto-activate the new task so the timer starts and buttons unlock
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
            self.current_state = "working"
            self._sync_execution_panel(task)
            self._refresh_task_list()
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
            self._sync_execution_panel(None)
            self._refresh_task_list()
            self.current_state = "planning"
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
            self._sync_execution_panel(None)
            self._refresh_task_list()
            self.current_state = "planning"
            logger.info("Paused task: %s", task.title)
        except Exception as e:
            logger.error("Failed to pause task: %s", e)

    def _start_break(self) -> None:
        """Start a break — pauses active task."""
        if not self.break_engine or not self._current_day:
            return
        try:
            self.break_engine.start_break(day_id=self._current_day.id)
            panel = self.main_layout.ids.execution_panel
            panel.panel_state = "break"
            self.current_state = "break"
            self._refresh_task_list()
            logger.info("Break started")
        except Exception as e:
            logger.error("Failed to start break: %s", e)

    def _resume_from_break(self) -> None:
        """Resume work from break — alias for end_break."""
        self._end_break()

    def _end_break(self) -> None:
        """End break — resumes the paused task."""
        if not self.break_engine or not self._current_day:
            return
        try:
            self.break_engine.end_break(day_id=self._current_day.id)
            panel = self.main_layout.ids.execution_panel
            # Check if a task was resumed
            active_id = self.state.get_active_task_id() if self.state else None
            if active_id:
                task = self.task_engine.get_task(active_id)
                self._sync_execution_panel(task)
                panel.panel_state = "working"
                self.current_state = "working"
            else:
                panel.panel_state = "idle"
                self.current_state = "planning"
            self._refresh_task_list()
            logger.info("Break ended")
        except Exception as e:
            logger.error("Failed to end break: %s", e)

    # ─── Task List UI ─────────────────────────────────────────────────

    def _refresh_task_list(self) -> None:
        """Rebuild the task list UI from the current day's tasks."""
        if not self.main_layout or not self._current_day or not self.task_engine:
            return

        task_container = self.main_layout.ids.task_list_container
        completed_container = self.main_layout.ids.completed_container
        task_container.clear_widgets()
        completed_container.clear_widgets()

        tasks = self.task_engine.get_tasks(self._current_day.id)
        active_id = self.state.get_active_task_id() if self.state else None

        for task in tasks:
            card = TaskCard()
            card.task_id = task.id
            card.title = task.title
            card.priority = task.priority
            card.status = task.status
            card.deadline = task.deadline or ""
            card.estimated_minutes = task.estimated_minutes or 0
            card.actual_seconds = task.actual_seconds or 0
            card.is_active = (task.id == active_id)
            card.is_completed = (task.status == TaskStatus.COMPLETED.value)

            # Wire card callbacks
            card.on_activate = lambda tid=task.id: self._activate_task(tid)
            card.on_complete = lambda tid=task.id: self._complete_task_from_card(tid)
            card.on_edit = lambda tid=task.id: logger.info("Edit task: %s", tid)
            card.on_delete = lambda tid=task.id: self._delete_task(tid)

            # Place in active list or completed section
            if task.status == TaskStatus.COMPLETED.value:
                completed_container.add_widget(card)
            else:
                task_container.add_widget(card)

        # Update next task in execution panel
        panel = self.main_layout.ids.execution_panel
        pending = [t for t in tasks if t.status in (
            TaskStatus.PENDING.value, TaskStatus.ACTIVE.value, TaskStatus.PAUSED.value
        )]
        if pending:
            panel.next_task_title = pending[0].title
        else:
            panel.next_task_title = ""

    def _sync_execution_panel(self, task) -> None:
        """Sync the execution panel to show/hide the current task."""
        if not self.main_layout:
            return
        panel = self.main_layout.ids.execution_panel
        if task:
            panel.set_task(task.title, task.priority)
            panel.panel_state = "working"
        else:
            panel.clear_task()

    def _complete_task_from_card(self, task_id: str) -> None:
        """Complete a task from the task card button."""
        if not self.task_engine:
            return
        try:
            # Capture active_id BEFORE completion clears it
            was_active = (self.state.get_active_task_id() == task_id) if self.state else False
            self.task_engine.complete_task(task_id)
            if was_active:
                self._sync_execution_panel(None)
            self._refresh_task_list()
            logger.info("Task completed from card: %s", task_id)
        except Exception as e:
            logger.error("Failed to complete task from card: %s", e)

    def _delete_task(self, task_id: str) -> None:
        """Delete a task from the card."""
        if not self.task_engine:
            return
        try:
            # Capture active_id BEFORE deletion clears it
            was_active = (self.state.get_active_task_id() == task_id) if self.state else False
            self.task_engine.delete_task(task_id)
            if was_active:
                self._sync_execution_panel(None)
                self.current_state = "planning"
            self._refresh_task_list()
            logger.info("Task deleted: %s", task_id)
        except Exception as e:
            logger.error("Failed to delete task: %s", e)

    # ─── Navigation Methods ───────────────────────────────────────────

    def switch_to_today(self) -> None:
        """Navigate to the Today/Planning view."""
        self.current_state = "planning"
        self._refresh_task_list()
        logger.info("Navigated to Today")

    def switch_to_history(self) -> None:
        """Navigate to the History view."""
        logger.info("Navigated to History")
        # Phase 9 will implement the History screen

    def switch_to_settings(self) -> None:
        """Navigate to the Settings view."""
        logger.info("Navigated to Settings")
        # Phase 9 will implement the Settings screen

    def show_search(self) -> None:
        """Open the search dialog."""
        logger.info("Search requested")
        # Phase 9 will implement search

    def show_command_palette(self) -> None:
        """Open the command palette."""
        logger.info("Command palette requested")
        # Future: Phase 9+ will implement command palette

    # ─── Lifecycle ────────────────────────────────────────────────────

    def on_stop(self) -> None:
        """Called when the application is shutting down."""
        logger.info("Leadership OS shutting down")

        if self.state:
            self.state.set_needs_review(True)
            self.state.set_app_state(self.current_state)
            self.state.save()

        if self.db:
            self.db.close()

        logger.info("Leadership OS shutdown complete")


def main() -> None:
    """Main entry point for Leadership OS."""
    setup_logging()
    _logger = logging.getLogger(__name__)
    _logger.info("Leadership OS starting...")

    try:
        LeadershipOSApp().run()
    except Exception as e:
        _logger.error("Fatal error: %s", e, exc_info=True)
        print(f"\n❌ Fatal Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
