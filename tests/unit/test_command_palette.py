"""Tests for the command palette."""

from __future__ import annotations

import flet as ft

from leadership_os.core.task_engine import TaskEngine
from leadership_os.ui.widgets.command_palette import _fuzzy_match, build_command_palette


class TestFuzzyMatch:
    def test_empty_query_matches_anything(self):
        assert _fuzzy_match("", "anything") is True

    def test_exact_match(self):
        assert _fuzzy_match("start", "start break") is True

    def test_fuzzy_match(self):
        assert _fuzzy_match("stbk", "start break") is True

    def test_case_insensitive(self):
        assert _fuzzy_match("START", "Start Break") is True

    def test_no_match(self):
        assert _fuzzy_match("xyz", "start break") is False

    def test_out_of_order_fails(self):
        assert _fuzzy_match("bkst", "start break") is False


class TestBuildCommandPalette:
    def test_palette_builds_without_error(self, task_engine: TaskEngine):
        # Build the palette overlay without a real page context
        palette = build_command_palette(
            task_engine,
            on_search_task=lambda tid: None,
            on_run_command=lambda cmd: None,
            on_close=lambda: None,
        )
        assert isinstance(palette, ft.Container)
        assert palette.expand is True
