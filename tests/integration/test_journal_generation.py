"""Integration tests for JournalEngine — full day lifecycle with journal generation.

Tests the complete workflow: create day → create tasks → work sessions →
breaks → complete tasks → generate journal → verify Markdown output.
"""

from __future__ import annotations

import time
from datetime import datetime, date

import pytest

from leadership_os.core.models import (
    Day, Task, WorkSession, BreakSession, Reflection, DailySummary,
)
from leadership_os.core.enums import TaskStatus, Priority, BreakType
from leadership_os.utils.path_utils import get_journal_path


class TestFullJournalWorkflow:
    """Test the complete journal generation workflow from a real day."""

    def test_full_day_journal_generation(
        self, journal_engine, tmp_dir, db, task_engine, timer_engine, break_engine
    ):
        """Simulate a full day and verify the generated journal."""
        # Override vault path to use temp directory for test isolation
        journal_engine.config.set("journaling", "vault_path", str(tmp_dir))
        journal_engine.config.set("journaling", "journal_dir", "Journals")

        day = db.create_day(Day(date="2026-07-15"))
        day.start_time = datetime.now().isoformat()
        db.update_day(day)

        # 1. Create tasks via task_engine
        task_a = task_engine.create_task(
            day.id, "Implement Journal Engine",
            priority=Priority.HIGH.value,
            estimated_minutes=120,
        )
        task_b = task_engine.create_task(
            day.id, "Write Unit Tests",
            priority=Priority.MEDIUM.value,
        )

        # 2. Activate and work on task A
        task_engine.activate_task(task_a.id)
        time.sleep(1.5)  # Simulate work — needs >1s for julianday to register

        # 3. Take a break
        break_session = break_engine.start_break(day.id, BreakType.LUNCH.value)
        time.sleep(1.0)  # Simulate break

        # 4. End break and resume
        break_engine.end_break(break_id=break_session.id)
        time.sleep(1.5)  # Simulate more work

        # 5. Complete task A
        task_engine.complete_task(task_a.id)
        time.sleep(1.0)  # Simulate work

        # 6. Activate and complete task B
        task_engine.activate_task(task_b.id)
        time.sleep(1.5)
        task_engine.complete_task(task_b.id)

        # 7. Record reflection
        reflection = Reflection(
            day_id=day.id,
            accomplishments="Implemented the journal engine end-to-end.",
            challenges="Timeline sorting needed careful ordering.",
            tomorrow_first="Add remaining UI screens.",
        )
        db.save_reflection(reflection)

        # 8. End the day
        day.end_time = datetime.now().isoformat()
        db.update_day(day)

        # 9. Generate journal
        summary = journal_engine.generate_journal(day.id)

        # 10. Verify summary
        assert summary is not None
        assert summary.day_id == day.id
        assert summary.completed >= 2
        # Each work sleep (~1.5s) yields ~1s recorded due to julianday CAST truncation.
        # 3 work sessions × 1s minimum = >= 3 seconds expected.
        assert summary.total_focus_seconds >= 3

        # 11. Verify the generated file exists and has correct content
        full_path = tmp_dir / "Journals" / "2026-07-15.md"
        assert full_path.exists()

        content = full_path.read_text(encoding="utf-8")

        # Verify core sections exist
        assert "# Wednesday, July 15, 2026" in content
        assert "## Summary" in content
        assert "## Completed" in content
        assert "## Timeline" in content
        assert "## Work Statistics" in content
        assert "## Reflection" in content
        assert "## Tomorrow" in content

        # Verify both tasks appear
        assert "Implement Journal Engine" in content
        assert "Write Unit Tests" in content

        # Verify reflection content
        assert "Implemented the journal engine end-to-end." in content
        assert "Timeline sorting needed careful ordering." in content
        assert "Add remaining UI screens." in content

        # Verify summary stored in DB
        stored = db.get_summary(day.id)
        assert stored is not None
        assert stored.journal_rel_path == summary.journal_rel_path
        assert stored.completed == 2

    def test_journal_with_incomplete_tasks(
        self, journal_engine, tmp_dir, db, task_engine
    ):
        """Test journal generation when some tasks are incomplete."""
        # Override vault path to use temp directory for test isolation
        journal_engine.config.set("journaling", "vault_path", str(tmp_dir))
        journal_engine.config.set("journaling", "journal_dir", "Journals")

        day = db.create_day(Day(date="2026-07-15"))

        # Create tasks but don't complete all
        task_a = task_engine.create_task(day.id, "Finished Task", priority=Priority.HIGH.value)
        task_b = task_engine.create_task(day.id, "Unfinished Task", priority=Priority.MEDIUM.value)

        # Complete only task A
        task_engine.activate_task(task_a.id)
        task_engine.complete_task(task_a.id)

        # Generate journal
        summary = journal_engine.generate_journal(day.id)

        full_path = tmp_dir / "Journals" / "2026-07-15.md"
        content = full_path.read_text(encoding="utf-8")

        # Verify both tasks appear in appropriate sections
        assert "Finished Task" in content
        assert "Unfinished Task" in content
        assert "## Incomplete" in content

    def test_journal_multiple_sessions(
        self, journal_engine, tmp_dir, db, task_engine, timer_engine, break_engine
    ):
        """Test journal with multiple work sessions per task."""
        # Override vault path to use temp directory for test isolation
        journal_engine.config.set("journaling", "vault_path", str(tmp_dir))
        journal_engine.config.set("journaling", "journal_dir", "Journals")

        day = db.create_day(Day(date="2026-07-15"))

        task = task_engine.create_task(day.id, "Interrupted Task", priority=Priority.HIGH.value)

        # Work → break → work → break → complete (3 sessions)
        task_engine.activate_task(task.id)
        time.sleep(1.0)

        b1 = break_engine.start_break(day.id, BreakType.TEA.value)
        time.sleep(1.0)
        break_engine.end_break(break_id=b1.id)
        time.sleep(1.0)

        b2 = break_engine.start_break(day.id, BreakType.PERSONAL.value)
        time.sleep(1.0)
        break_engine.end_break(break_id=b2.id)
        time.sleep(1.0)

        task_engine.complete_task(task.id)

        # Generate journal
        summary = journal_engine.generate_journal(day.id)

        full_path = tmp_dir / "Journals" / "2026-07-15.md"
        content = full_path.read_text(encoding="utf-8")

        # Verify timeline has multiple entries
        assert "Started **Interrupted Task**" in content
        assert "Tea break" in content
        assert "Paused **Interrupted Task**" in content
        assert "Resumed" in content
        assert "Work Statistics" in content
