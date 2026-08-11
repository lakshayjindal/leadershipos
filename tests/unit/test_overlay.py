"""Tests for the floating overlay window (Phase 8)."""

from __future__ import annotations

import os
import pytest

# Check if we have a display for GUI tests
_HAS_DISPLAY = bool(os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY"))


class TestOverlayWindow:
    """Unit tests for OverlayWindow state management and IPC."""

    def test_create_overlay(self):
        """OverlayWindow should be creatable with callbacks."""
        from leadership_os.ui.overlay import OverlayWindow

        called: dict[str, int] = {}

        overlay = OverlayWindow(
            on_show_main=lambda: called.__setitem__("show", called.get("show", 0) + 1),
            on_pause=lambda: called.__setitem__("pause", called.get("pause", 0) + 1),
            on_complete=lambda: called.__setitem__("complete", called.get("complete", 0) + 1),
            on_start_break=lambda: called.__setitem__("break", called.get("break", 0) + 1),
            on_resume=lambda: called.__setitem__("resume", called.get("resume", 0) + 1),
            on_end_break=lambda: called.__setitem__("end", called.get("end", 0) + 1),
        )

        assert overlay is not None
        # Not started yet
        assert overlay._running is False

    def test_send_update_before_start_is_safe(self):
        """send_update should not crash when overlay is not running."""
        from leadership_os.ui.overlay import OverlayWindow

        overlay = OverlayWindow(
            on_show_main=lambda: None,
            on_pause=lambda: None,
            on_complete=lambda: None,
            on_start_break=lambda: None,
            on_resume=lambda: None,
            on_end_break=lambda: None,
        )

        # Should not raise
        overlay.send_update({"task": "Test", "timer": "00:01:00"})

    def test_get_position_returns_tuple(self):
        """get_position should return a tuple of (x, y)."""
        from leadership_os.ui.overlay import OverlayWindow

        overlay = OverlayWindow(
            on_show_main=lambda: None,
            on_pause=lambda: None,
            on_complete=lambda: None,
            on_start_break=lambda: None,
            on_resume=lambda: None,
            on_end_break=lambda: None,
        )

        x, y = overlay.get_position()
        assert isinstance(x, int)
        assert isinstance(y, int)

    def test_config_passed_to_overlay(self):
        """Config values should be used for opacity and position."""
        from leadership_os.ui.overlay import OverlayWindow

        overlay = OverlayWindow(
            on_show_main=lambda: None,
            on_pause=lambda: None,
            on_complete=lambda: None,
            on_start_break=lambda: None,
            on_resume=lambda: None,
            on_end_break=lambda: None,
            config={
                "overlay_opacity": 0.75,
                "overlay_position_x": 100,
                "overlay_position_y": 200,
            },
        )

        assert overlay._opacity == 0.75
        assert overlay._pos_x == 100
        assert overlay._pos_y == 200

    def test_config_defaults(self):
        """Default values should be used when no config provided."""
        from leadership_os.ui.overlay import OverlayWindow

        overlay = OverlayWindow(
            on_show_main=lambda: None,
            on_pause=lambda: None,
            on_complete=lambda: None,
            on_start_break=lambda: None,
            on_resume=lambda: None,
            on_end_break=lambda: None,
        )

        assert overlay._opacity == 0.85
        assert overlay._pos_x == -1
        assert overlay._pos_y == 40

    def test_hide_show_are_safe_before_start(self):
        """hide() and show() should not crash when overlay is not running."""
        from leadership_os.ui.overlay import OverlayWindow

        overlay = OverlayWindow(
            on_show_main=lambda: None,
            on_pause=lambda: None,
            on_complete=lambda: None,
            on_start_break=lambda: None,
            on_resume=lambda: None,
            on_end_break=lambda: None,
        )

        overlay.hide()
        overlay.show()

    def test_stop_is_safe_before_start(self):
        """stop() should not crash when overlay was never started."""
        from leadership_os.ui.overlay import OverlayWindow

        overlay = OverlayWindow(
            on_show_main=lambda: None,
            on_pause=lambda: None,
            on_complete=lambda: None,
            on_start_break=lambda: None,
            on_resume=lambda: None,
            on_end_break=lambda: None,
        )

        overlay.stop()

    def test_callbacks_are_callable(self):
        """All callback slots should be callable."""
        from leadership_os.ui.overlay import OverlayWindow

        results: list[str] = []

        overlay = OverlayWindow(
            on_show_main=lambda: results.append("show"),
            on_pause=lambda: results.append("pause"),
            on_complete=lambda: results.append("complete"),
            on_start_break=lambda: results.append("break"),
            on_resume=lambda: results.append("resume"),
            on_end_break=lambda: results.append("end"),
        )

        overlay._callbacks["show_main"]()
        overlay._callbacks["pause"]()
        overlay._callbacks["complete"]()
        overlay._callbacks["start_break"]()
        overlay._callbacks["resume"]()
        overlay._callbacks["end_break"]()

        assert results == ["show", "pause", "complete", "break", "resume", "end"]

    def test_select_task_callback_wired(self):
        """on_select_task should receive the clicked task id."""
        from leadership_os.ui.overlay import OverlayWindow

        received: list[str] = []

        overlay = OverlayWindow(
            on_show_main=lambda: None,
            on_pause=lambda: None,
            on_complete=lambda: None,
            on_start_break=lambda: None,
            on_resume=lambda: None,
            on_end_break=lambda: None,
            on_select_task=lambda tid: received.append(tid),
        )

        # Simulate clicking a pending-task row
        overlay._callbacks["select_task"]("task-123")
        assert received == ["task-123"]

    def test_select_task_optional(self):
        """on_select_task is optional — a no-op default is used when omitted."""
        from leadership_os.ui.overlay import OverlayWindow

        overlay = OverlayWindow(
            on_show_main=lambda: None,
            on_pause=lambda: None,
            on_complete=lambda: None,
            on_start_break=lambda: None,
            on_resume=lambda: None,
            on_end_break=lambda: None,
        )

        # Should not raise
        overlay._callbacks["select_task"]("task-999")

    def test_pending_tasks_stored_from_update(self):
        """send_update data with pending_tasks should be stored and trimmed."""
        from leadership_os.ui.overlay import OverlayWindow, OVERLAY_MAX_PENDING

        overlay = OverlayWindow(
            on_show_main=lambda: None,
            on_pause=lambda: None,
            on_complete=lambda: None,
            on_start_break=lambda: None,
            on_resume=lambda: None,
            on_end_break=lambda: None,
            on_select_task=lambda tid: None,
        )

        # Simulate _apply_update parsing pending tasks (no display needed)
        overlay._apply_update({
            "pending_tasks": [
                {"id": f"t{i}", "title": f"Task {i}"} for i in range(OVERLAY_MAX_PENDING + 3)
            ],
        })

        assert len(overlay._pending_tasks) == OVERLAY_MAX_PENDING
        assert overlay._pending_tasks[0]["id"] == "t0"

    def test_pending_tasks_ignore_invalid(self):
        """Entries without an id should be filtered out."""
        from leadership_os.ui.overlay import OverlayWindow

        overlay = OverlayWindow(
            on_show_main=lambda: None,
            on_pause=lambda: None,
            on_complete=lambda: None,
            on_start_break=lambda: None,
            on_resume=lambda: None,
            on_end_break=lambda: None,
        )

        overlay._apply_update({
            "pending_tasks": [{"title": "No id"}, {"id": "t1", "title": "Valid"}],
        })

        assert len(overlay._pending_tasks) == 1
        assert overlay._pending_tasks[0]["id"] == "t1"

    @pytest.mark.skipif(not _HAS_DISPLAY, reason="No display available")
    def test_start_and_stop_with_display(self):
        """Integration test: start overlay, send updates, stop."""
        from leadership_os.ui.overlay import OverlayWindow

        started: list[bool] = []

        overlay = OverlayWindow(
            on_show_main=lambda: None,
            on_pause=lambda: None,
            on_complete=lambda: None,
            on_start_break=lambda: None,
            on_resume=lambda: None,
            on_end_break=lambda: None,
        )

        overlay.start()
        assert overlay._running is True

        # Send some updates
        overlay.send_update({"task": "Test Task", "timer": "00:42:18", "state": "working"})

        import time
        time.sleep(0.3)  # Let the thread process

        overlay.stop()
        assert overlay._running is False


class TestOverlayImport:
    """Verify the overlay module can be imported in the main app context."""

    def test_import_in_app_context(self):
        """All overlay types should be importable."""
        from leadership_os.ui.overlay import (
            OverlayWindow,
            OVERLAY_WIDTH,
            OVERLAY_HEIGHT,
            DEFAULT_OPACITY,
        )

        assert OVERLAY_WIDTH == 320
        assert OVERLAY_HEIGHT == 180
        assert DEFAULT_OPACITY == 0.85
