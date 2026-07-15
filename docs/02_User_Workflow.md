# User Workflow

## Purpose

This document defines the complete lifecycle of a normal working day using Leadership OS.

The workflow is intentionally opinionated. The application is designed around a single daily routine rather than providing multiple ways to accomplish the same objective.

Every feature implemented within Leadership OS must belong to one of the workflow stages described below.

---

# Daily Workflow

Every day consists of six phases.

1. Startup
2. Morning Planning
3. Focused Work
4. Break Management
5. End of Day Review
6. Shutdown & Archive

Each phase has a clearly defined purpose and transition.

---

# Phase 1 — Startup

## Trigger

The application starts automatically when the operating system starts.

The application should restore its previous state before displaying any UI.

This includes:

- unfinished tasks
- active projects
- current configuration
- previous session state
- application preferences

Startup should complete silently.

If the previous day was not properly closed, Leadership OS should detect this and automatically transition into the Morning Planning phase.

---

# Phase 2 — Morning Planning

## Objective

Determine today's execution plan before beginning work.

The planning session should take only a few minutes.

This is the only time during the day where the user is expected to actively organize work.

---

## Step 1 — Welcome

Display a short summary of yesterday.

Example information includes:

- completed tasks
- unfinished tasks
- total focused work time
- last shutdown time

The summary should provide context without overwhelming the user.

---

## Step 2 — Carry Forward

If unfinished tasks exist from previous days, present them to the user.

For every unfinished task the user can choose to:

- Continue today
- Reschedule
- Archive
- Delete

No task should automatically disappear.

---

## Step 3 — Create Today's Plan

The user creates today's task list.

Each task contains:

- title
- priority
- optional deadline
- optional notes

The application should encourage entering tasks quickly without excessive configuration.

---

## Step 4 — Prioritize

Tasks are ordered according to importance.

Leadership OS should always know:

- what should be done first
- what should be done next
- what can wait

The user may reorder tasks manually.

---

## Step 5 — Define Deadlines

Tasks may optionally receive a deadline.

Examples include:

- 11:00 AM
- Before Lunch
- 5:00 PM
- Before Dinner
- End of Day

Deadlines exist to improve awareness rather than create pressure.

---

## Step 6 — Begin Work

Once planning is complete, Leadership OS enters Focus Mode.

The planning interface closes.

The workspace overlay becomes active.

---

# Phase 3 — Focused Work

This is the primary operating mode of Leadership OS.

The application should remain visible without interrupting the user's workflow.

---

## Active Task

Exactly one task is active.

The overlay continuously displays:

- current task
- elapsed time
- remaining deadline (if applicable)
- next task

The user should never wonder:

"What am I supposed to be working on?"

---

## Task Switching

The current task may change at any time.

Switching should require minimal effort.

Possible triggers include:

- keyboard shortcut
- quick command palette
- overlay interaction

Task switching immediately updates:

- timer
- activity log
- current state

---

## Timer

Every active task records:

- start time
- stop time
- total duration

The timer should continue running until:

- task changes
- break begins
- application exits
- task completes

---

## Task Completion

When work finishes:

- timer stops
- completion time is recorded
- task moves into Completed
- next task becomes active

If no tasks remain, Leadership OS enters an Idle state until new work is selected.

---

## Deadline Awareness

Leadership OS should quietly monitor deadlines.

When a deadline approaches, the application may display subtle reminders.

Notifications should be informative rather than disruptive.

---

# Phase 4 — Break Management

Breaks are considered part of the workday.

Leadership OS should distinguish between productive work and intentional rest.

---

## Starting a Break

The user may begin a break manually.

Examples include:

- Lunch
- Dinner
- Tea Break
- Personal Break

Beginning a break pauses the active task timer.

---

## Returning

When the user returns:

- break ends
- timer resumes
- previous task becomes active again

The transition should require only a single action.

---

# Phase 5 — End of Day Review

The workday concludes with a structured review.

Reflection is mandatory because it transforms daily activity into long-term knowledge.

---

## Daily Questions

Leadership OS asks three questions.

1. What did you accomplish today?

2. What slowed you down today?

3. What is the first thing you should do tomorrow?

Future versions may include optional reflection questions.

---

## Carry Forward

Incomplete tasks are reviewed.

The user decides whether each task should:

- continue tomorrow
- be rescheduled
- be archived
- be deleted

Nothing should silently disappear.

---

## Summary

Leadership OS prepares the day's summary.

The summary includes:

- completed tasks
- unfinished tasks
- work duration
- break duration
- task timeline
- reflections

---

# Phase 6 — Shutdown & Archive

After review, Leadership OS archives the day.

---

## Daily Note

A Markdown file is automatically generated.

The note contains:

- date
- planned tasks
- completed tasks
- carried tasks
- timeline
- reflections
- statistics

The file is saved to the configured Obsidian vault.

Example:

~/Documents/Obsidian/Daily Notes/2026-07-09.md

---

## Prepare Tomorrow

Leadership OS saves:

- unfinished tasks
- application state
- configuration
- preferences

The next startup should immediately continue from this information.

---

# Exceptional Scenarios

## Computer Shutdown

If the computer powers off unexpectedly:

- active timers are recovered
- unfinished tasks remain
- no data is lost

---

## Missed End-of-Day Review

If the application was closed without completing the daily review:

The next startup begins by asking the user to complete yesterday before planning today.

---

## Empty Day

If the user creates no tasks:

Leadership OS remains available in Idle Mode.

The application should never force work where none exists.

---

# Workflow Summary

```
System Startup
      │
      ▼
Morning Planning
      │
      ▼
Focus Mode
      │
      ├──────────────┐
      ▼              │
Break               Task Switch
      │              │
      └──────┬───────┘
             ▼
Continue Working
             │
             ▼
End of Day Review
             │
             ▼
Generate Markdown
             │
             ▼
Save State
             │
             ▼
Shutdown
```

---

# Design Principle

The workflow should feel like a quiet daily ritual rather than a productivity system.

The user plans once, executes throughout the day, reflects once, and leaves behind a permanent record with minimal effort.