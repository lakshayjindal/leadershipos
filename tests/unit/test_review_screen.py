"""Unit tests for the End-of-Day review screen."""

from __future__ import annotations

import pytest

import flet as ft

from leadership_os.ui.widgets.review_screen import build_review_screen


class TestBuildReviewScreen:
    """Test building and interacting with the review screen."""

    def test_build_returns_container(self):
        """The review screen should return a Flet Container."""
        screen = build_review_screen(
            focus_seconds=3600,
            completed_count=3,
            total_count=5,
            session_count=4,
            break_seconds=600,
            tomorrow_tasks=["Task A", "Task B"],
        )
        assert isinstance(screen, ft.Container)

    def test_finalize_callback_receives_data(self):
        """Clicking finalize should invoke the callback with reflection data."""
        captured = {}

        def on_finalize(data):
            captured["data"] = data

        screen = build_review_screen(
            focus_seconds=3600,
            completed_count=3,
            total_count=5,
            session_count=4,
            break_seconds=600,
            tomorrow_tasks=["Task A"],
            initial_accomplishments="Finished things",
            initial_challenges="Hard problems",
            initial_tomorrow_first="Keep going",
            initial_notes="Note here",
            on_finalize=on_finalize,
        )
        # Simulate clicking the finalize button by calling its on_click handler.
        # The screen contains the finalize button; find it by traversing controls.
        finalize_button = self._find_finalize_button(screen)
        assert finalize_button is not None
        finalize_button.on_click(None)

        assert captured["data"]["accomplishments"] == "Finished things"
        assert captured["data"]["challenges"] == "Hard problems"
        assert captured["data"]["tomorrow_first"] == "Keep going"
        assert captured["data"]["additional_notes"] == "Note here"

    def test_skip_callback_invoked(self):
        """Clicking skip should invoke the skip callback."""
        skipped = {"called": False}

        def on_skip():
            skipped["called"] = True

        screen = build_review_screen(
            focus_seconds=3600,
            completed_count=3,
            total_count=5,
            session_count=4,
            break_seconds=600,
            tomorrow_tasks=["Task A"],
            on_skip=on_skip,
        )
        skip_button = self._find_button_by_text(screen, "Skip Review")
        assert skip_button is not None
        skip_button.on_click(None)
        assert skipped["called"] is True

    def test_cancel_callback_invoked(self):
        """Clicking cancel should invoke the cancel callback."""
        cancelled = {"called": False}

        def on_cancel():
            cancelled["called"] = True

        screen = build_review_screen(
            focus_seconds=3600,
            completed_count=3,
            total_count=5,
            session_count=4,
            break_seconds=600,
            tomorrow_tasks=["Task A"],
            on_cancel=on_cancel,
        )
        cancel_button = self._find_button_by_text(screen, "Cancel")
        assert cancel_button is not None
        cancel_button.on_click(None)
        assert cancelled["called"] is True

    def test_empty_tomorrow_shows_message(self):
        """When there are no tomorrow tasks, a placeholder message is shown."""
        screen = build_review_screen(
            focus_seconds=3600,
            completed_count=3,
            total_count=5,
            session_count=4,
            break_seconds=600,
            tomorrow_tasks=[],
        )
        # Just ensure it builds without error
        assert isinstance(screen, ft.Container)

    def test_finalize_button_disabled_and_reenabled(self):
        """The finalize button is disabled during finalize and re-enabled after."""
        captured = {"button_states": []}

        def on_finalize(data):
            captured["button_states"].append(captured["button"].disabled)

        screen = build_review_screen(
            focus_seconds=3600,
            completed_count=3,
            total_count=5,
            session_count=4,
            break_seconds=600,
            tomorrow_tasks=["Task A"],
            on_finalize=on_finalize,
        )
        finalize_button = self._find_finalize_button(screen)
        assert finalize_button is not None
        captured["button"] = finalize_button

        assert finalize_button.disabled is False
        finalize_button.on_click(None)
        assert finalize_button.disabled is False
        assert captured["button_states"] == [True]

    def test_finalize_button_reenabled_on_exception(self):
        """The finalize button is re-enabled even if the callback raises."""
        def on_finalize(data):
            raise RuntimeError("boom")

        screen = build_review_screen(
            focus_seconds=3600,
            completed_count=3,
            total_count=5,
            session_count=4,
            break_seconds=600,
            tomorrow_tasks=["Task A"],
            on_finalize=on_finalize,
        )
        finalize_button = self._find_finalize_button(screen)
        assert finalize_button is not None
        assert finalize_button.disabled is False

        with pytest.raises(RuntimeError, match="boom"):
            finalize_button.on_click(None)

        assert finalize_button.disabled is False

    def _find_finalize_button(self, control: ft.Control) -> ft.Button | None:
        for child in self._iter_controls(control):
            if isinstance(child, ft.Button):
                return child
        return None

    def _find_button_by_text(self, control: ft.Control, label: str) -> ft.TextButton | None:
        for child in self._iter_controls(control):
            if isinstance(child, ft.TextButton):
                content = getattr(child, "content", None)
                if isinstance(content, ft.Text) and label in (content.value or ""):
                    return child
        return None

    def _iter_controls(self, control: ft.Control):
        """Yield the control and recursively yield its descendants."""
        yield control
        children = getattr(control, "controls", None) or []
        for child in children:
            yield from self._iter_controls(child)
        # Some controls have a single `content` child
        content = getattr(control, "content", None)
        if isinstance(content, ft.Control):
            yield from self._iter_controls(content)
