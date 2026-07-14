# Task Lifecycle

## Purpose

This document defines the complete lifecycle of a task within Leadership OS.

A task is never simply "created" and "completed." Instead, it moves through a series of well-defined states throughout its lifetime.

This document defines:

- Every possible task state
- Valid state transitions
- Events that trigger transitions
- Rules governing task behavior

The lifecycle is intentionally strict to ensure consistent application behavior and prevent ambiguous task states.

---

# Lifecycle Overview

Every task follows the same lifecycle.

```

Created
│
▼
Pending
│
├──────────────┐
│              │
▼              ▼
Active      Archived
│
├──────────────┐
│              │
▼              ▼
Completed   Paused
│              │
│              ▼
│          Active
│
▼
Closed

```

Some transitions are optional.

Some transitions are permanent.

---

# State Definitions

## Created

A task has been created by the user but has not yet entered the daily workflow.

Characteristics:

- Exists in storage
- Has not started
- No work sessions
- Editable

Created is a temporary internal state.

Immediately after creation, every task becomes Pending.

---

## Pending

The task exists but no work has begun.

Characteristics:

- Appears in today's task list
- Can be reordered
- Can be edited
- Can be deleted
- May receive deadlines
- Has zero work sessions

Possible transitions:

Pending → Active

Pending → Archived

Pending → Deleted

---

## Active

The task is currently being worked on.

Leadership OS allows exactly one Active task at any given time.

Entering Active automatically:

- Starts the timer
- Updates the overlay
- Records the activation time
- Creates a new work session

Possible transitions:

Active → Paused

Active → Completed

Active → Archived

---

## Paused

The task has temporarily stopped.

Examples:

- Lunch
- Dinner
- Phone call
- Meeting
- Manual pause

Entering Paused:

- Stops the current work session
- Preserves accumulated time
- Keeps task unfinished

Possible transitions:

Paused → Active

Paused → Archived

Paused → Completed

---

## Completed

The work has finished successfully.

Entering Completed:

- Stops the timer
- Records completion timestamp
- Updates statistics
- Removes task from active queue

Completed tasks remain editable only for notes.

Possible transitions:

Completed → Closed

---

## Archived

The task is intentionally removed from active planning.

Reasons include:

- No longer relevant
- Deferred indefinitely
- Duplicate
- Cancelled

Archived tasks:

- Never appear in today's planning
- Remain searchable
- Remain part of history

Archived tasks are never automatically deleted.

---

## Deleted

The user explicitly deletes the task.

Deleted tasks are permanently removed.

Deletion should require confirmation.

Deletion should be uncommon.

---

## Closed

Closed represents the final immutable state.

The task becomes part of historical records.

Closed tasks cannot change state.

---

# State Transition Rules

Allowed transitions:

```

Created
↓

Pending

↓

Active

↓

Paused

↓

Active

↓

Completed

↓

Closed

```

Alternative paths:

```

Pending → Archived

Active → Archived

Paused → Archived

Pending → Deleted

```

All other transitions are invalid.

---

# Transition Events

## Create Task

Trigger:

User creates task.

Result:

Created → Pending

---

## Start Task

Trigger:

User selects task.

Result:

Pending → Active

Effects:

- Timer starts
- Overlay updates
- Work session begins

---

## Pause Task

Trigger:

Break begins

Manual pause

Application shutdown

Result:

Active → Paused

Effects:

- Timer pauses
- Session ends

---

## Resume Task

Trigger:

Break ends

Manual resume

Result:

Paused → Active

Effects:

- New work session begins

---

## Complete Task

Trigger:

User marks task complete.

Result:

Active → Completed

Effects:

- Timer stops
- Completion timestamp stored
- Overlay selects next task

---

## Archive Task

Trigger:

User archives task.

Possible sources:

Pending

Active

Paused

Result:

Archived

---

## Delete Task

Trigger:

User confirms deletion.

Result:

Deleted

---

## Close Task

Trigger:

End-of-day archival

Result:

Completed → Closed

Closed is irreversible.

---

# Work Session Behavior

Every transition into Active creates a new work session.

Example:

```

09:00 Start

↓

10:15 Lunch

↓

11:00 Resume

↓

12:00 Meeting

↓

12:30 Resume

↓

14:00 Complete

```

Produces:

Session 1

09:00–10:15

Session 2

11:00–12:00

Session 3

12:30–14:00

The task duration is the sum of all sessions.

---

# Validation Rules

Leadership OS must enforce the following:

Only one Active task exists.

Completed tasks cannot become Pending.

Archived tasks cannot automatically reactivate.

Deleted tasks cannot be recovered.

Every Active task must have an active timer.

Every timer belongs to exactly one task.

---

# User Actions

Allowed actions by state:

| State | Edit | Reorder | Start | Complete | Archive | Delete |
|--------|------|----------|---------|-----------|-----------|-----------|
| Pending | Yes | Yes | Yes | No | Yes | Yes |
| Active | Limited | No | Already Active | Yes | Yes | No |
| Paused | Limited | No | Resume | Yes | Yes | No |
| Completed | Notes Only | No | No | Already Complete | No | No |
| Archived | No | No | No | No | Restore (Future) | Yes |
| Closed | No | No | No | No | No | No |

---

# Timeline Example

```

09:00 Create Task

↓

09:05 Start Task

↓

10:30 Lunch

↓

11:10 Resume

↓

13:45 Complete

↓

18:00 Archive Day

↓

Task Closed

```

---

# Design Philosophy

A task represents a commitment made during planning.

Leadership OS should preserve the complete history of that commitment—from creation to archival—rather than simply recording whether it was completed.

By modeling each state explicitly, the application can accurately reconstruct the user's work, generate meaningful daily journals, and maintain a reliable historical record without ambiguity.