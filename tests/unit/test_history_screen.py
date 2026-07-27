"""Tests for the history screen."""

from __future__ import annotations

from unittest.mock import patch

import flet as ft

from leadership_os.core.database import Database
from leadership_os.ui.widgets.history_screen import (
    _format_date_heading,
    build_history_screen,
    init_history_list,
)


class TestFormatDateHeading:
    def test_valid_date(self):
        assert _format_date_heading("2026-07-14") == "Tuesday, July 14, 2026"

    def test_invalid_date_returns_original(self):
        assert _format_date_heading("not-a-date") == "not-a-date"


class TestBuildHistoryScreen:
    def test_build_returns_container(self, db: Database):
        calls = []
        screen = build_history_screen(db, lambda: calls.append("close"))
        assert isinstance(screen, ft.Container)
        # Should expose internal handles after build
        assert hasattr(screen, "_lhos_select_day")
        assert hasattr(screen, "_lhos_day_list_ref")

    def test_init_history_list_populates_days(self, db: Database):
        # Create a day with a task so the list is not empty
        from leadership_os.core.models import Task
        day = db.get_or_create_today()
        db.create_task(Task(day_id=day.id, title="History Task"))

        screen = build_history_screen(db, lambda: None)

        # Patch update on the day list column so we don't need a real Flet page
        with patch.object(screen._lhos_day_list_ref.current, "update"):
            init_history_list(db, screen)

        day_list_ref = screen._lhos_day_list_ref
        assert day_list_ref.current is not None
        # Should have at least one entry
        assert len(day_list_ref.current.controls) > 0

    def test_init_history_list_no_op_without_handles(self, db: Database, caplog):
        screen = ft.Container()
        # Should not raise, just log a warning
        init_history_list(db, screen)
        assert "missing" in caplog.text.lower()
