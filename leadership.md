# Leadership OS
*A desktop application for Ubuntu that reinforces Ownership, Accountability, and Daily Reflection.*

---

# Vision

Leadership OS is a lightweight desktop application designed to help engineers build disciplined daily habits based on leadership frameworks rather than simply managing tasks.

The application focuses on two daily rituals:

1. Morning Planning
2. End-of-Day Reflection

The application is **not** intended to become a full-featured project management system. It exists solely to guide the user through intentional planning, execution, and reflection.

---

# Primary Goals

- Encourage deliberate planning every morning.
- Force task prioritization.
- Track estimated vs actual effort.
- Remind the user when time estimates are exceeded.
- Encourage conscious decision making.
- Capture lessons learned every day.
- Automatically maintain an Obsidian daily journal.

---

# Target Platform

- Ubuntu Desktop
- Native Linux application
- Local-first
- No cloud dependency
- No user accounts
- Single-user application

---

# Daily Workflow

## Morning

User presses:

Start My Day

The application opens a guided planning workflow.

---

### Step 1
Load Previous Tasks

Load all incomplete tasks from previous days.

Example

Yesterday

- Finish Celery Queue
- Deploy Supervisor
- Resume redesign

These tasks appear already populated.

---

### Step 2
Task Editing Screen

The user may

- edit tasks
- delete tasks
- mark tasks completed
- create new tasks
- reorder tasks

---

### Step 3
Priority Assignment

Each task must be assigned one of:

- Urgent
- Important
- Urgent & Important

No task can remain unclassified.

---

### Step 4
Time Estimate

Every task requires

Estimated Duration

Examples

15 min

30 min

1 hour

3 hours

No task can be started without an estimate.

---

### Step 5
Execution Queue

Tasks appear ordered by

1. Urgent & Important
2. Important
3. Urgent

The dashboard now becomes active.

---

# Dashboard

Shows

Current Task

Remaining Estimated Time

Today's Progress

Completed Tasks

Pending Tasks

Overdue Tasks

---

Each task has

Start

Pause

Resume

Complete

Skip

Extend Time

buttons.

---

# Notifications

When the estimated duration expires

Desktop notification

Example

----------------------------------

Time is up for

Separate Celery Workers

Did you

✓ Finish

+15 minutes

+30 minutes

Still Working

Switch Task

----------------------------------

The user must make an explicit decision.

---

If the user ignores the notification

Repeat every

5 minutes

until acknowledged.

---

# End Day

User presses

End My Day

The application checks

Are there unfinished tasks?

If yes

Offer

Carry Forward

or

Mark Cancelled

---

# Reflection Questions

Prompt the user with

## 1

What Went Well?

Large text input

---

## 2

What Went Wrong?

Large text input

---

## 3

What Could Be Improved?

Large text input

---

The reflection cannot be skipped without confirmation.

---

# Daily Note Generation

After submission

Automatically generate

~/Documents/obsidian/days/YYYY-MM-DD.md

---

Example

# 2026-07-07

## Tasks

### Completed

- [x] Separate Celery queues
- [x] Add Supervisor configs

### Carried Forward

- [ ] Resume redesign

---

## Priority Matrix

### Urgent & Important

- Separate Celery queues

### Important

- Resume redesign

### Urgent

- HR follow-up

---

## Time Tracking

| Task | Estimated | Actual |
|------|-----------|--------|
| Celery | 2h | 2h 15m |
| Resume | 1h | 0h |

---

## Reflection

### What Went Well

...

---

### What Went Wrong

...

---

### What Could Be Improved

...

---

Generated automatically by Leadership OS.

---

# Task Persistence

Tasks are stored locally.

Fields

- UUID
- Title
- Description
- Created Date
- Completed Date
- Priority
- Status
- Estimated Duration
- Actual Duration
- Carry Forward Count

---

# Notifications

Support native Ubuntu notifications.

Notifications include

Task Finished

Break Reminder

Planning Reminder

Reflection Reminder

---

# Statistics

Dashboard should display

Tasks Completed Today

Estimated Time

Actual Time

Average Estimation Accuracy

Carry Forward Count

Completion %

Current Streak

Reflection Streak

Planning Streak

---

# Weekly Review (Future)

Automatically summarize

Last 7 days

Average completion

Most common improvement

Most common mistake

Most productive day

Most carried-forward task

---

# Non Functional Requirements

Application starts in under 2 seconds.

Runs offline.

Uses minimal RAM.

Automatically saves changes.

No internet required.

No telemetry.

---

# Technology

Frontend

- React
- TypeScript

Desktop

- Tauri

Backend

- Rust

Storage

SQLite

Notifications

Native Linux notifications

Markdown Generation

Local filesystem

---

# Future Enhancements

- Pomodoro Mode
- Calendar Integration
- GitHub Issue Import
- Jira Import
- VSCode Integration
- AI Reflection Summaries
- Weekly Leadership Report
- Monthly Growth Dashboard
- Habit Tracking
- Energy Tracking
- Deep Work Sessions
