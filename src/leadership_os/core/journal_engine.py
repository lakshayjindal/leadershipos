"""Journal Engine — generates Markdown daily journals.

Responsibilities:
- Build structured Markdown journal from day's data
- Include header, summary, completed/incomplete tasks, timeline, statistics,
  reflection, and tomorrow sections
- Write journal to configured Obsidian vault path
- Store relative journal path in DailySummary
- Emit JOURNAL_GENERATED event on success

Design principle: The journal is the permanent memory of Leadership OS.
It should be human-readable, Markdown-compatible, and easy to edit manually.
No proprietary formatting should be introduced.
"""

from __future__ import annotations

import logging
from datetime import datetime

from leadership_os.core.database import Database
from leadership_os.core.event_bus import EventBus, JOURNAL_GENERATED
from leadership_os.core.models import (
    Day,
    Task,
    WorkSession,
    BreakSession,
    Reflection,
    DailySummary,
)
from leadership_os.core.enums import TaskStatus
from leadership_os.config.config_manager import ConfigManager
from leadership_os.config.defaults import DEFAULTS
from leadership_os.utils.path_utils import (
    get_journal_path,
    get_relative_journal_path,
    ensure_directory,
)

logger = logging.getLogger(__name__)


class JournalEngine:
    """Generates Markdown daily journals from day data.

    The journal engine is a standalone generator — it reads data from the
    database, constructs a structured Markdown document, and writes it to
    the configured Obsidian vault path.
    """

    def __init__(
        self, db: Database, event_bus: EventBus, config_manager: ConfigManager
    ) -> None:
        self.db = db
        self.event_bus = event_bus
        self.config = config_manager

    # ─── Main Entry Point ─────────────────────────────────────────────

    def generate_journal(self, day_id: str) -> DailySummary:
        """Generate and write the Markdown journal for a given day.

        Workflow:
        1. Load all day data (day, tasks, sessions, breaks, reflection)
        2. Calculate daily statistics
        3. Build Markdown content
        4. Write to file in Obsidian vault
        5. Persist DailySummary with journal_rel_path
        6. Emit JOURNAL_GENERATED event

        Args:
            day_id: The ID of the day to generate a journal for.

        Returns:
            The DailySummary with journal path set.

        Raises:
            ValueError: If the day is not found.
            FileNotFoundError: If the vault path is not writable.
        """
        # Load day data
        day = self.db.get_day(day_id)
        if day is None:
            raise ValueError(f"Day not found: {day_id}")

        tasks = self.db.get_tasks_by_day(day_id)
        break_sessions = self.db.get_breaks_by_day(day_id)
        reflection = self.db.get_reflection(day_id)

        # Collect all work sessions across all tasks
        all_sessions: list[WorkSession] = []
        for task in tasks:
            sessions = self.db.get_sessions_by_task(task.id)
            all_sessions.extend(sessions)

        # Calculate statistics
        focus_seconds = self.db.calculate_day_focus_seconds(day_id)
        break_seconds = self.db.calculate_day_break_seconds(day_id)
        longest_session = self.db.get_longest_session(day_id)
        session_count = self.db.get_session_count(day_id)
        completion_pct = self._calculate_completion(tasks)

        # Build the Markdown content
        markdown = self._build_full_journal(
            day=day,
            tasks=tasks,
            all_sessions=all_sessions,
            break_sessions=break_sessions,
            reflection=reflection,
            focus_seconds=focus_seconds,
            break_seconds=break_seconds,
            longest_session=longest_session,
            session_count=session_count,
            completion_pct=completion_pct,
        )

        # Write the file
        vault_path = self._get_vault_path()
        journal_dir = self._get_journal_dir()
        rel_path = get_relative_journal_path(journal_dir, day.date)
        full_path = get_journal_path(vault_path, journal_dir, day.date)

        try:
            ensure_directory(full_path.parent)
            full_path.write_text(markdown, encoding="utf-8")
        except OSError as e:
            raise RuntimeError(
                f"Failed to write journal to {full_path}: {e}"
            ) from e

        logger.info("Journal written to %s", full_path)

        # Save or update DailySummary
        summary = self.db.get_summary(day_id)
        carried_forward = len(
            [t for t in tasks if t.status == TaskStatus.CARRIED_FORWARD.value]
        )
        archived = len(
            [t for t in tasks if t.status == TaskStatus.ARCHIVED.value]
        )
        completed = len(
            [t for t in tasks if t.status == TaskStatus.COMPLETED.value]
        )
        total_planned = len(tasks)

        if summary is None:
            summary = DailySummary(
                day_id=day_id,
                total_planned=total_planned,
                completed=completed,
                carried_forward=carried_forward,
                archived=archived,
                total_focus_seconds=focus_seconds,
                total_break_seconds=break_seconds,
                completion_percentage=completion_pct,
                longest_session_seconds=longest_session,
                session_count=session_count,
                journal_rel_path=rel_path,
            )
        else:
            # Recalculate stats for existing summary on re-generation
            summary.total_planned = total_planned
            summary.completed = completed
            summary.carried_forward = carried_forward
            summary.archived = archived
            summary.total_focus_seconds = focus_seconds
            summary.total_break_seconds = break_seconds
            summary.completion_percentage = completion_pct
            summary.longest_session_seconds = longest_session
            summary.session_count = session_count

        summary.journal_rel_path = rel_path
        summary.generated_at = datetime.now().isoformat()
        self.db.save_summary(summary)

        # Emit event
        self.event_bus.emit(
            JOURNAL_GENERATED,
            {
                "day_id": day_id,
                "date": day.date,
                "journal_path": str(full_path),
                "journal_rel_path": rel_path,
            },
        )

        logger.info(
            "Journal generated for %s: %s", day.date, rel_path
        )
        return summary

    # ─── Full Journal Builder ─────────────────────────────────────────

    def _build_full_journal(
        self,
        day: Day,
        tasks: list[Task],
        all_sessions: list[WorkSession],
        break_sessions: list[BreakSession],
        reflection: Reflection | None,
        focus_seconds: int,
        break_seconds: int,
        longest_session: int,
        session_count: int,
        completion_pct: float,
    ) -> str:
        """Build the complete Markdown journal document."""
        parts: list[str] = []

        parts.append(self._build_header(day))
        parts.append("")

        parts.append(self._build_summary(
            tasks, focus_seconds, break_seconds, completion_pct
        ))
        parts.append("")

        parts.append(self._build_completed_tasks(tasks, all_sessions))
        parts.append("")

        parts.append(self._build_incomplete_tasks(tasks))
        parts.append("")

        parts.append(self._build_carried_forward(tasks))
        parts.append("")

        parts.append(self._build_timeline(all_sessions, break_sessions, tasks))
        parts.append("")

        parts.append(self._build_statistics(
            focus_seconds, break_seconds, len(tasks),
            len([t for t in tasks if t.status == TaskStatus.COMPLETED.value]),
            session_count, longest_session, completion_pct,
        ))
        parts.append("")

        parts.append(self._build_reflection(reflection))
        parts.append("")

        parts.append(self._build_tomorrow(tasks))

        return "\n".join(parts).strip() + "\n"

    # ─── Section Builders ─────────────────────────────────────────────

    def _build_header(self, day: Day) -> str:
        """Build the header section with date and start/end times."""
        lines: list[str] = []

        # Parse date for human-readable format
        try:
            dt = datetime.strptime(day.date, "%Y-%m-%d")
            day_name = dt.strftime("%A")
            month_name = dt.strftime("%B")
            day_num = dt.day
            year = dt.year
            header_line = f"# {day_name}, {month_name} {day_num}, {year}"
        except ValueError:
            header_line = f"# {day.date}"

        lines.append(header_line)
        lines.append("")

        # Start and end times
        start_str = self._format_time(day.start_time, "Not started")
        end_str = self._format_time(day.end_time, "Not finished")
        lines.append(f"**Started:** {start_str}")
        lines.append(f"**Finished:** {end_str}")

        return "\n".join(lines)

    def _build_summary(
        self,
        tasks: list[Task],
        focus_seconds: int,
        break_seconds: int,
        completion_pct: float,
    ) -> str:
        """Build the daily summary overview section."""
        total = len(tasks)
        completed = len(
            [t for t in tasks if t.status == TaskStatus.COMPLETED.value]
        )
        carried = len(
            [t for t in tasks if t.status == TaskStatus.CARRIED_FORWARD.value]
        )
        pending = len(
            [t for t in tasks if t.status in (
                TaskStatus.PENDING.value,
                TaskStatus.ACTIVE.value,
                TaskStatus.PAUSED.value,
            )]
        )

        lines = ["## Summary", ""]
        lines.append(f"- **Planned Tasks:** {total}")
        lines.append(
            f"- **Completed:** {completed} "
            f"({completion_pct:.0f}%)"
        )
        if pending > 0:
            lines.append(f"- **Incomplete:** {pending}")
        if carried > 0:
            lines.append(f"- **Carried Forward:** {carried}")
        lines.append(f"- **Focus Time:** {self._format_duration_human(focus_seconds)}")
        lines.append(f"- **Break Time:** {self._format_duration_human(break_seconds)}")
        lines.append("")
        lines.append("---")

        return "\n".join(lines)

    def _build_completed_tasks(
        self,
        tasks: list[Task],
        all_sessions: list[WorkSession],
    ) -> str:
        """Build the completed tasks section."""
        completed = [
            t for t in tasks
            if t.status == TaskStatus.COMPLETED.value
        ]

        if not completed:
            return "## Completed\n\n_No tasks completed._"

        lines = ["## Completed", ""]
        for task in completed:
            # Calculate total time from sessions
            task_sessions = [
                s for s in all_sessions if s.task_id == task.id
            ]
            total_seconds = sum(s.duration_seconds for s in task_sessions)
            time_str = self._format_duration_human(total_seconds)

            line = f"- [x] **{task.title}**"
            if time_str:
                line += f" ({time_str})"
            lines.append(line)

            # Add notes if present
            if task.notes:
                # Indent notes below the task
                for note_line in task.notes.strip().split("\n"):
                    lines.append(f"  > {note_line}")

        return "\n".join(lines)

    def _build_incomplete_tasks(self, tasks: list[Task]) -> str:
        """Build the incomplete tasks section (pending, active, paused — NOT carried forward)."""
        incomplete = [
            t for t in tasks
            if t.status in (
                TaskStatus.PENDING.value,
                TaskStatus.ACTIVE.value,
                TaskStatus.PAUSED.value,
            )
        ]

        if not incomplete:
            # Check if there are any tasks at all
            if not tasks:
                return "## Incomplete\n\n_No tasks planned._"
            return "## Incomplete\n\n_All tasks completed._"

        lines = ["## Incomplete", ""]
        for task in incomplete:
            status_label = task.status.replace("_", " ").title()
            lines.append(
                f"- [ ] **{task.title}** — {status_label}"
            )

        return "\n".join(lines)

    def _build_carried_forward(self, tasks: list[Task]) -> str:
        """Build the carried-forward tasks section."""
        carried = [
            t for t in tasks
            if t.status == TaskStatus.CARRIED_FORWARD.value
        ]

        if not carried:
            return "## Carried Forward\n\n_No tasks carried forward._"

        lines = ["## Carried Forward", ""]
        for task in carried:
            lines.append(f"- [ ] **{task.title}** — {task.priority.upper()}")

        return "\n".join(lines)

    def _build_timeline(
        self,
        all_sessions: list[WorkSession],
        break_sessions: list[BreakSession],
        tasks: list[Task],
    ) -> str:
        """Build the timeline of events during the day.

        Reconstructs the workday chronologically from all recorded events:
        - Work session starts (task activated / resumed)
        - Work session ends (paused or completed)
        - Break session starts
        - Break session ends

        Session ends are labelled "Completed" if the session's end time matches
        the task's completion time, otherwise "Paused".
        """
        # Build lookups
        task_titles: dict[str, str] = {t.id: t.title for t in tasks}
        task_completed: dict[str, bool] = {
            t.id: t.status == TaskStatus.COMPLETED.value
            for t in tasks
        }

        # Find the last session (latest end_time) per task for the "Completed" label
        last_session_per_task: dict[str, WorkSession] = {}
        for session in all_sessions:
            if session.end_time is None:
                continue
            existing = last_session_per_task.get(session.task_id)
            if existing is None or session.end_time > existing.end_time:
                last_session_per_task[session.task_id] = session

        last_session_ids: set[str] = {
            s.id for s in last_session_per_task.values()
        }

        # Collect all events with (timestamp, description)
        events: list[tuple[str, str]] = []

        for session in all_sessions:
            title = task_titles.get(session.task_id, "Unknown Task")
            events.append((session.start_time, f"Started **{title}**"))
            if session.end_time:
                # If this is the last session AND the task is completed, label "Completed"
                is_last = session.id in last_session_ids
                task_done = task_completed.get(session.task_id, False)
                if is_last and task_done:
                    label = f"Completed **{title}**"
                else:
                    label = f"Paused **{title}**"
                events.append((session.end_time, label))

        for break_sesh in break_sessions:
            title = break_sesh.break_type.title()
            events.append(
                (break_sesh.start_time, f"{title} break")
            )
            if break_sesh.end_time:
                events.append(
                    (break_sesh.end_time, "Resumed")
                )

        if not events:
            return "## Timeline\n\n_No events recorded._"

        # Sort chronologically by timestamp
        events.sort(key=lambda e: e[0])

        lines = ["## Timeline", ""]
        for ts, description in events:
            time_str = self._format_time(ts, "—")
            lines.append(f"- **{time_str}** — {description}")

        return "\n".join(lines)

    def _build_statistics(
        self,
        focus_seconds: int,
        break_seconds: int,
        total_tasks: int,
        completed_tasks: int,
        session_count: int,
        longest_session: int,
        completion_pct: float,
    ) -> str:
        """Build the work statistics section."""
        lines = ["## Work Statistics", ""]

        # Define stats as (label, value) pairs
        stats: list[tuple[str, str]] = [
            ("Total Focus Time", self._format_duration_human(focus_seconds)),
            ("Total Break Time", self._format_duration_human(break_seconds)),
            ("Total Tasks", str(total_tasks)),
            ("Completed", str(completed_tasks)),
            ("Work Sessions", str(session_count)),
            ("Longest Session", self._format_duration_human(longest_session)),
            ("Completion", f"{completion_pct:.0f}%"),
        ]

        # Average session
        if session_count > 0:
            avg = focus_seconds // session_count
            stats.insert(-1, ("Average Session", self._format_duration_human(avg)))

        for label, value in stats:
            lines.append(f"- **{label}:** {value}")

        return "\n".join(lines)

    def _build_reflection(
        self, reflection: Reflection | None
    ) -> str:
        """Build the reflection section from user's End-of-Day answers."""
        lines = ["## Reflection", ""]

        if reflection is None or not reflection.has_content:
            lines.append("_No reflection recorded._")
            return "\n".join(lines)

        questions = [
            ("What did you accomplish today?", "accomplishments"),
            ("What slowed you down?", "challenges"),
            ("What should you do first tomorrow?", "tomorrow_first"),
        ]

        for question, attr in questions:
            answer = getattr(reflection, attr, "").strip()
            lines.append(f"### {question}")
            if answer:
                lines.append("")
                lines.append(answer)
            else:
                lines.append("")
                lines.append("_No answer provided._")
            lines.append("")

        # Additional notes if present
        if reflection.additional_notes.strip():
            lines.append("### Additional Notes")
            lines.append("")
            lines.append(reflection.additional_notes.strip())
            lines.append("")

        return "\n".join(lines).rstrip()

    def _build_tomorrow(self, tasks: list[Task]) -> str:
        """Build the 'Tomorrow' section with the first action.

        Shows the first pending/incomplete task as the recommended
        starting point for the next day.
        """
        lines = ["---", "", "## Tomorrow", ""]

        # Find the first incomplete task (ordered by display_order)
        incomplete = [
            t for t in tasks
            if t.status in (
                TaskStatus.PENDING.value,
                TaskStatus.ACTIVE.value,
                TaskStatus.PAUSED.value,
            )
        ]

        if incomplete:
            first = incomplete[0]
            lines.append(
                f"Start with **{first.title}**."
            )
        else:
            lines.append("_No pending tasks for tomorrow._")

        # Show reflection's tomorrow_first if available
        # (the reflection is already included above, no need to duplicate)

        return "\n".join(lines)

    # ─── Helpers ──────────────────────────────────────────────────────

    def _calculate_completion(self, tasks: list[Task]) -> float:
        """Calculate completion percentage from task list."""
        if not tasks:
            return 0.0
        completed = len(
            [t for t in tasks if t.status == TaskStatus.COMPLETED.value]
        )
        return round((completed / len(tasks)) * 100, 1)

    def _format_time(self, time_str: str | None, fallback: str = "--:--") -> str:
        """Format an ISO timestamp or time string to HH:MM display."""
        if not time_str:
            return fallback
        try:
            # Try parsing as full ISO timestamp
            dt = datetime.fromisoformat(time_str)
            return dt.strftime("%H:%M")
        except (ValueError, TypeError):
            # If it's already just a time like "09:00" or "HH:MM:SS"
            if isinstance(time_str, str) and len(time_str) >= 5 and ":" in time_str:
                return time_str[:5]
            return fallback

    def _format_duration_human(self, total_seconds: int) -> str:
        """Format seconds into human-readable duration like '2h 34m'."""
        if total_seconds <= 0:
            return "0m"
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        if hours > 0 and minutes > 0:
            return f"{hours}h {minutes}m"
        elif hours > 0:
            return f"{hours}h"
        else:
            return f"{minutes}m"

    def _get_vault_path(self) -> str:
        """Get the configured vault path, falling back to default."""
        journaling = self.config.get_section("journaling")
        if journaling and "vault_path" in journaling:
            return str(journaling["vault_path"])
        return DEFAULTS.get("journaling", {}).get("vault_path", "~/Documents/Obsidian")

    def _get_journal_dir(self) -> str:
        """Get the configured journal directory, falling back to default."""
        journaling = self.config.get_section("journaling")
        if journaling and "journal_dir" in journaling:
            return str(journaling["journal_dir"])
        return DEFAULTS.get("journaling", {}).get("journal_dir", "Daily Notes")
