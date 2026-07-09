# Daily Journal

## Purpose

The Daily Journal is the permanent historical record generated at the conclusion of every working day.

It captures not only what was accomplished, but also how the day unfolded.

Unlike traditional productivity applications that focus only on completed tasks, Leadership OS preserves the complete story of the day.

Every completed day results in exactly one Markdown document.

These journals form a chronological archive that can be searched, reviewed, and referenced months or years later.

The Daily Journal is one of the primary outputs of Leadership OS.

---

# Philosophy

People rarely remember details of their work after a few weeks.

Tasks are forgotten.

Problems solved are forgotten.

Decisions are forgotten.

The Daily Journal exists to preserve those memories.

Rather than asking the user to manually maintain a diary, Leadership OS automatically constructs one from the information already collected throughout the day.

The user should only contribute reflection.

Everything else should be generated automatically.

---

# Journal Generation

A journal is generated when:

- The End-of-Day Review has been completed.
- The day's data has been validated.
- Reflection questions have been answered.

Only one journal may exist for a given day.

If regeneration is required, the existing file should be updated rather than duplicated.

---

# Storage Location

The journal is stored inside the configured Obsidian vault.

Example

```
~/Documents/Obsidian/Daily Notes/
```

Default filename

```
YYYY-MM-DD.md
```

Example

```
2026-07-09.md
```

The storage location must be configurable.

---

# Journal Structure

Every journal follows the same structure.

Consistency is more important than customization.

The default structure consists of:

- Header
- Daily Summary
- Planned Tasks
- Completed Tasks
- Carried Forward Tasks
- Timeline
- Work Statistics
- Reflection
- Tomorrow

Additional sections may be added in future versions without breaking compatibility.

---

# Header

Contains basic information about the day.

Fields include:

- Date
- Day of Week
- Start Time
- End Time
- Total Working Duration

Example

```md
# Wednesday, July 9, 2026

Started: 09:05

Finished: 21:12
```

---

# Daily Summary

Provides a quick overview of the day.

Example information includes:

- Planned Tasks
- Completed Tasks
- Carried Forward Tasks
- Focus Time
- Break Time
- Completion Percentage

The summary should be readable in under thirty seconds.

---

# Planned Tasks

Displays every task planned during Morning Planning.

Tasks should preserve their original execution order.

Completed tasks should remain visible.

The purpose is historical accuracy rather than showing only successful outcomes.

---

# Completed Tasks

Lists all completed work.

Each completed task may optionally include:

- Completion Time
- Total Focus Time
- Notes

---

# Carried Forward

Displays unfinished work.

Each task should include:

Reason if available.

Examples

- Waiting for review
- Blocked
- Insufficient time
- Deferred

These tasks become available during the next Morning Planning session.

---

# Timeline

The timeline reconstructs the workday.

Every important event appears chronologically.

Examples

```
09:00 Started "Implement Credits"

10:45 Tea Break

11:00 Resumed

12:30 Completed "Implement Credits"

13:00 Lunch

14:00 Started "Review Pull Requests"

17:15 Completed

19:30 Dinner

20:10 Reflection
```

The timeline should be generated automatically from recorded events.

---

# Work Statistics

Displays numerical information.

Examples include:

Total Focus Time

Total Break Time

Number of Tasks

Completed Tasks

Work Sessions

Longest Focus Session

Average Focus Session

Completion Percentage

These values are calculated automatically.

---

# Reflection

Reflection is the only section primarily written by the user.

Required questions

What did you accomplish today?

What slowed you down?

What should you do first tomorrow?

Future versions may support additional questions.

---

# Tomorrow

Displays the first planned action for the next working day.

Example

```
Tomorrow

Start by fixing upload batching.
```

This section helps reduce startup friction the following morning.

---

# Formatting

The journal should remain:

Human readable.

Markdown compatible.

Plain text.

Easy to edit manually.

No proprietary formatting should be introduced.

---

# Editing

The generated journal belongs to the user.

Users may edit it freely inside Obsidian.

Leadership OS should never overwrite manual edits without confirmation.

If regeneration becomes necessary:

The application should preserve user-written content whenever possible.

---

# Searchability

The journal should support Obsidian's search features naturally.

This is achieved by using:

Headings

Bullet lists

Standard Markdown

Consistent terminology

Optional tags (future)

No custom syntax should be required.

---

# Reliability

Journal generation must never fail silently.

If generation fails:

- The user should be informed.
- The cause should be explained.
- The journal should be recoverable.

No completed day should be lost because of a file system error.

---

# Future Expansion

Future versions may automatically include:

Git commits.

Application usage statistics.

Screenshots.

Weather.

Music played.

Meeting summaries.

AI-generated daily summaries.

These additions should remain optional and should never replace the core journal structure.

---

# Example Journal

```md
# Wednesday, July 9, 2026

## Summary

- Planned Tasks: 5
- Completed: 4
- Carried Forward: 1
- Focus Time: 7h 42m
- Break Time: 1h 18m

---

## Planned Tasks

- [x] Implement Credits
- [x] Review Pull Requests
- [x] Fix Upload Bug
- [x] Update Documentation
- [ ] Improve Notification Engine

---

## Timeline

09:05 Started Implement Credits

11:10 Tea Break

11:25 Resumed

13:00 Completed Implement Credits

14:00 Review Pull Requests

17:20 Completed

19:30 Dinner

20:05 Resume

21:10 End of Day Review

---

## Reflection

### What did I accomplish?

Implemented the complete credits system and merged two pull requests.

### What slowed me down?

Unexpected upload validation bug.

### First task tomorrow

Finish Notification Engine.
```

---

# Design Principles

The Daily Journal should be:

Automatic.

Accurate.

Readable.

Permanent.

Searchable.

Timeless.

The user should be able to open any journal years later and immediately understand how that day unfolded.

---

# Final Principle

The Daily Journal is not merely a report.

It is the permanent memory of Leadership OS.

Every feature in the application ultimately exists to produce a richer, more accurate, and more valuable record of the user's working day.

If Leadership OS were reduced to a single lasting output, it would be the Daily Journal.