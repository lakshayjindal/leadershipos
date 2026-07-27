"""Tray Manager — system tray integration via pystray.

Responsibilities:
- Run a system tray icon in a background daemon thread (pystray blocks)
- Display current task title, focus time, and task progress in the tray menu
- Provide quick actions: Pause, Complete, Start Break, Open App, Quit
- Communicate with the Flet app thread via EventBus (thread-safe)
- Generate tray icon using Pillow

Design principle: The tray runs in its own thread. All communication
with the Flet UI happens through the EventBus, never through direct
widget manipulation. The tray never touches UI controls directly.
"""

from __future__ import annotations

import logging
import threading
from collections.abc import Callable

try:
    import pystray
    from PIL import Image, ImageDraw
except ImportError as e:
    raise ImportError(
        "pystray and Pillow are required for system tray support. "
        "Install with: pip install pystray Pillow"
    ) from e

from leadership_os.core.event_bus import (
    BREAK_ENDED,
    BREAK_STARTED,
    TASK_ACTIVATED,
    TASK_COMPLETED,
    TASK_PAUSED,
    TIMER_STARTED,
    TIMER_STOPPED,
    EventBus,
)

logger = logging.getLogger(__name__)

# ─── Tray Menu Item Constants ─────────────────────────────────────────

MENU_CURRENT_TASK = "current_task"
MENU_FOCUS_TIME = "focus_time"
MENU_TASK_PROGRESS = "task_progress"
MENU_PAUSE_TASK = "pause_task"
MENU_COMPLETE_TASK = "complete_task"
MENU_START_BREAK = "start_break"
MENU_OPEN_APP = "open_app"
MENU_QUIT = "quit"


# ─── Icon Generation ──────────────────────────────────────────────────

def _generate_icon(width: int = 64, height: int = 64) -> Image.Image:
    """Generate a simple Leadership OS tray icon.

    Creates a dark rounded-square icon with a blue 'L' monogram.
    """
    image = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)

    # Background: rounded dark square
    margin = 4
    draw.rounded_rectangle(
        [margin, margin, width - margin, height - margin],
        radius=12,
        fill=(13, 13, 26, 255),  # #0D0D1A
    )

    # Accent bar (left edge)
    draw.rectangle(
        [margin + 2, margin + 6, margin + 6, height - margin - 6],
        fill=(74, 111, 165, 255),  # #4A6FA5
    )

    # Letter 'L' in white
    draw.text(
        (width // 2 - 6, height // 2 - 10),
        "L",
        fill=(232, 232, 240, 255),  # #E8E8F0
    )

    return image


# ─── Tray Manager ──────────────────────────────────────────────────────

class TrayManager:
    """Manages the system tray icon and menu.

    Runs pystray.Icon in a background daemon thread. Updates the tray
    menu dynamically based on app events. Emits command events back
    to the app via EventBus.

    Usage:
        tray = TrayManager(event_bus)
        tray.start()
        # ... app runs ...
        tray.stop()
    """

    def __init__(
        self,
        event_bus: EventBus,
        on_show_window: Callable[[], None] | None = None,
        on_quit: Callable[[], None] | None = None,
    ) -> None:
        self._event_bus = event_bus
        self._on_show_window = on_show_window
        self._on_quit = on_quit
        self._icon: pystray.Icon | None = None
        self._thread: threading.Thread | None = None
        self._running = False

        # Dynamic menu state (updated by events)
        self._current_task_title: str = "No active task"
        self._focus_time: str = "0m"
        self._task_progress: str = "0/0 tasks"
        self._is_working: bool = False
        self._is_break: bool = False

        # Subscribe to relevant events
        self._event_bus.subscribe(TASK_ACTIVATED, self._on_task_activated)
        self._event_bus.subscribe(TASK_COMPLETED, self._on_task_completed)
        self._event_bus.subscribe(TASK_PAUSED, self._on_task_paused)
        self._event_bus.subscribe(TIMER_STARTED, self._on_timer_event)
        self._event_bus.subscribe(TIMER_STOPPED, self._on_timer_event)
        self._event_bus.subscribe(BREAK_STARTED, self._on_break_started)
        self._event_bus.subscribe(BREAK_ENDED, self._on_break_ended)

    # ─── Lifecycle ─────────────────────────────────────────────────

    def start(self) -> None:
        """Start the tray icon in a background thread."""
        if self._running:
            logger.warning("TrayManager already running")
            return

        self._running = True
        self._thread = threading.Thread(
            target=self._run_tray, daemon=True, name="tray-thread"
        )
        self._thread.start()
        logger.info("Tray manager started")

    def stop(self) -> None:
        """Stop the tray icon and join the thread."""
        self._running = False
        if self._icon is not None:
            self._icon.stop()
        if self._thread is not None and self._thread.is_alive():
            self._thread.join(timeout=3.0)
        logger.info("Tray manager stopped")

    def update_progress(
        self, focus_time: str, completed: int, total: int
    ) -> None:
        """Update the tray menu with current progress stats."""
        self._focus_time = focus_time
        self._task_progress = f"{completed}/{total} tasks"
        # Update tray menu if running
        if self._icon is not None and self._running:
            self._icon.update_menu()

    # ─── Tray Thread ───────────────────────────────────────────────

    def _run_tray(self) -> None:
        """Main tray loop — runs in background thread."""
        try:
            icon = _generate_icon()
            self._icon = pystray.Icon(
                "leadership_os",
                icon,
                "Leadership OS",
                menu=pystray.Menu(self._build_menu),
            )
            self._icon.run()
        except Exception as e:
            logger.error("Tray icon failed: %s", e, exc_info=True)

    # ─── Menu Builder ──────────────────────────────────────────────

    def _build_menu(self) -> pystray.Menu:
        """Build the tray menu dynamically from current state.

        This is called by pystray each time the menu needs to be rendered.
        """
        # Info items (non-clickable)
        info_items = [
            pystray.MenuItem(
                f"📋 {self._current_task_title[:40]}{'...' if len(self._current_task_title) > 40 else ''}",
                None,
                enabled=False,
            ),
            pystray.MenuItem(
                f"⏱  Focus: {self._focus_time}",
                None,
                enabled=False,
            ),
            pystray.MenuItem(
                f"📅 {self._task_progress}",
                None,
                enabled=False,
            ),
            pystray.Menu.SEPARATOR,
        ]

        # Action items
        if self._is_break:
            action_items = [
                pystray.MenuItem(
                    "▶ Resume Work",
                    self._on_menu_resume,
                    default=True,
                ),
                pystray.MenuItem(
                    "■ End Break",
                    self._on_menu_end_break,
                ),
            ]
        elif self._is_working:
            action_items = [
                pystray.MenuItem(
                    "⏸ Pause Task",
                    self._on_menu_pause,
                    default=True,
                ),
                pystray.MenuItem(
                    "✓ Complete Task",
                    self._on_menu_complete,
                ),
                pystray.MenuItem(
                    "☕ Start Break",
                    self._on_menu_start_break,
                ),
            ]
        else:
            action_items = [
                pystray.MenuItem(
                    "📝 Open App",
                    self._on_menu_open,
                    default=True,
                ),
            ]

        # Bottom items
        bottom_items = [
            pystray.Menu.SEPARATOR,
            pystray.MenuItem(
                "📝 Open App",
                self._on_menu_open,
            ),
            pystray.MenuItem(
                "❌ Quit",
                self._on_menu_quit,
            ),
        ]

        return pystray.Menu(*(info_items + action_items + bottom_items))

    # ─── Menu Callbacks (thread-safe) ──────────────────────────────

    def _on_menu_open(self) -> None:
        """Show the main window."""
        if self._on_show_window:
            self._on_show_window()

    def _on_menu_quit(self) -> None:
        """Quit the application."""
        if self._on_quit:
            self._on_quit()
        self.stop()

    def _on_menu_pause(self) -> None:
        """Emit pause command."""
        self._event_bus.emit("cmd_pause_task", {})

    def _on_menu_complete(self) -> None:
        """Emit complete command."""
        self._event_bus.emit("cmd_complete_task", {})

    def _on_menu_start_break(self) -> None:
        """Emit start break command."""
        self._event_bus.emit("cmd_start_break", {})

    def _on_menu_resume(self) -> None:
        """Emit resume command."""
        self._event_bus.emit("cmd_resume_task", {})

    def _on_menu_end_break(self) -> None:
        """Emit end break command."""
        self._event_bus.emit("cmd_end_break", {})

    # ─── Event Handlers ────────────────────────────────────────────

    def _on_task_activated(self, event: str, data: dict) -> None:
        title = data.get("title", "Working...")
        self._current_task_title = title
        self._is_working = True
        self._is_break = False

    def _on_task_completed(self, event: str, data: dict) -> None:
        self._is_working = False
        self._current_task_title = "No active task"

    def _on_task_paused(self, event: str, data: dict) -> None:
        self._is_working = False

    def _on_timer_event(self, event: str, data: dict) -> None:
        """Handle timer tick events for updating focus time."""
        # Timer events carry duration info
        duration = data.get("duration_seconds", 0)
        total = data.get("total_seconds", duration)
        hours = total // 3600
        minutes = (total % 3600) // 60
        if hours > 0:
            self._focus_time = f"{hours}h {minutes}m"
        else:
            self._focus_time = f"{minutes}m"

    def _on_break_started(self, event: str, data: dict) -> None:
        self._is_break = True
        self._is_working = False
        self._current_task_title = "On Break"

    def _on_break_ended(self, event: str, data: dict) -> None:
        self._is_break = False
