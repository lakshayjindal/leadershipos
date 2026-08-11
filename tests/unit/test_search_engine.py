"""Tests for the global search engine (Phase 9c)."""

from __future__ import annotations

from datetime import date, timedelta

import pytest

from leadership_os.core.database import Database
from leadership_os.core.models import (
    Day,
    Task,
    WorkSession,
    BreakSession,
    Reflection,
    DailySummary,
)
from leadership_os.core.search_engine import (
    SearchEngine,
    SearchHit,
    format_seconds,
    highlight_segments,
    score_match,
)
from leadership_os.core.enums import Priority, BreakType


# ─── Fixtures / Helpers ───────────────────────────────────────────────


def _make_day(db: Database, date_str: str) -> Day:
    """Create a day with a specific date."""
    from datetime import datetime
    now = datetime.now().isoformat()
    day = Day(date=date_str, created_at=now, updated_at=now)
    return db.create_day(day)


def _make_task(db: Database, day: Day, title: str, **kwargs) -> Task:
    task = Task(day_id=day.id, title=title, **kwargs)
    return db.create_task(task)


@pytest.fixture
def search_engine(db: Database, config):
    return SearchEngine(db, config)


# ─── score_match ──────────────────────────────────────────────────────


class TestScoreMatch:
    def test_exact_title_match_scores_highest(self):
        assert score_match("timer", "timer", is_title=True) > score_match("timer", "a timer thing", is_title=True)

    def test_prefix_beats_substring(self):
        assert score_match("tim", "timer", is_title=True) > score_match("tim", "estimator", is_title=True)

    def test_case_insensitive(self):
        assert score_match("TIMER", "Timer Engine") > 0

    def test_no_match_returns_zero(self):
        assert score_match("xyz", "timer") == 0

    def test_empty_query_returns_zero(self):
        assert score_match("", "anything") == 0

    def test_title_field_gets_boost(self):
        assert score_match("timer", "timer engine", is_title=True) > score_match("timer", "timer engine", is_title=False)


# ─── highlight_segments ───────────────────────────────────────────────


class TestHighlightSegments:
    def test_single_match(self):
        segs = highlight_segments("Implement Timer Engine", "timer")
        assert ("Timer", True) in segs
        joined = "".join(s for s, _ in segs)
        assert joined == "Implement Timer Engine"

    def test_case_insensitive_highlight(self):
        segs = highlight_segments("TIMER ENGINE", "timer")
        assert ("TIMER", True) in segs

    def test_no_match_returns_single_false_segment(self):
        assert highlight_segments("hello", "xyz") == [("hello", False)]

    def test_empty_query(self):
        assert highlight_segments("hello", "") == [("hello", False)]


# ─── format_seconds ───────────────────────────────────────────────────


class TestFormatSeconds:
    def test_hours(self):
        assert format_seconds(3725) == "1h 02m"

    def test_minutes(self):
        assert format_seconds(1500) == "25m"

    def test_seconds_only(self):
        assert format_seconds(45) == "45s"

    def test_zero(self):
        assert format_seconds(0) == "0m"


# ─── DB Search Methods ────────────────────────────────────────────────


class TestDatabaseSearch:
    def test_search_tasks_finds_title_across_days(self, db: Database):
        d1 = _make_day(db, "2026-07-01")
        d2 = _make_day(db, "2026-07-02")
        _make_task(db, d1, "Implement Timer Engine")
        _make_task(db, d2, "Write Documentation")

        results = db.search_tasks("timer")
        assert len(results) == 1
        task, day = results[0]
        assert task.title == "Implement Timer Engine"
        assert day.date == "2026-07-01"

    def test_search_tasks_matches_description_and_notes(self, db: Database):
        day = _make_day(db, "2026-07-01")
        _make_task(db, day, "Task Alpha", description="focused work on the overlay window")
        _make_task(db, day, "Task Beta", notes="mentions the notification system")

        assert len(db.search_tasks("overlay")) == 1
        assert len(db.search_tasks("notification")) == 1

    def test_search_tasks_case_insensitive(self, db: Database):
        day = _make_day(db, "2026-07-01")
        _make_task(db, day, "FOCUS TIMER")
        assert len(db.search_tasks("timer")) == 1
        assert len(db.search_tasks("FOCUS")) == 1

    def test_search_tasks_no_match(self, db: Database):
        day = _make_day(db, "2026-07-01")
        _make_task(db, day, "Task Alpha")
        assert db.search_tasks("nonexistent") == []

    def test_search_tasks_limit(self, db: Database):
        day = _make_day(db, "2026-07-01")
        for i in range(5):
            _make_task(db, day, f"Shared Keyword Task {i}")
        assert len(db.search_tasks("keyword", limit=3)) == 3

    def test_search_reflections_finds_content(self, db: Database):
        day = _make_day(db, "2026-07-01")
        reflection = Reflection(
            day_id=day.id,
            accomplishments="Shipped the search feature",
            challenges="",
        )
        db.save_reflection(reflection)

        results = db.search_reflections("search feature")
        assert len(results) == 1
        refl, day_found, summary = results[0]
        assert refl.id == reflection.id
        assert day_found.date == "2026-07-01"
        assert summary is None

    def test_search_reflections_with_summary(self, db: Database):
        day = _make_day(db, "2026-07-01")
        db.save_reflection(Reflection(day_id=day.id, accomplishments="Wrote journal about focus"))
        summary = DailySummary(day_id=day.id, journal_rel_path="Daily Notes/2026-07-01.md")
        db.save_summary(summary)

        results = db.search_reflections("journal")
        assert len(results) == 1
        _, _, found_summary = results[0]
        assert found_summary is not None
        assert found_summary.journal_rel_path == "Daily Notes/2026-07-01.md"

    def test_search_work_sessions_by_task_title(self, db: Database):
        day = _make_day(db, "2026-07-01")
        task = _make_task(db, day, "Deep Work on Overlay")
        session = WorkSession(task_id=task.id, duration_seconds=1500)
        db.create_work_session(session)

        results = db.search_work_sessions("overlay")
        assert len(results) == 1
        found_session, found_task, found_day = results[0]
        assert found_session.id == session.id
        assert found_task.title == "Deep Work on Overlay"
        assert found_day.date == "2026-07-01"

    def test_search_break_sessions_by_type_and_notes(self, db: Database):
        day = _make_day(db, "2026-07-01")
        lunch = BreakSession(day_id=day.id, break_type=BreakType.LUNCH.value, notes="Ate at the park")
        db.create_break_session(lunch)

        assert len(db.search_break_sessions("lunch")) == 1
        assert len(db.search_break_sessions("park")) == 1
        assert db.search_break_sessions("dinner") == []


# ─── SearchEngine.search ──────────────────────────────────────────────


class TestSearchEngine:
    def test_empty_query_returns_empty(self, search_engine):
        assert search_engine.search("") == []
        assert search_engine.search("   ") == []

    def test_search_returns_grouped_hits(self, db: Database, search_engine):
        day = _make_day(db, "2026-07-01")
        task = _make_task(db, day, "Implement Timer Engine")
        db.create_work_session(WorkSession(task_id=task.id, duration_seconds=600))
        db.save_reflection(Reflection(day_id=day.id, accomplishments="Built the timer module"))

        hits = search_engine.search("timer")
        categories = {h.category for h in hits}
        assert "task" in categories
        assert "journal" in categories
        assert "session" in categories

    def test_search_orders_tasks_before_journals(self, db: Database, search_engine):
        day = _make_day(db, "2026-07-01")
        _make_task(db, day, "Timer Task")
        db.save_reflection(Reflection(day_id=day.id, accomplishments="Timer reflection"))

        hits = search_engine.search("timer")
        assert hits[0].category == "task"

    def test_search_ranks_exact_title_first(self, db: Database, search_engine):
        day = _make_day(db, "2026-07-01")
        _make_task(db, day, "Overlay Window")
        _make_task(db, day, "Improve the overlay UX")

        hits = search_engine.search_tasks("overlay")
        assert hits[0].title == "Overlay Window"

    def test_search_tasks_excludes_non_matching(self, db: Database, search_engine):
        day = _make_day(db, "2026-07-01")
        _make_task(db, day, "Write Documentation")
        assert search_engine.search_tasks("timer") == []

    def test_search_tasks_limit(self, db: Database, search_engine):
        day = _make_day(db, "2026-07-01")
        for i in range(10):
            _make_task(db, day, f"Searchable Task {i}")
        hits = search_engine.search_tasks("searchable", limit=4)
        assert len(hits) <= 4

    def test_search_journals_finds_day_by_date(self, db: Database, search_engine):
        _make_day(db, "2026-07-15")
        hits = search_engine.search_journals("2026-07-15")
        assert any(h.title == "Day — 2026-07-15" for h in hits)

    def test_search_sessions_breaks(self, db: Database, search_engine):
        day = _make_day(db, "2026-07-01")
        db.create_break_session(BreakSession(day_id=day.id, break_type=BreakType.DINNER.value))
        hits = search_engine.search_sessions("dinner")
        assert len(hits) == 1
        assert hits[0].category == "session"
        assert "Break" in hits[0].title

    def test_search_hit_has_navigation_data(self, db: Database, search_engine):
        day = _make_day(db, "2026-07-01")
        task = _make_task(db, day, "Navigation Target")
        hits = search_engine.search_tasks("navigation")
        assert len(hits) == 1
        hit = hits[0]
        assert hit.id == task.id
        assert hit.day_id == day.id
        assert hit.date == "2026-07-01"

    def test_recency_boost_newer_days(self, db: Database, search_engine):
        old = _make_day(db, "2020-01-01")
        recent = _make_day(db, date.today().isoformat())
        _make_task(db, old, "Overlay Window")
        _make_task(db, recent, "Overlay Window")

        hits = search_engine.search_tasks("overlay")
        assert hits[0].date == recent.date


# ─── Recent Searches ──────────────────────────────────────────────────


class TestRecentSearches:
    def test_add_and_get(self, search_engine):
        search_engine.add_recent_search("timer")
        search_engine.add_recent_search("journal")
        assert search_engine.get_recent_searches() == ["journal", "timer"]

    def test_most_recent_first_and_dedup(self, search_engine):
        search_engine.add_recent_search("timer")
        search_engine.add_recent_search("timer")
        assert search_engine.get_recent_searches() == ["timer"]

    def test_clear(self, search_engine):
        search_engine.add_recent_search("timer")
        search_engine.clear_recent_searches()
        assert search_engine.get_recent_searches() == []

    def test_empty_query_not_recorded(self, search_engine):
        search_engine.add_recent_search("   ")
        assert search_engine.get_recent_searches() == []

    def test_capped_by_config(self, db: Database, config):
        config.set("search", "max_recent_searches", 3)
        engine = SearchEngine(db, config)
        for term in ("a", "b", "c", "d", "e"):
            engine.add_recent_search(term)
        assert len(engine.get_recent_searches(max_count=10)) == 3
        assert engine.get_recent_searches(max_count=10) == ["e", "d", "c"]

    def test_no_config_returns_empty(self, db: Database):
        engine = SearchEngine(db, config=None)
        engine.add_recent_search("timer")  # should be a no-op
        assert engine.get_recent_searches() == []


# ─── Command Palette Integration ──────────────────────────────────────


class TestPaletteWithSearchEngine:
    def test_palette_builds_with_search_engine(self, db: Database, config, task_engine):
        import flet as ft
        from leadership_os.ui.widgets.command_palette import build_command_palette
        from leadership_os.core.search_engine import SearchEngine

        engine = SearchEngine(db, config)
        palette = build_command_palette(
            task_engine,
            on_search_task=lambda tid: None,
            on_run_command=lambda cmd: None,
            on_close=lambda: None,
            search_engine=engine,
            on_open_day=lambda day_id: None,
        )
        assert isinstance(palette, ft.Container)

    def test_highlight_spans_util(self):
        from leadership_os.core.search_engine import highlight_segments
        segs = highlight_segments("Timer Engine", "timer")
        assert any(is_match for _, is_match in segs)
