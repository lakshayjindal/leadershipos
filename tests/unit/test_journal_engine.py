"""Unit tests for JournalEngine — Markdown journal generation."""

from __future__ import annotations

from datetime import datetime, date, timedelta

import pytest

from leadership_os.core.journal_engine import JournalEngine
from leadership_os.core.models import (
    Day, Task, WorkSession, BreakSession, Reflection, DailySummary,
)
from leadership_os.core.enums import TaskStatus, Priority, BreakType


class TestJournalGeneration:
    """Test the full journal generation flow."""

    def test_generate_journal_creates_file(
        self, journal_engine: JournalEngine, db, sample_day: Day, sample_task: Task
    ):
        """Test that generate_journal creates a Markdown file on disk."""
        # Set a fixed date on the day for predictable output
        sample_day.date = "2026-07-15"
        sample_day.start_time = "2026-07-15T09:05:00"
        sample_day.end_time = "2026-07-15T21:12:00"
        db.update_day(sample_day)

        # Complete the task so we have data
        sample_task.status = TaskStatus.COMPLETED.value
        sample_task.completed_at = "2026-07-15T14:30:00"
        sample_task.actual_seconds = 7200
        db.update_task(sample_task)

        summary = journal_engine.generate_journal(sample_day.id)

        # Verify summary was created
        assert summary is not None
        assert summary.day_id == sample_day.id
        assert summary.journal_rel_path != ""
        assert "2026-07-15.md" in summary.journal_rel_path
        assert summary.total_focus_seconds >= 0
        assert summary.completed >= 1

    def test_generate_journal_invalid_day(
        self, journal_engine: JournalEngine
    ):
        """Test that generating for a non-existent day raises ValueError."""
        with pytest.raises(ValueError, match="Day not found"):
            journal_engine.generate_journal("nonexistent-day-id")


class TestJournalContent:
    """Test the Markdown content structure of generated journals."""

    def test_journal_has_all_sections(
        self, journal_engine: JournalEngine, db, sample_day: Day
    ):
        """Test that the generated Markdown contains all expected sections."""
        sample_day.date = "2026-07-15"
        sample_day.start_time = "2026-07-15T09:00:00"
        sample_day.end_time = "2026-07-15T17:30:00"
        db.update_day(sample_day)

        # Create a completed task with sessions
        task = Task(
            day_id=sample_day.id,
            title="Implement Journal Engine",
            priority=Priority.HIGH.value,
            status=TaskStatus.COMPLETED.value,
            completed_at="2026-07-15T14:30:00",
            notes="Worked through the design carefully.",
        )
        task = db.create_task(task)

        session = WorkSession(
            task_id=task.id,
            start_time="2026-07-15T09:05:00",
            end_time="2026-07-15T10:30:00",
            duration_seconds=5100,
        )
        db.create_work_session(session)

        # Create a reflection
        reflection = Reflection(
            day_id=sample_day.id,
            accomplishments="Built the full journal engine",
            challenges="Timeline sorting was tricky",
            tomorrow_first="Write integration tests",
        )
        db.save_reflection(reflection)

        summary = journal_engine.generate_journal(sample_day.id)

        # Read the generated file back
        vault_path = journal_engine._get_vault_path()
        journal_dir = journal_engine._get_journal_dir()
        from leadership_os.utils.path_utils import get_journal_path
        full_path = get_journal_path(vault_path, journal_dir, sample_day.date)
        content = full_path.read_text(encoding="utf-8")

        # Verify all expected sections exist
        assert "# Wednesday, July 15, 2026" in content
        assert "## Summary" in content
        assert "## Completed" in content
        assert "## Incomplete" in content
        assert "## Timeline" in content
        assert "## Work Statistics" in content
        assert "## Reflection" in content
        assert "## Tomorrow" in content

        # Verify task appears
        assert "Implement Journal Engine" in content

        # Verify reflection content
        assert "Built the full journal engine" in content
        assert "Timeline sorting was tricky" in content
        assert "Write integration tests" in content

        # Verify notes appear
        assert "Worked through the design carefully." in content

        # Verify summary was persisted
        stored = db.get_summary(sample_day.id)
        assert stored is not None
        assert stored.journal_rel_path == summary.journal_rel_path

    def test_journal_empty_day(
        self, journal_engine: JournalEngine, db, sample_day: Day
    ):
        """Test that a day with no tasks still generates a valid journal."""
        sample_day.date = "2026-07-15"
        db.update_day(sample_day)

        summary = journal_engine.generate_journal(sample_day.id)
        assert summary is not None

        vault_path = journal_engine._get_vault_path()
        journal_dir = journal_engine._get_journal_dir()
        from leadership_os.utils.path_utils import get_journal_path
        full_path = get_journal_path(vault_path, journal_dir, sample_day.date)
        content = full_path.read_text(encoding="utf-8")

        assert "# Wednesday, July 15, 2026" in content
        assert "No tasks completed" in content or "Summary" in content


class TestJournalSections:
    """Test individual journal section builders."""

    def test_build_header(self, journal_engine: JournalEngine):
        """Test header generation with start/end times."""
        day = Day(date="2026-07-15", start_time="2026-07-15T09:05:00", end_time="2026-07-15T21:12:00")
        header = journal_engine._build_header(day)

        assert "# Wednesday, July 15, 2026" in header
        assert "**Started:** 09:05" in header
        assert "**Finished:** 21:12" in header

    def test_build_header_no_times(self, journal_engine: JournalEngine):
        """Test header generation without start/end times."""
        day = Day(date="2026-07-15")
        header = journal_engine._build_header(day)

        assert "# Wednesday, July 15, 2026" in header
        assert "**Started:** Not started" in header
        assert "**Finished:** Not finished" in header

    def test_build_summary(self, journal_engine: JournalEngine):
        """Test summary section with various task statuses."""
        tasks = [
            Task(day_id="d1", title="Task A", status=TaskStatus.COMPLETED.value),
            Task(day_id="d1", title="Task B", status=TaskStatus.COMPLETED.value),
            Task(day_id="d1", title="Task C", status=TaskStatus.PENDING.value),
            Task(day_id="d1", title="Task D", status=TaskStatus.CARRIED_FORWARD.value),
        ]

        summary = journal_engine._build_summary(
            tasks, focus_seconds=7500, break_seconds=1800, completion_pct=50.0
        )

        assert "## Summary" in summary
        assert "**Planned Tasks:** 4" in summary
        assert "**Completed:** 2 (50%)" in summary
        assert "**Incomplete:** 1" in summary
        assert "**Carried Forward:** 1" in summary
        assert "**Focus Time:** 2h 5m" in summary
        assert "**Break Time:** 30m" in summary
        assert "---" in summary

    def test_build_completed_tasks(self, journal_engine: JournalEngine):
        """Test completed tasks section."""
        tasks = [
            Task(
                day_id="d1", title="Done Task",
                status=TaskStatus.COMPLETED.value,
                completed_at="2026-07-15T14:30:00",
                notes="Great work!",
            ),
            Task(
                day_id="d1", title="Another Done",
                status=TaskStatus.COMPLETED.value,
                completed_at="2026-07-15T16:00:00",
            ),
        ]
        all_sessions = [
            WorkSession(task_id=tasks[0].id, start_time="09:00", end_time="14:30", duration_seconds=7200),
            WorkSession(task_id=tasks[1].id, start_time="15:00", end_time="16:00", duration_seconds=3600),
        ]

        result = journal_engine._build_completed_tasks(tasks, all_sessions)

        assert "## Completed" in result
        # 7200s = 2h exactly, formatted as "2h"
        assert "- [x] **Done Task** (2h)" in result
        assert "> Great work!" in result
        assert "- [x] **Another Done** (1h)" in result

    def test_build_completed_tasks_empty(self, journal_engine: JournalEngine):
        """Test completed tasks section with no completed tasks."""
        tasks = [Task(day_id="d1", title="Pending Task", status=TaskStatus.PENDING.value)]
        result = journal_engine._build_completed_tasks(tasks, [])

        assert "## Completed" in result
        assert "No tasks completed" in result

    def test_build_incomplete_tasks(self, journal_engine: JournalEngine):
        """Test incomplete tasks section (excludes carried-forward tasks)."""
        tasks = [
            Task(day_id="d1", title="Pending A", status=TaskStatus.PENDING.value, priority=Priority.HIGH.value),
            Task(day_id="d1", title="Paused B", status=TaskStatus.PAUSED.value, priority=Priority.MEDIUM.value),
        ]

        result = journal_engine._build_incomplete_tasks(tasks)

        assert "## Incomplete" in result
        assert "- [ ] **Pending A" in result
        assert "- [ ] **Paused B" in result

    def test_build_incomplete_tasks_all_done(self, journal_engine: JournalEngine):
        """Test incomplete section when all tasks are completed."""
        tasks = [Task(day_id="d1", title="Done", status=TaskStatus.COMPLETED.value)]
        result = journal_engine._build_incomplete_tasks(tasks)

        assert "All tasks completed" in result

    def test_build_timeline(self, journal_engine: JournalEngine):
        """Test timeline generation from sessions and breaks."""
        all_sessions = [
            WorkSession(
                task_id="t1", start_time="2026-07-15T09:05:00",
                end_time="2026-07-15T10:30:00",
            ),
            WorkSession(
                task_id="t1", start_time="2026-07-15T11:00:00",
                end_time="2026-07-15T12:30:00",
            ),
        ]
        break_sessions = [
            BreakSession(
                day_id="d1", break_type=BreakType.LUNCH.value,
                start_time="2026-07-15T12:30:00",
                end_time="2026-07-15T13:30:00",
            ),
        ]
        tasks = [Task(day_id="d1", id="t1", title="Main Work")]

        result = journal_engine._build_timeline(all_sessions, break_sessions, tasks)

        assert "## Timeline" in result
        assert "Started **Main Work**" in result
        assert "Paused **Main Work**" in result
        assert "Lunch break" in result
        assert "Resumed" in result

    def test_build_timeline_completed_label(self, journal_engine: JournalEngine):
        """Test that the last session of a completed task shows 'Completed' not 'Paused'."""
        # The final session end_time matches completed_at
        all_sessions = [
            WorkSession(
                task_id="t1", start_time="2026-07-15T09:00:00",
                end_time="2026-07-15T10:00:00",
            ),
            WorkSession(
                task_id="t1", start_time="2026-07-15T11:00:00",
                end_time="2026-07-15T12:30:00",
            ),
        ]
        break_sessions: list[BreakSession] = []
        tasks = [
            Task(
                day_id="d1", id="t1", title="Main Work",
                status=TaskStatus.COMPLETED.value,
                completed_at="2026-07-15T12:30:00",
            )
        ]

        result = journal_engine._build_timeline(all_sessions, break_sessions, tasks)

        assert "Completed **Main Work**" in result
        assert "Paused **Main Work**" in result
        assert "Started **Main Work**" in result

    def test_build_timeline_no_events(self, journal_engine: JournalEngine):
        """Test timeline with no events."""
        result = journal_engine._build_timeline([], [], [])
        assert "No events recorded" in result

    def test_build_statistics(self, journal_engine: JournalEngine):
        """Test work statistics section."""
        result = journal_engine._build_statistics(
            focus_seconds=14400,
            break_seconds=3600,
            total_tasks=5,
            completed_tasks=3,
            session_count=6,
            longest_session=5400,
            completion_pct=60.0,
        )

        assert "## Work Statistics" in result
        assert "**Total Focus Time:** 4h" in result
        assert "**Total Break Time:** 1h" in result
        assert "**Total Tasks:** 5" in result
        assert "**Completed:** 3" in result
        assert "**Work Sessions:** 6" in result
        assert "**Longest Session:** 1h 30m" in result
        assert "**Average Session:** 40m" in result
        assert "**Completion:** 60%" in result

    def test_build_reflection(self, journal_engine: JournalEngine):
        """Test reflection section with user answers."""
        reflection = Reflection(
            day_id="d1",
            accomplishments="Finished the project.",
            challenges="Integration was complex.",
            tomorrow_first="Write tests.",
        )
        result = journal_engine._build_reflection(reflection)

        assert "## Reflection" in result
        assert "### What did you accomplish today?" in result
        assert "Finished the project." in result
        assert "### What slowed you down?" in result
        assert "Integration was complex." in result
        assert "### What should you do first tomorrow?" in result
        assert "Write tests." in result

    def test_build_reflection_no_content(self, journal_engine: JournalEngine):
        """Test reflection section with no reflection data and no content."""
        reflection = Reflection(day_id="d1")
        result = journal_engine._build_reflection(reflection)
        assert "No reflection recorded" in result

    def test_build_reflection_none(self, journal_engine: JournalEngine):
        """Test reflection section with None reflection."""
        result = journal_engine._build_reflection(None)
        assert "No reflection recorded" in result

    def test_build_tomorrow(self, journal_engine: JournalEngine):
        """Test tomorrow section with pending tasks."""
        tasks = [
            Task(day_id="d1", title="First Task", status=TaskStatus.PENDING.value, display_order=10),
            Task(day_id="d1", title="Second Task", status=TaskStatus.PENDING.value, display_order=20),
        ]
        result = journal_engine._build_tomorrow(tasks)

        assert "## Tomorrow" in result
        assert "Start with **First Task**." in result

    def test_build_tomorrow_all_done(self, journal_engine: JournalEngine):
        """Test tomorrow section when all tasks are complete."""
        tasks = [Task(day_id="d1", title="Done", status=TaskStatus.COMPLETED.value)]
        result = journal_engine._build_tomorrow(tasks)

        assert "No pending tasks for tomorrow" in result

    def test_build_tomorrow_with_carried(self, journal_engine: JournalEngine):
        """Test tomorrow with carried-forward tasks."""
        tasks = [
            Task(day_id="d1", title="Carried Task", status=TaskStatus.CARRIED_FORWARD.value),
        ]
        result = journal_engine._build_tomorrow(tasks)

        assert "No pending tasks for tomorrow" in result


class TestJournalHelpers:
    """Test journal engine helper methods."""

    def test_format_time_iso(self, journal_engine: JournalEngine):
        """Test formatting ISO timestamps to HH:MM."""
        result = journal_engine._format_time("2026-07-15T09:05:00")
        assert result == "09:05"

    def test_format_time_none(self, journal_engine: JournalEngine):
        """Test formatting None time."""
        result = journal_engine._format_time(None)
        assert result == "--:--"

    def test_format_time_custom_fallback(self, journal_engine: JournalEngine):
        """Test formatting with custom fallback."""
        result = journal_engine._format_time(None, "TBD")
        assert result == "TBD"

    def test_format_duration_human_seconds(self, journal_engine: JournalEngine):
        """Test duration formatting for seconds-only."""
        assert journal_engine._format_duration_human(45) == "0m"
        assert journal_engine._format_duration_human(120) == "2m"

    def test_format_duration_human_minutes(self, journal_engine: JournalEngine):
        """Test duration formatting for minutes."""
        assert journal_engine._format_duration_human(300) == "5m"
        assert journal_engine._format_duration_human(3540) == "59m"

    def test_format_duration_human_hours(self, journal_engine: JournalEngine):
        """Test duration formatting for hours."""
        assert journal_engine._format_duration_human(3600) == "1h"
        assert journal_engine._format_duration_human(7200) == "2h"

    def test_format_duration_human_hours_minutes(self, journal_engine: JournalEngine):
        """Test duration formatting for hours and minutes."""
        assert journal_engine._format_duration_human(3660) == "1h 1m"
        assert journal_engine._format_duration_human(7500) == "2h 5m"

    def test_format_duration_human_zero(self, journal_engine: JournalEngine):
        """Test duration formatting for zero."""
        assert journal_engine._format_duration_human(0) == "0m"
        assert journal_engine._format_duration_human(-5) == "0m"

    def test_calculate_completion(self, journal_engine: JournalEngine):
        """Test completion percentage calculation."""
        tasks = [
            Task(day_id="d1", title="A", status=TaskStatus.COMPLETED.value),
            Task(day_id="d1", title="B", status=TaskStatus.COMPLETED.value),
            Task(day_id="d1", title="C", status=TaskStatus.PENDING.value),
            Task(day_id="d1", title="D", status=TaskStatus.PENDING.value),
        ]
        pct = journal_engine._calculate_completion(tasks)
        assert pct == 50.0

    def test_calculate_completion_empty(self, journal_engine: JournalEngine):
        """Test completion percentage with no tasks."""
        assert journal_engine._calculate_completion([]) == 0.0

    def test_calculate_completion_all_done(self, journal_engine: JournalEngine):
        """Test completion percentage with all tasks done."""
        tasks = [
            Task(day_id="d1", title="A", status=TaskStatus.COMPLETED.value),
            Task(day_id="d1", title="B", status=TaskStatus.COMPLETED.value),
        ]
        assert journal_engine._calculate_completion(tasks) == 100.0
