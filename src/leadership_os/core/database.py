"""SQLite database layer for Leadership OS.

Responsibilities:
- Schema creation and migration
- CRUD operations for all entities
- Query helpers for common operations
- Database integrity checks

Design principle: The database hides storage implementation details
from the rest of the application.
"""

from __future__ import annotations

import logging
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Generator

from leadership_os.core.enums import TaskStatus, DayStatus
from leadership_os.core.models import (
    Day,
    Task,
    WorkSession,
    BreakSession,
    Reflection,
    DailySummary,
)

logger = logging.getLogger(__name__)

# ─── Schema ───────────────────────────────────────────────────────────

SCHEMA_VERSION = 1

SCHEMA_SQL = """
-- Schema version for migration tracking
CREATE TABLE IF NOT EXISTS schema_version (
    version INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS days (
    id TEXT PRIMARY KEY,
    date TEXT NOT NULL UNIQUE,
    start_time TEXT,
    end_time TEXT,
    status TEXT NOT NULL DEFAULT 'active',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS tasks (
    id TEXT PRIMARY KEY,
    day_id TEXT NOT NULL,
    title TEXT NOT NULL,
    description TEXT DEFAULT '',
    priority TEXT NOT NULL DEFAULT 'medium',
    status TEXT NOT NULL DEFAULT 'pending',
    deadline TEXT,
    estimated_minutes INTEGER,
    actual_seconds INTEGER DEFAULT 0,
    created_at TEXT NOT NULL,
    activated_at TEXT,
    completed_at TEXT,
    display_order INTEGER DEFAULT 0,
    notes TEXT DEFAULT '',
    FOREIGN KEY (day_id) REFERENCES days(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS work_sessions (
    id TEXT PRIMARY KEY,
    task_id TEXT NOT NULL,
    start_time TEXT NOT NULL,
    end_time TEXT,
    duration_seconds INTEGER DEFAULT 0,
    created_at TEXT NOT NULL,
    FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS break_sessions (
    id TEXT PRIMARY KEY,
    day_id TEXT NOT NULL,
    break_type TEXT NOT NULL,
    start_time TEXT NOT NULL,
    end_time TEXT,
    duration_seconds INTEGER DEFAULT 0,
    notes TEXT DEFAULT '',
    FOREIGN KEY (day_id) REFERENCES days(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS reflections (
    id TEXT PRIMARY KEY,
    day_id TEXT NOT NULL UNIQUE,
    accomplishments TEXT DEFAULT '',
    challenges TEXT DEFAULT '',
    tomorrow_first TEXT DEFAULT '',
    additional_notes TEXT DEFAULT '',
    created_at TEXT NOT NULL,
    FOREIGN KEY (day_id) REFERENCES days(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS daily_summaries (
    id TEXT PRIMARY KEY,
    day_id TEXT NOT NULL UNIQUE,
    total_planned INTEGER DEFAULT 0,
    completed INTEGER DEFAULT 0,
    carried_forward INTEGER DEFAULT 0,
    archived INTEGER DEFAULT 0,
    deleted INTEGER DEFAULT 0,
    total_focus_seconds INTEGER DEFAULT 0,
    total_break_seconds INTEGER DEFAULT 0,
    completion_percentage REAL DEFAULT 0.0,
    longest_session_seconds INTEGER DEFAULT 0,
    session_count INTEGER DEFAULT 0,
    journal_rel_path TEXT DEFAULT '',
    generated_at TEXT NOT NULL,
    FOREIGN KEY (day_id) REFERENCES days(id) ON DELETE CASCADE
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_tasks_day_id ON tasks(day_id);
CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);
CREATE INDEX IF NOT EXISTS idx_work_sessions_task_id ON work_sessions(task_id);
CREATE INDEX IF NOT EXISTS idx_break_sessions_day_id ON break_sessions(day_id);
CREATE INDEX IF NOT EXISTS idx_daily_summaries_day_id ON daily_summaries(day_id);
CREATE INDEX IF NOT EXISTS idx_reflections_day_id ON reflections(day_id);
"""


# ─── Database Manager ─────────────────────────────────────────────────


class Database:
    """SQLite database manager with thread-safe connection handling.

    Usage:
        db = Database(Path("data/leadership_os.db"))
        db.initialize()
        day = db.get_or_create_today()
    """

    # Column name sets for merging joined rows in search queries
    _DAY_COLUMNS = frozenset({"id", "date", "start_time", "end_time", "status", "created_at", "updated_at"})
    _TASK_COLUMNS = frozenset({
        "id", "day_id", "title", "description", "priority", "status", "deadline",
        "estimated_minutes", "actual_seconds", "created_at", "activated_at",
        "completed_at", "display_order", "notes",
    })
    _SESSION_COLUMNS = frozenset({"id", "task_id", "start_time", "end_time", "duration_seconds", "created_at"})
    _BREAK_COLUMNS = frozenset({"id", "day_id", "break_type", "start_time", "end_time", "duration_seconds", "notes"})
    _REFLECTION_COLUMNS = frozenset({
        "id", "day_id", "accomplishments", "challenges", "tomorrow_first",
        "additional_notes", "created_at",
    })
    _SUMMARY_COLUMNS = frozenset({
        "id", "day_id", "total_planned", "completed", "carried_forward", "archived",
        "deleted", "total_focus_seconds", "total_break_seconds", "completion_percentage",
        "longest_session_seconds", "session_count", "journal_rel_path", "generated_at",
    })

    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        self._conn: sqlite3.Connection | None = None

    def initialize(self) -> None:
        """Open connection and create schema if needed."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(
            str(self.db_path),
            check_same_thread=False,
            detect_types=sqlite3.PARSE_DECLTYPES,
        )
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("PRAGMA foreign_keys=ON")
        self._create_schema()
        logger.info("Database initialized: %s", self.db_path)

    def close(self) -> None:
        """Close database connection."""
        if self._conn:
            self._conn.close()
            self._conn = None

    @contextmanager
    def _cursor(self) -> Generator[sqlite3.Cursor, None, None]:
        """Provide a transactional cursor scope."""
        if self._conn is None:
            raise RuntimeError("Database not initialized")
        cursor = self._conn.cursor()
        try:
            yield cursor
            self._conn.commit()
        except Exception:
            self._conn.rollback()
            raise

    def _create_schema(self) -> None:
        """Create tables and indexes if they don't exist."""
        with self._cursor() as cursor:
            cursor.executescript(SCHEMA_SQL)
            # Insert schema version if not present
            cursor.execute(
                "INSERT OR IGNORE INTO schema_version (version) VALUES (?)",
                (SCHEMA_VERSION,),
            )

    # ─── Day Operations ───────────────────────────────────────────────

    def get_or_create_today(self) -> Day:
        """Get today's day record, or create it if it doesn't exist."""
        from datetime import date

        today = date.today().isoformat()
        with self._cursor() as cursor:
            cursor.execute("SELECT * FROM days WHERE date = ?", (today,))
            row = cursor.fetchone()
            if row:
                return self._row_to_day(row)

            from datetime import datetime
            now = datetime.now().isoformat()
            day = Day(date=today, created_at=now, updated_at=now)
            cursor.execute(
                """INSERT INTO days (id, date, start_time, end_time, status, created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (day.id, day.date, day.start_time, day.end_time, day.status, day.created_at, day.updated_at),
            )
            logger.info("Created day record for %s", today)
            return day

    def create_day(self, day: Day) -> Day:
        """Insert a new day record."""
        with self._cursor() as cursor:
            cursor.execute(
                """INSERT INTO days (id, date, start_time, end_time, status, created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (day.id, day.date, day.start_time, day.end_time, day.status, day.created_at, day.updated_at),
            )
        return day

    def get_day(self, day_id: str) -> Day | None:
        """Get a day record by its ID."""
        with self._cursor() as cursor:
            cursor.execute("SELECT * FROM days WHERE id = ?", (day_id,))
            row = cursor.fetchone()
            return self._row_to_day(row) if row else None

    def get_day_by_date(self, date_str: str) -> Day | None:
        """Get a day record by date string (YYYY-MM-DD)."""
        with self._cursor() as cursor:
            cursor.execute("SELECT * FROM days WHERE date = ?", (date_str,))
            row = cursor.fetchone()
            return self._row_to_day(row) if row else None

    def update_day(self, day: Day) -> None:
        """Update an existing day record."""
        with self._cursor() as cursor:
            cursor.execute(
                """UPDATE days SET start_time=?, end_time=?, status=?, updated_at=?
                   WHERE id=?""",
                (day.start_time, day.end_time, day.status, day.updated_at, day.id),
            )

    def get_previous_days(self, limit: int = 10) -> list[Day]:
        """Get previous days (not today) for history and carry-forward."""
        from datetime import date

        today = date.today().isoformat()
        with self._cursor() as cursor:
            cursor.execute(
                "SELECT * FROM days WHERE date < ? ORDER BY date DESC LIMIT ?",
                (today, limit),
            )
            return [self._row_to_day(row) for row in cursor.fetchall()]

    def end_day(self, day: Day) -> None:
        """Mark a day as completed and close any active sessions."""
        from datetime import datetime

        now = datetime.now().isoformat()
        with self._cursor() as cursor:
            # End any active work sessions
            cursor.execute(
                """UPDATE work_sessions SET end_time=?, duration_seconds=
                   CAST((julianday(?) - julianday(start_time)) * 86400 AS INTEGER)
                   WHERE end_time IS NULL""",
                (now, now),
            )
            # Update actual_seconds for tasks with ended sessions
            cursor.execute(
                """UPDATE tasks SET actual_seconds = (
                   SELECT COALESCE(SUM(duration_seconds), 0)
                   FROM work_sessions WHERE task_id = tasks.id AND end_time IS NOT NULL
                ) WHERE day_id = ?""",
                (day.id,),
            )
            # End any active break sessions
            cursor.execute(
                """UPDATE break_sessions SET end_time=?, duration_seconds=
                   CAST((julianday(?) - julianday(start_time)) * 86400 AS INTEGER)
                   WHERE end_time IS NULL""",
                (now, now),
            )
            # Update day
            day.end_time = now
            day.status = DayStatus.COMPLETED.value
            day.updated_at = now
            cursor.execute(
                """UPDATE days SET end_time=?, status=?, updated_at=? WHERE id=?""",
                (day.end_time, day.status, day.updated_at, day.id),
            )

    # ─── Task Operations ──────────────────────────────────────────────

    def create_task(self, task: Task) -> Task:
        """Insert a new task into the database."""
        with self._cursor() as cursor:
            cursor.execute(
                """INSERT INTO tasks
                   (id, day_id, title, description, priority, status, deadline,
                    estimated_minutes, actual_seconds, created_at, activated_at,
                    completed_at, display_order, notes)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    task.id, task.day_id, task.title, task.description,
                    task.priority, task.status, task.deadline,
                    task.estimated_minutes, task.actual_seconds,
                    task.created_at, task.activated_at, task.completed_at,
                    task.display_order, task.notes,
                ),
            )
            logger.info("Created task: %s", task.title)
            return task

    def get_task(self, task_id: str) -> Task | None:
        """Get a single task by ID."""
        with self._cursor() as cursor:
            cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
            row = cursor.fetchone()
            return self._row_to_task(row) if row else None

    def get_tasks_by_day(self, day_id: str) -> list[Task]:
        """Get all tasks for a given day, ordered by display_order then priority."""
        with self._cursor() as cursor:
            cursor.execute(
                """SELECT * FROM tasks WHERE day_id = ?
                   ORDER BY display_order ASC, 
                   CASE priority
                       WHEN 'critical' THEN 0
                       WHEN 'high' THEN 1
                       WHEN 'medium' THEN 2
                       WHEN 'low' THEN 3
                   END ASC""",
                (day_id,),
            )
            return [self._row_to_task(row) for row in cursor.fetchall()]

    def update_task(self, task: Task) -> None:
        """Update an existing task."""
        with self._cursor() as cursor:
            cursor.execute(
                """UPDATE tasks SET title=?, description=?, priority=?, status=?,
                   deadline=?, estimated_minutes=?, actual_seconds=?,
                   activated_at=?, completed_at=?, display_order=?, notes=?
                   WHERE id=?""",
                (
                    task.title, task.description, task.priority, task.status,
                    task.deadline, task.estimated_minutes, task.actual_seconds,
                    task.activated_at, task.completed_at, task.display_order,
                    task.notes, task.id,
                ),
            )

    def delete_task(self, task_id: str) -> None:
        """Permanently delete a task and its sessions."""
        with self._cursor() as cursor:
            cursor.execute("DELETE FROM work_sessions WHERE task_id = ?", (task_id,))
            cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
            logger.info("Deleted task: %s", task_id)

    def get_active_task(self, day_id: str) -> Task | None:
        """Get the currently active task for a day (at most one)."""
        with self._cursor() as cursor:
            cursor.execute(
                "SELECT * FROM tasks WHERE day_id = ? AND status = ?",
                (day_id, TaskStatus.ACTIVE.value),
            )
            row = cursor.fetchone()
            return self._row_to_task(row) if row else None

    def get_next_pending_task(self, day_id: str) -> Task | None:
        """Get the next pending task (by display_order then priority)."""
        with self._cursor() as cursor:
            cursor.execute(
                """SELECT * FROM tasks WHERE day_id = ? AND status = ?
                   ORDER BY display_order ASC,
                   CASE priority
                       WHEN 'critical' THEN 0
                       WHEN 'high' THEN 1
                       WHEN 'medium' THEN 2
                       WHEN 'low' THEN 3
                   END ASC
                   LIMIT 1""",
                (day_id, TaskStatus.PENDING.value),
            )
            row = cursor.fetchone()
            return self._row_to_task(row) if row else None

    def set_task_status(self, task_id: str, status: str) -> None:
        """Update only the status of a task."""
        with self._cursor() as cursor:
            cursor.execute(
                "UPDATE tasks SET status = ? WHERE id = ?",
                (status, task_id),
            )

    # ─── Work Session Operations ──────────────────────────────────────

    def create_work_session(self, session: WorkSession) -> WorkSession:
        """Insert a new work session."""
        with self._cursor() as cursor:
            cursor.execute(
                """INSERT INTO work_sessions
                   (id, task_id, start_time, end_time, duration_seconds, created_at)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (
                    session.id, session.task_id, session.start_time,
                    session.end_time, session.duration_seconds, session.created_at,
                ),
            )
            return session

    def get_active_session(self, task_id: str) -> WorkSession | None:
        """Get the currently running work session for a task."""
        with self._cursor() as cursor:
            cursor.execute(
                "SELECT * FROM work_sessions WHERE task_id = ? AND end_time IS NULL",
                (task_id,),
            )
            row = cursor.fetchone()
            return self._row_to_work_session(row) if row else None

    def get_sessions_by_task(self, task_id: str) -> list[WorkSession]:
        """Get all work sessions for a task."""
        with self._cursor() as cursor:
            cursor.execute(
                "SELECT * FROM work_sessions WHERE task_id = ? ORDER BY start_time",
                (task_id,),
            )
            return [self._row_to_work_session(row) for row in cursor.fetchall()]

    def end_work_session(self, session_id: str) -> WorkSession | None:
        """End a running work session and return the updated session."""
        from datetime import datetime

        now = datetime.now().isoformat()
        with self._cursor() as cursor:
            cursor.execute(
                """UPDATE work_sessions SET end_time=?,
                   duration_seconds=CAST((julianday(?) - julianday(start_time)) * 86400 AS INTEGER)
                   WHERE id=? AND end_time IS NULL""",
                (now, now, session_id),
            )
            cursor.execute("SELECT * FROM work_sessions WHERE id = ?", (session_id,))
            row = cursor.fetchone()
            return self._row_to_work_session(row) if row else None

    # ─── Break Session Operations ─────────────────────────────────────

    def create_break_session(self, session: BreakSession) -> BreakSession:
        """Insert a new break session."""
        with self._cursor() as cursor:
            cursor.execute(
                """INSERT INTO break_sessions
                   (id, day_id, break_type, start_time, end_time, duration_seconds, notes)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    session.id, session.day_id, session.break_type,
                    session.start_time, session.end_time,
                    session.duration_seconds, session.notes,
                ),
            )
            return session

    def get_active_break(self, day_id: str) -> BreakSession | None:
        """Get the currently running break for a day."""
        with self._cursor() as cursor:
            cursor.execute(
                "SELECT * FROM break_sessions WHERE day_id = ? AND end_time IS NULL",
                (day_id,),
            )
            row = cursor.fetchone()
            return self._row_to_break_session(row) if row else None

    def get_breaks_by_day(self, day_id: str) -> list[BreakSession]:
        """Get all break sessions for a day, ordered by start time."""
        with self._cursor() as cursor:
            cursor.execute(
                "SELECT * FROM break_sessions WHERE day_id = ? ORDER BY start_time",
                (day_id,),
            )
            return [self._row_to_break_session(row) for row in cursor.fetchall()]

    def end_break(self, break_id: str) -> BreakSession | None:
        """End a running break session."""
        from datetime import datetime

        now = datetime.now().isoformat()
        with self._cursor() as cursor:
            cursor.execute(
                """UPDATE break_sessions SET end_time=?,
                   duration_seconds=CAST((julianday(?) - julianday(start_time)) * 86400 AS INTEGER)
                   WHERE id=? AND end_time IS NULL""",
                (now, now, break_id),
            )
            cursor.execute("SELECT * FROM break_sessions WHERE id = ?", (break_id,))
            row = cursor.fetchone()
            return self._row_to_break_session(row) if row else None

    # ─── Search Operations ────────────────────────────────────────────

    # Alias scheme for day columns in joined search queries: prefix "d__"
    # avoids collisions with identically-named task/session columns.
    _DAY_ALIASES: dict[str, str] = {
        "d__id": "id",
        "d__date": "date",
        "d__start_time": "start_time",
        "d__end_time": "end_time",
        "d__status": "status",
        "d__created_at": "created_at",
        "d__updated_at": "updated_at",
    }

    _DAY_ALIAS_SQL = ", ".join(
        f"d.{col} AS {alias}" for alias, col in _DAY_ALIASES.items()
    )

    @staticmethod
    def _like_pattern(term: str) -> str:
        """Escape LIKE wildcards and wrap a term in % for substring matching."""
        escaped = (
            term.replace("\\", "\\\\")
            .replace("%", "\\%")
            .replace("_", "\\_")
        )
        return f"%{escaped}%"

    def _day_from_row(self, row: sqlite3.Row) -> Day:
        """Extract the day from an aliased joined search row."""
        return self._row_to_day({
            col: row[alias] for alias, col in self._DAY_ALIASES.items()
        })

    def search_tasks(
        self, term: str, limit: int = 50
    ) -> list[tuple[Task, Day]]:
        """Search tasks by title, description, or notes, joined with their day.

        Returns a list of (Task, Day) tuples ordered by day recency then
        display order. Case-insensitive substring matching.
        """
        pattern = self._like_pattern(term)
        with self._cursor() as cursor:
            cursor.execute(
                f"""SELECT t.*, {self._DAY_ALIAS_SQL} FROM tasks t
                   JOIN days d ON t.day_id = d.id
                   WHERE t.title LIKE ? ESCAPE '\\'
                      OR t.description LIKE ? ESCAPE '\\'
                      OR t.notes LIKE ? ESCAPE '\\'
                   ORDER BY d.date DESC, t.display_order ASC
                   LIMIT ?""",
                (pattern, pattern, pattern, limit),
            )
            rows = cursor.fetchall()
        return [
            (self._row_to_task(row), self._day_from_row(row))
            for row in rows
        ]

    def search_reflections(
        self, term: str, limit: int = 50
    ) -> list[tuple[Reflection, Day, DailySummary | None]]:
        """Search reflections by their content, joined with day and summary.

        Returns (Reflection, Day, DailySummary) tuples for reflections whose
        accomplishments, challenges, tomorrow_first, or additional_notes
        contain the term.
        """
        pattern = self._like_pattern(term)
        with self._cursor() as cursor:
            cursor.execute(
                f"""SELECT r.*, {self._DAY_ALIAS_SQL},
                          s.id AS s_id, s.total_planned AS s_total_planned,
                          s.completed AS s_completed,
                          s.carried_forward AS s_carried_forward,
                          s.archived AS s_archived, s.deleted AS s_deleted,
                          s.total_focus_seconds AS s_total_focus_seconds,
                          s.total_break_seconds AS s_total_break_seconds,
                          s.completion_percentage AS s_completion_percentage,
                          s.longest_session_seconds AS s_longest_session_seconds,
                          s.session_count AS s_session_count,
                          s.journal_rel_path AS s_journal_rel_path,
                          s.generated_at AS s_generated_at
                   FROM reflections r
                   JOIN days d ON r.day_id = d.id
                   LEFT JOIN daily_summaries s ON s.day_id = r.day_id
                   WHERE r.accomplishments LIKE ? ESCAPE '\\'
                      OR r.challenges LIKE ? ESCAPE '\\'
                      OR r.tomorrow_first LIKE ? ESCAPE '\\'
                      OR r.additional_notes LIKE ? ESCAPE '\\'
                   ORDER BY d.date DESC
                   LIMIT ?""",
                (pattern, pattern, pattern, pattern, limit),
            )
            rows = cursor.fetchall()

        results: list[tuple[Reflection, Day, DailySummary | None]] = []
        for row in rows:
            reflection = self._row_to_reflection(row)
            day = self._day_from_row(row)
            summary = None
            if row["s_id"] is not None:
                summary = DailySummary(
                    id=row["s_id"],
                    day_id=row["day_id"],
                    total_planned=row["s_total_planned"],
                    completed=row["s_completed"],
                    carried_forward=row["s_carried_forward"],
                    archived=row["s_archived"],
                    deleted=row["s_deleted"],
                    total_focus_seconds=row["s_total_focus_seconds"],
                    total_break_seconds=row["s_total_break_seconds"],
                    completion_percentage=row["s_completion_percentage"],
                    longest_session_seconds=row["s_longest_session_seconds"],
                    session_count=row["s_session_count"],
                    journal_rel_path=row["s_journal_rel_path"],
                    generated_at=row["s_generated_at"],
                )
            results.append((reflection, day, summary))
        return results

    def search_work_sessions(
        self, term: str, limit: int = 50
    ) -> list[tuple[WorkSession, Task, Day]]:
        """Search work sessions by their task's title or description.

        Returns (WorkSession, Task, Day) tuples ordered by recency.
        """
        pattern = self._like_pattern(term)
        with self._cursor() as cursor:
            cursor.execute(
                f"""SELECT ws.id AS ws__id, ws.task_id AS ws__task_id,
                          ws.start_time AS ws__start_time, ws.end_time AS ws__end_time,
                          ws.duration_seconds AS ws__duration_seconds,
                          ws.created_at AS ws__created_at,
                          t.*, {self._DAY_ALIAS_SQL}
                   FROM work_sessions ws
                   JOIN tasks t ON ws.task_id = t.id
                   JOIN days d ON t.day_id = d.id
                   WHERE t.title LIKE ? ESCAPE '\\'
                      OR t.description LIKE ? ESCAPE '\\'
                   ORDER BY ws.start_time DESC
                   LIMIT ?""",
                (pattern, pattern, limit),
            )
            rows = cursor.fetchall()

        results: list[tuple[WorkSession, Task, Day]] = []
        for row in rows:
            session = WorkSession(
                id=row["ws__id"],
                task_id=row["ws__task_id"],
                start_time=row["ws__start_time"],
                end_time=row["ws__end_time"],
                duration_seconds=row["ws__duration_seconds"],
                created_at=row["ws__created_at"],
            )
            results.append((session, self._row_to_task(row), self._day_from_row(row)))
        return results

    def search_break_sessions(
        self, term: str, limit: int = 50
    ) -> list[tuple[BreakSession, Day]]:
        """Search break sessions by break type or notes."""
        pattern = self._like_pattern(term)
        with self._cursor() as cursor:
            cursor.execute(
                f"""SELECT b.*, {self._DAY_ALIAS_SQL} FROM break_sessions b
                   JOIN days d ON b.day_id = d.id
                   WHERE b.break_type LIKE ? ESCAPE '\\'
                      OR b.notes LIKE ? ESCAPE '\\'
                   ORDER BY b.start_time DESC
                   LIMIT ?""",
                (pattern, pattern, limit),
            )
            rows = cursor.fetchall()
        return [
            (self._row_to_break_session(row), self._day_from_row(row))
            for row in rows
        ]

    # ─── Reflection Operations ────────────────────────────────────────

    def save_reflection(self, reflection: Reflection) -> Reflection:
        """Insert or update reflection for a day."""
        with self._cursor() as cursor:
            cursor.execute(
                """INSERT OR REPLACE INTO reflections
                   (id, day_id, accomplishments, challenges, tomorrow_first,
                    additional_notes, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    reflection.id, reflection.day_id, reflection.accomplishments,
                    reflection.challenges, reflection.tomorrow_first,
                    reflection.additional_notes, reflection.created_at,
                ),
            )
            return reflection

    def get_reflection(self, day_id: str) -> Reflection | None:
        """Get the reflection for a day."""
        with self._cursor() as cursor:
            cursor.execute(
                "SELECT * FROM reflections WHERE day_id = ?", (day_id,)
            )
            row = cursor.fetchone()
            return self._row_to_reflection(row) if row else None

    # ─── Summary Operations ───────────────────────────────────────────

    def save_summary(self, summary: DailySummary) -> DailySummary:
        """Insert or update daily summary."""
        with self._cursor() as cursor:
            cursor.execute(
                """INSERT OR REPLACE INTO daily_summaries
                   (id, day_id, total_planned, completed, carried_forward,
                    archived, deleted, total_focus_seconds, total_break_seconds,
                    completion_percentage, longest_session_seconds, session_count,
                    journal_rel_path, generated_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    summary.id, summary.day_id, summary.total_planned,
                    summary.completed, summary.carried_forward, summary.archived,
                    summary.deleted, summary.total_focus_seconds,
                    summary.total_break_seconds, summary.completion_percentage,
                    summary.longest_session_seconds, summary.session_count,
                    summary.journal_rel_path, summary.generated_at,
                ),
            )
            return summary

    def get_summary(self, day_id: str) -> DailySummary | None:
        """Get the daily summary for a day."""
        with self._cursor() as cursor:
            cursor.execute(
                "SELECT * FROM daily_summaries WHERE day_id = ?", (day_id,)
            )
            row = cursor.fetchone()
            return self._row_to_summary(row) if row else None

    # ─── Calculation Helpers ──────────────────────────────────────────

    def calculate_day_focus_seconds(self, day_id: str) -> int:
        """Calculate total focus time for a day from all work sessions."""
        with self._cursor() as cursor:
            cursor.execute(
                """SELECT COALESCE(SUM(ws.duration_seconds), 0)
                   FROM work_sessions ws
                   JOIN tasks t ON ws.task_id = t.id
                   WHERE t.day_id = ? AND ws.end_time IS NOT NULL""",
                (day_id,),
            )
            row = cursor.fetchone()
            return row[0] if row else 0

    def calculate_day_break_seconds(self, day_id: str) -> int:
        """Calculate total break time for a day."""
        with self._cursor() as cursor:
            cursor.execute(
                """SELECT COALESCE(SUM(duration_seconds), 0)
                   FROM break_sessions
                   WHERE day_id = ? AND end_time IS NOT NULL""",
                (day_id,),
            )
            row = cursor.fetchone()
            return row[0] if row else 0

    def get_longest_session(self, day_id: str) -> int:
        """Get the longest work session duration for a day."""
        with self._cursor() as cursor:
            cursor.execute(
                """SELECT COALESCE(MAX(ws.duration_seconds), 0)
                   FROM work_sessions ws
                   JOIN tasks t ON ws.task_id = t.id
                   WHERE t.day_id = ? AND ws.end_time IS NOT NULL""",
                (day_id,),
            )
            row = cursor.fetchone()
            return row[0] if row else 0

    def get_session_count(self, day_id: str) -> int:
        """Get the number of completed work sessions for a day."""
        with self._cursor() as cursor:
            cursor.execute(
                """SELECT COUNT(*)
                   FROM work_sessions ws
                   JOIN tasks t ON ws.task_id = t.id
                   WHERE t.day_id = ? AND ws.end_time IS NOT NULL""",
                (day_id,),
            )
            row = cursor.fetchone()
            return row[0] if row else 0

    # ─── Row Converters ───────────────────────────────────────────────

    @staticmethod
    def _row_to_day(row: sqlite3.Row) -> Day:
        return Day(
            id=row["id"],
            date=row["date"],
            start_time=row["start_time"],
            end_time=row["end_time"],
            status=row["status"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    @staticmethod
    def _row_to_task(row: sqlite3.Row) -> Task:
        return Task(
            id=row["id"],
            day_id=row["day_id"],
            title=row["title"],
            description=row["description"],
            priority=row["priority"],
            status=row["status"],
            deadline=row["deadline"],
            estimated_minutes=row["estimated_minutes"],
            actual_seconds=row["actual_seconds"],
            created_at=row["created_at"],
            activated_at=row["activated_at"],
            completed_at=row["completed_at"],
            display_order=row["display_order"],
            notes=row["notes"],
        )

    @staticmethod
    def _row_to_work_session(row: sqlite3.Row) -> WorkSession:
        return WorkSession(
            id=row["id"],
            task_id=row["task_id"],
            start_time=row["start_time"],
            end_time=row["end_time"],
            duration_seconds=row["duration_seconds"],
            created_at=row["created_at"],
        )

    @staticmethod
    def _row_to_break_session(row: sqlite3.Row) -> BreakSession:
        return BreakSession(
            id=row["id"],
            day_id=row["day_id"],
            break_type=row["break_type"],
            start_time=row["start_time"],
            end_time=row["end_time"],
            duration_seconds=row["duration_seconds"],
            notes=row["notes"],
        )

    @staticmethod
    def _row_to_reflection(row: sqlite3.Row) -> Reflection:
        return Reflection(
            id=row["id"],
            day_id=row["day_id"],
            accomplishments=row["accomplishments"],
            challenges=row["challenges"],
            tomorrow_first=row["tomorrow_first"],
            additional_notes=row["additional_notes"],
            created_at=row["created_at"],
        )

    @staticmethod
    def _row_to_summary(row: sqlite3.Row) -> DailySummary:
        return DailySummary(
            id=row["id"],
            day_id=row["day_id"],
            total_planned=row["total_planned"],
            completed=row["completed"],
            carried_forward=row["carried_forward"],
            archived=row["archived"],
            deleted=row["deleted"],
            total_focus_seconds=row["total_focus_seconds"],
            total_break_seconds=row["total_break_seconds"],
            completion_percentage=row["completion_percentage"],
            longest_session_seconds=row["longest_session_seconds"],
            session_count=row["session_count"],
            journal_rel_path=row["journal_rel_path"],
            generated_at=row["generated_at"],
        )
