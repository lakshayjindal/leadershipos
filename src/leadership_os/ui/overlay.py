"""Floating Overlay Window — always-on-top semi-transparent companion window.

Displays current task, elapsed timer, and next task at a glance.
Built with Tkinter (stdlib) for reliable cross-platform always-on-top behavior.

If tkinter is not available (headless/server environments), the overlay
gracefully degrades: OverlayWindow can still be instantiated but start()
will log a warning and do nothing.

Features:
- Frameless, always-on-top, semi-transparent (configurable opacity)
- Draggable (click and drag anywhere on the window)
- Click to show/hide the main app window
- Right-click context menu: Pause, Complete, Start Break, Resume, End Break
- Updates via thread-safe queue from the main Flet app
- Remembers position across restarts
"""

from __future__ import annotations

import logging
import queue
import threading
from pathlib import Path
from typing import Any, Callable

logger = logging.getLogger(__name__)

# ── Optional tkinter import ──────────────────────────────────────────
try:
    import tkinter as tk
    _HAS_TKINTER = True
except ModuleNotFoundError:
    _HAS_TKINTER = False
    logger.warning("tkinter not available — floating overlay disabled")

# ─── Defaults ─────────────────────────────────────────────────────────

OVERLAY_WIDTH = 320
OVERLAY_HEIGHT = 180
DEFAULT_OPACITY = 0.85

# Dark theme colors
BG_COLOR = "#14142A"
TEXT_PRIMARY = "#E8E8F0"
TEXT_SECONDARY = "#9898B8"
TEXT_MUTED = "#747496"
ACCENT_BLUE = "#4A6FA5"
ACCENT_GREEN = "#66A66B"
ACCENT_RED = "#C45B5B"
ACCENT_AMBER = "#C4A35A"


class OverlayWindow:
    """Floating always-on-top overlay window using Tkinter.

    Runs in a background thread. Receives updates via a thread-safe queue.
    If tkinter is not available, all methods are no-ops.

    Usage:
        overlay = OverlayWindow(callbacks)
        overlay.start()
        overlay.send_update({"task": "Implement Feature", "timer": "00:42:18", ...})
        overlay.stop()
    """

    def __init__(
        self,
        on_show_main: Callable[[], None],
        on_pause: Callable[[], None],
        on_complete: Callable[[], None],
        on_start_break: Callable[[], None],
        on_resume: Callable[[], None],
        on_end_break: Callable[[], None],
        config: dict[str, Any] | None = None,
    ) -> None:
        """
        Args:
            on_show_main: Called when overlay is clicked (show/hide main window).
            on_pause: Called when "Pause Task" is selected from context menu.
            on_complete: Called when "Complete Task" is selected.
            on_start_break: Called when "Start Break" is selected.
            on_resume: Called when "Resume Work" is selected.
            on_end_break: Called when "End Break" is selected.
            config: Optional config dict with overlay_opacity, overlay_position_x/y.
        """
        self._callbacks = {
            "show_main": on_show_main,
            "pause": on_pause,
            "complete": on_complete,
            "start_break": on_start_break,
            "resume": on_resume,
            "end_break": on_end_break,
        }

        # Config
        self._opacity = DEFAULT_OPACITY
        self._pos_x = -1  # -1 means right edge
        self._pos_y = 40
        if config:
            self._opacity = float(config.get("overlay_opacity", DEFAULT_OPACITY))
            self._pos_x = int(config.get("overlay_position_x", -1))
            self._pos_y = int(config.get("overlay_position_y", 40))

        # State
        self._queue: queue.Queue[dict[str, Any]] = queue.Queue()
        self._root: tk.Tk | None = None
        self._thread: threading.Thread | None = None
        self._running = False
        self._visible = True

        # Current display data
        self._current: dict[str, str] = {
            "task": "",
            "timer": "00:00:00",
            "state": "idle",
            "state_label": "Ready",
            "priority": "",
            "next_task": "",
        }

    # ─── Public API ──────────────────────────────────────────────────

    def start(self) -> None:
        """Start the overlay in a background daemon thread.

        If tkinter is not available, logs a warning and does nothing.
        """
        if not _HAS_TKINTER:
            logger.warning("Cannot start overlay: tkinter not available")
            return
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._run, daemon=True, name="overlay")
        self._thread.start()
        logger.info("Overlay window started")

    def stop(self) -> None:
        """Stop the overlay window and join the thread."""
        self._running = False
        if _HAS_TKINTER:
            self._queue.put({"__command__": "quit"})
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2.0)
        logger.info("Overlay window stopped")

    def send_update(self, data: dict[str, Any]) -> None:
        """Push an update to the overlay (thread-safe)."""
        if self._running and _HAS_TKINTER:
            self._queue.put(data)

    def hide(self) -> None:
        """Hide the overlay window."""
        if _HAS_TKINTER:
            self._queue.put({"__command__": "hide"})

    def show(self) -> None:
        """Show the overlay window."""
        if _HAS_TKINTER:
            self._queue.put({"__command__": "show"})

    def get_position(self) -> tuple[int, int]:
        """Get the current overlay position (for saving to config)."""
        return (self._pos_x, self._pos_y)

    # ─── Internal: Thread Loop ───────────────────────────────────────

    def _run(self) -> None:
        """Main loop running in the background thread. Requires tkinter."""
        if not _HAS_TKINTER:
            return

        self._root = tk.Tk()
        self._root.title("Leadership OS")
        self._root.overrideredirect(True)
        self._root.attributes("-topmost", True)
        self._root.attributes("-alpha", self._opacity)

        self._build_ui()
        self._position_window()

        self._root.bind("<Button-1>", self._on_drag_start)
        self._root.bind("<B1-Motion>", self._on_drag_motion)
        self._root.bind("<Button-3>", self._on_right_click)

        self._poll_updates()
        self._root.mainloop()

    def _build_ui(self) -> None:
        """Build the overlay UI with tkinter widgets."""
        if self._root is None:
            return

        self._root.configure(bg=BG_COLOR)
        self._root.geometry(f"{OVERLAY_WIDTH}x{OVERLAY_HEIGHT}")

        frame = tk.Frame(self._root, bg=BG_COLOR, padx=14, pady=12)
        frame.pack(fill=tk.BOTH, expand=True)

        # Row 1: State dot + label + priority
        row1 = tk.Frame(frame, bg=BG_COLOR)
        row1.pack(fill=tk.X)

        self._state_dot = tk.Canvas(row1, width=10, height=10, bg=BG_COLOR, highlightthickness=0)
        self._state_dot.pack(side=tk.LEFT, padx=(0, 6))
        self._state_dot.create_oval(1, 1, 9, 9, fill=ACCENT_AMBER, outline="")

        self._state_label_w = tk.Label(
            row1, text="Ready", font=("Inter", 9, "bold"),
            fg=TEXT_SECONDARY, bg=BG_COLOR,
        )
        self._state_label_w.pack(side=tk.LEFT)

        self._priority_label_w = tk.Label(
            row1, text="", font=("Inter", 9),
            fg=TEXT_MUTED, bg=BG_COLOR,
        )
        self._priority_label_w.pack(side=tk.RIGHT)

        # Row 2: Task title
        tk.Frame(frame, bg=BG_COLOR, height=6).pack()
        self._task_label = tk.Label(
            frame, text="No active task",
            font=("Inter", 15, "bold"),
            fg=TEXT_PRIMARY, bg=BG_COLOR,
            anchor="w", justify=tk.LEFT, wraplength=OVERLAY_WIDTH - 28,
        )
        self._task_label.pack(fill=tk.X)

        # Row 3: Timer
        tk.Frame(frame, bg=BG_COLOR, height=8).pack()
        self._timer_label = tk.Label(
            frame, text="00:00:00",
            font=("Roboto Mono", 36, "bold"),
            fg=TEXT_SECONDARY, bg=BG_COLOR,
        )
        self._timer_label.pack()

        # Row 4: Next task
        tk.Frame(frame, bg=BG_COLOR, height=8).pack()
        next_frame = tk.Frame(frame, bg=BG_COLOR)
        next_frame.pack(fill=tk.X)
        tk.Label(
            next_frame, text="Next: ", font=("Inter", 9),
            fg=TEXT_MUTED, bg=BG_COLOR,
        ).pack(side=tk.LEFT)
        self._next_label = tk.Label(
            next_frame, text="—",
            font=("Inter", 9),
            fg=TEXT_MUTED, bg=BG_COLOR,
            anchor="w",
        )
        self._next_label.pack(side=tk.LEFT, fill=tk.X, expand=True)

    def _position_window(self) -> None:
        """Position the overlay on screen based on config."""
        if self._root is None:
            return
        self._root.update_idletasks()
        screen_width = self._root.winfo_screenwidth()
        if self._pos_x < 0:
            x = screen_width - OVERLAY_WIDTH - 20
        else:
            x = self._pos_x
        self._root.geometry(f"+{x}+{self._pos_y}")

    def _poll_updates(self) -> None:
        """Check the queue for updates and apply them."""
        if self._root is None:
            return

        try:
            while True:
                data = self._queue.get_nowait()
                command = data.get("__command__")
                if command == "quit":
                    self._root.destroy()
                    return
                elif command == "hide":
                    self._root.withdraw()
                    self._visible = False
                    continue
                elif command == "show":
                    self._root.deiconify()
                    self._visible = True
                    continue
                self._apply_update(data)
        except queue.Empty:
            pass

        if self._running:
            self._root.after(250, self._poll_updates)

    def _apply_update(self, data: dict[str, Any]) -> None:
        """Apply a data update to the overlay widgets."""
        if "task" in data:
            self._task_label.configure(text=data["task"] or "No active task")
        if "timer" in data:
            self._timer_label.configure(text=data["timer"])
        if "state" in data:
            state_colors = {"working": ACCENT_GREEN, "break": ACCENT_RED, "idle": ACCENT_AMBER}
            color = state_colors.get(data["state"], ACCENT_AMBER)
            self._state_dot.delete("all")
            self._state_dot.create_oval(1, 1, 9, 9, fill=color, outline="")
        if "state_label" in data:
            self._state_label_w.configure(text=data["state_label"])
        if "priority" in data:
            self._priority_label_w.configure(text=data["priority"])
        if "next_task" in data:
            self._next_label.configure(text=data["next_task"] or "—")

    # ─── Drag handling ───────────────────────────────────────────────

    def _on_drag_start(self, event) -> None:
        self._drag_x = event.x
        self._drag_y = event.y

    def _on_drag_motion(self, event) -> None:
        if self._root is None:
            return
        x = self._root.winfo_x() + event.x - self._drag_x
        y = self._root.winfo_y() + event.y - self._drag_y
        self._root.geometry(f"+{x}+{y}")
        self._pos_x = x
        self._pos_y = y

    # ─── Context menu ────────────────────────────────────────────────

    def _on_right_click(self, event) -> None:
        """Show right-click context menu."""
        menu = tk.Menu(self._root, tearoff=0, bg="#1A1A2E", fg=TEXT_PRIMARY,
                       activebackground="#2D2D4A", activeforeground=TEXT_PRIMARY,
                       font=("Inter", 10))
        menu.add_command(label="Pause Task", command=self._callbacks["pause"])
        menu.add_command(label="Complete Task", command=self._callbacks["complete"])
        menu.add_separator()
        menu.add_command(label="Start Break", command=self._callbacks["start_break"])
        menu.add_command(label="Resume Work", command=self._callbacks["resume"])
        menu.add_command(label="End Break", command=self._callbacks["end_break"])
        menu.add_separator()
        menu.add_command(label="Show Main Window", command=self._callbacks["show_main"])
        menu.post(event.x_root, event.y_root)
