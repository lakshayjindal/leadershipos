"""Search Engine — global full-text search for Leadership OS.

Searches every searchable entity in one pass:

- Tasks (title, description, notes, deadline)
- Journal entries (reflections content, journal path, day date)
- Sessions (work sessions via task title/description, break sessions via
  break type and notes)

Results are grouped by category, ranked by relevance (exact title match >
prefix > word match > substring, with a recency bonus), and support
term highlighting for the UI.

Design principle: search is local-first and instant. Everything is
queried straight from SQLite — no separate index to rebuild or corrupt.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any

from leadership_os.core.database import Database

logger = logging.getLogger(__name__)

# ─── Result Model ─────────────────────────────────────────────────────


@dataclass
class SearchHit:
    """A single search result grouped under a category."""

    category: str  # "task" | "journal" | "session"
    title: str
    subtitle: str
    score: int
    id: str  # Entity id (task id, day id, session id)
    day_id: str  # Owning day id (for navigation)
    date: str  # Day date YYYY-MM-DD (for grouping/sorting)
    payload: dict[str, Any] = field(default_factory=dict)

    def __lt__(self, other: "SearchHit") -> bool:
        return self.score > other.score  # Higher score sorts first


# ─── Scoring ──────────────────────────────────────────────────────────


def score_match(query: str, text: str, is_title: bool = False) -> int:
    """Score how well `text` matches `query`.

    Returns 0 if there is no match at all. Higher is more relevant.
    """
    if not query or not text:
        return 0
    q = query.lower().strip()
    t = text.lower().strip()
    if q not in t:
        return 0

    base = 100 if is_title else 40
    if t == q:
        return base + 30  # exact
    if t.startswith(q):
        return base + 20  # prefix
    # Word boundary match (query appears as a whole word)
    for word in t.split():
        if word == q or word.startswith(q):
            return base + 10
    return base  # plain substring


def _recency_bonus(day_date: str, max_bonus: int = 12) -> int:
    """Give newer results a small boost (0..max_bonus)."""
    try:
        d = datetime.strptime(day_date, "%Y-%m-%d").date()
        days_ago = (date.today() - d).days
    except (ValueError, TypeError):
        return 0
    if days_ago < 0:
        days_ago = 0
    return max(0, max_bonus - days_ago)


# ─── Highlighting ─────────────────────────────────────────────────────


def highlight_segments(text: str, query: str) -> list[tuple[str, bool]]:
    """Split `text` into (segment, is_match) tuples for UI highlighting.

    Every case-insensitive occurrence of `query` becomes a match segment.
    """
    if not query or not text:
        return [(text, False)]
    q = query.lower()
    t = text
    segments: list[tuple[str, bool]] = []
    idx = 0
    lower = t.lower()
    while True:
        pos = lower.find(q, idx)
        if pos == -1:
            if idx < len(t):
                segments.append((t[idx:], False))
            break
        if pos > idx:
            segments.append((t[idx:pos], False))
        segments.append((t[pos:pos + len(q)], True))
        idx = pos + len(q)
    return segments


# ─── Search Engine ────────────────────────────────────────────────────


class SearchEngine:
    """Search across all Leadership OS data, grouped by entity type.

    Usage:
        engine = SearchEngine(db, config)
        hits = engine.search("timer")
        for hit in hits:
            print(hit.category, hit.title, hit.score)
    """

    def __init__(self, db: Database, config: Any = None) -> None:
        self.db = db
        self.config = config  # Optional ConfigManager for recent searches

    # ─── Main Entry Point ─────────────────────────────────────────────

    def search(
        self,
        query: str,
        limit_per_category: int = 12,
    ) -> list[SearchHit]:
        """Search everything and return results ordered by relevance.

        The returned list is grouped by category (tasks first, then
        journals, then sessions) and sorted by score within each group.

        Args:
            query: Free-text search term.
            limit_per_category: Max results per entity category.

        Returns:
            A flat list of SearchHit objects, grouped and ranked.
        """
        q = (query or "").strip()
        if not q:
            return []

        tasks = self.search_tasks(q, limit_per_category)
        journals = self.search_journals(q, limit_per_category)
        sessions = self.search_sessions(q, limit_per_category)

        return tasks + journals + sessions

    # ─── Category Searches ────────────────────────────────────────────

    def search_tasks(self, query: str, limit: int = 12) -> list[SearchHit]:
        """Search tasks by title, description, notes, or deadline."""
        hits: list[SearchHit] = []
        try:
            for task, day in self.db.search_tasks(query, limit=limit * 2):
                title_score = score_match(query, task.title, is_title=True)
                desc_score = score_match(query, task.description)
                notes_score = score_match(query, task.notes)
                deadline_score = score_match(query, task.deadline or "")
                best = max(title_score, desc_score, notes_score, deadline_score)
                if best <= 0:
                    continue
                score = best + _recency_bonus(day.date)
                subtitle = task.status.replace("_", " ").title()
                if task.priority != "medium":
                    subtitle = f"{task.priority.upper()} · {subtitle}"
                hits.append(SearchHit(
                    category="task",
                    title=task.title,
                    subtitle=f"{subtitle} — {day.date}",
                    score=score,
                    id=task.id,
                    day_id=day.id,
                    date=day.date,
                    payload={"status": task.status, "priority": task.priority},
                ))
        except Exception as e:
            logger.debug("Task search failed: %s", e)
        hits.sort()
        return hits[:limit]

    def search_journals(self, query: str, limit: int = 12) -> list[SearchHit]:
        """Search journal entries by reflection content, path, or day date."""
        hits: list[SearchHit] = []
        try:
            # 1) Reflections containing the term
            for reflection, day, summary in self.db.search_reflections(query, limit=limit * 2):
                fields = [
                    ("accomplishments", reflection.accomplishments),
                    ("challenges", reflection.challenges),
                    ("tomorrow_first", reflection.tomorrow_first),
                    ("additional_notes", reflection.additional_notes),
                ]
                best = 0
                matched_field = ""
                for field_name, value in fields:
                    s = score_match(query, value)
                    if s > best:
                        best = s
                        matched_field = field_name
                if best <= 0:
                    continue
                score = best + _recency_bonus(day.date)
                excerpt = _excerpt(getattr(reflection, matched_field), query)
                journal_path = summary.journal_rel_path if summary else ""
                hits.append(SearchHit(
                    category="journal",
                    title=f"Journal — {day.date}",
                    subtitle=excerpt or f"Reflection: {matched_field.replace('_', ' ')}",
                    score=score,
                    id=day.id,
                    day_id=day.id,
                    date=day.date,
                    payload={"journal_path": journal_path},
                ))
        except Exception as e:
            logger.debug("Reflection search failed: %s", e)

        try:
            # 2) Days whose date matches (e.g. searching "2026-07-09").
            # Scored low (30) so a content-rich reflection hit for the same
            # day always wins the dedup below.
            for day in self._all_days():
                if score_match(query, day.date) > 0 or query in day.date:
                    summary = self.db.get_summary(day.id)
                    score = 30 + _recency_bonus(day.date)
                    hits.append(SearchHit(
                        category="journal",
                        title=f"Day — {day.date}",
                        subtitle=(
                            f"Journal: {summary.journal_rel_path}"
                            if summary and summary.journal_rel_path
                            else "No journal generated"
                        ),
                        score=score,
                        id=day.id,
                        day_id=day.id,
                        date=day.date,
                        payload={"journal_path": summary.journal_rel_path if summary else ""},
                    ))
        except Exception as e:
            logger.debug("Day-date search failed: %s", e)

        hits.sort()
        # Deduplicate by id keeping the highest score
        seen: dict[str, SearchHit] = {}
        for hit in hits:
            if hit.id not in seen or hit.score > seen[hit.id].score:
                seen[hit.id] = hit
        return sorted(seen.values())[:limit]

    def search_sessions(self, query: str, limit: int = 12) -> list[SearchHit]:
        """Search focus sessions (via task) and break sessions."""
        hits: list[SearchHit] = []
        try:
            for session, task, day in self.db.search_work_sessions(query, limit=limit * 2):
                score = max(
                    score_match(query, task.title, is_title=True),
                    score_match(query, task.description),
                ) + _recency_bonus(day.date)
                duration = format_seconds(session.duration_seconds)
                hits.append(SearchHit(
                    category="session",
                    title=f"Focus: {task.title}",
                    subtitle=f"{duration} · {day.date}",
                    score=score,
                    id=session.id,
                    day_id=day.id,
                    date=day.date,
                    payload={"kind": "work"},
                ))
        except Exception as e:
            logger.debug("Work session search failed: %s", e)

        try:
            for session, day in self.db.search_break_sessions(query, limit=limit * 2):
                score = max(
                    score_match(query, session.break_type, is_title=True),
                    score_match(query, session.notes),
                ) + _recency_bonus(day.date)
                duration = format_seconds(session.duration_seconds)
                hits.append(SearchHit(
                    category="session",
                    title=f"Break: {session.break_type.title()}",
                    subtitle=f"{duration} · {day.date}",
                    score=score,
                    id=session.id,
                    day_id=day.id,
                    date=day.date,
                    payload={"kind": "break"},
                ))
        except Exception as e:
            logger.debug("Break session search failed: %s", e)

        hits.sort()
        return hits[:limit]

    # ─── Recent Searches ──────────────────────────────────────────────

    def get_recent_searches(self, max_count: int = 6) -> list[str]:
        """Return the most recent search terms, most recent first."""
        if self.config is None:
            return []
        try:
            recent = list(self.config.get("search", "recent_searches", []) or [])
            return [str(r) for r in recent][:max_count]
        except Exception as e:
            logger.debug("Failed to read recent searches: %s", e)
            return []

    def add_recent_search(self, query: str) -> None:
        """Record a search term, most recent first, capped and persisted."""
        if self.config is None:
            return
        q = (query or "").strip()
        if not q:
            return
        try:
            recent = [str(r) for r in (self.config.get("search", "recent_searches", []) or [])]
            if q in recent:
                recent.remove(q)
            recent.insert(0, q)
            max_recent = int(self.config.get("search", "max_recent_searches", 10))
            self.config.set("search", "recent_searches", recent[:max_recent])
            self.config.save()
        except Exception as e:
            logger.debug("Failed to record recent search: %s", e)

    def clear_recent_searches(self) -> None:
        """Clear all recorded search history."""
        if self.config is None:
            return
        try:
            self.config.set("search", "recent_searches", [])
            self.config.save()
        except Exception as e:
            logger.debug("Failed to clear recent searches: %s", e)

    # ─── Helpers ──────────────────────────────────────────────────────

    def _all_days(self) -> list:
        """All day records (today + previous days). Read-only — never creates rows."""
        from datetime import date
        days = list(self.db.get_previous_days(limit=1000))
        try:
            today = self.db.get_day_by_date(date.today().isoformat())
            if today is not None and not any(d.id == today.id for d in days):
                days.insert(0, today)
        except Exception:
            pass
        return days


def _excerpt(text: str, query: str, radius: int = 60) -> str:
    """Return a short excerpt around the first match of `query` in `text`."""
    if not text or not query:
        return ""
    lower = text.lower()
    pos = lower.find(query.lower())
    if pos == -1:
        return text[: radius * 2].strip()
    start = max(0, pos - radius)
    end = min(len(text), pos + len(query) + radius)
    prefix = "…" if start > 0 else ""
    suffix = "…" if end < len(text) else ""
    return f"{prefix}{text[start:end].strip()}{suffix}"


def format_seconds(total_seconds: int) -> str:
    """Format seconds as '1h 05m' / '25m' / '45s'."""
    if total_seconds <= 0:
        return "0m"
    hours, rem = divmod(int(total_seconds), 3600)
    minutes, seconds = divmod(rem, 60)
    if hours > 0:
        return f"{hours}h {minutes:02d}m"
    if minutes > 0:
        return f"{minutes}m"
    return f"{seconds}s"
