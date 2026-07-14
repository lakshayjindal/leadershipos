# Timer Engine

## Purpose

The Timer Engine is responsible for accurately recording productive work throughout the day.

Unlike a traditional stopwatch, the Timer Engine automatically tracks work sessions based on the user's workflow and application state.

Its primary responsibility is to answer the question:

> "How did I spend my working day?"

Every recorded work session contributes to the historical timeline, daily journal, and productivity statistics.

The Timer Engine is designed to operate silently in the background with minimal user interaction.

---

# Objectives

The Timer Engine must:

- Track productive work automatically.
- Record every work session.
- Handle interruptions gracefully.
- Support pause and resume.
- Recover from unexpected shutdowns.
- Produce reliable historical records.
- Never lose tracked time.

Accuracy is more important than visual presentation.

---

# Core Philosophy

Leadership OS does not measure productivity by counting completed tasks.

It measures execution by recording focused work.

The Timer Engine exists to preserve an accurate history of work rather than to pressure the user with time metrics.

Timers are observational, not motivational.

---

# Terminology

## Task

A unit of planned work.

Example:

Implement Overlay

---

## Work Session

One uninterrupted period spent working on a task.

Example:

09:00 → 10:15

Every work session belongs to exactly one task.

---

## Focus Time

The total duration of all work sessions for a task.

Focus Time is calculated rather than stored manually.

---

## Break

A period during which productive work is intentionally paused.

Breaks never contribute to Focus Time.

---

# Responsibilities

The Timer Engine is responsible for:

- Starting timers.
- Stopping timers.
- Pausing timers.
- Resuming timers.
- Recording work sessions.
- Calculating elapsed time.
- Calculating total task duration.
- Maintaining session history.
- Recovering interrupted sessions.

The Timer Engine is not responsible for:

- Displaying timers.
- Managing tasks.
- Rendering overlays.
- Sending notifications.

Those responsibilities belong to other subsystems.

---

# Timer Lifecycle

Every work session follows the same lifecycle.

```
Idle
 │
 ▼
Started
 │
 ▼
Running
 │
 ├──────────────┐
 │              │
 ▼              ▼
Paused      Completed
 │
 ▼
Running
 │
 ▼
Completed
```

---

# Starting a Timer

A timer starts automatically when:

- A task becomes Active.

Starting a timer performs the following actions:

- Records the start timestamp.
- Creates a new Work Session.
- Updates the current application state.
- Begins elapsed time tracking.

The user should rarely need to start timers manually.

---

# Running State

While running:

The Timer Engine continuously tracks elapsed time.

The engine should not permanently write to storage every second.

Instead, elapsed time should be calculated using:

Current Time

minus

Session Start Time

This reduces unnecessary disk activity.

---

# Pausing

A running timer pauses when:

- Lunch begins.
- Dinner begins.
- Manual break starts.
- Computer enters sleep.
- Application enters Break State.

Pausing records:

Pause Timestamp

Current Elapsed Duration

The current Work Session is temporarily suspended.

---

# Resuming

When work resumes:

A new Work Session begins.

Leadership OS intentionally creates multiple work sessions rather than one long interrupted session.

Example:

09:00 → 10:20

11:00 → 12:30

15:00 → 16:10

Each period becomes an independent Work Session.

---

# Completing a Task

Completing a task performs:

- Stop current timer.
- Record completion timestamp.
- Close current Work Session.
- Calculate total Focus Time.
- Publish Task Completed event.

No further work sessions may be added after completion.

---

# Timer Accuracy

Leadership OS prioritizes correctness.

Time should always be calculated using absolute timestamps.

Avoid incrementing counters every second.

Preferred approach:

```
Elapsed Time =
Current Timestamp
-
Session Start Timestamp
```

This guarantees accurate recovery after:

- Sleep
- Suspend
- Application restart
- Clock drift (within reasonable limits)

---

# Recovery

If Leadership OS closes unexpectedly:

On next startup the Timer Engine should inspect:

Previous Application State

Current Active Task

Last Recorded Session

If an interruption occurred:

The session should be safely closed at the last known timestamp.

The application should never invent missing work time.

---

# Sleep & Resume

If the operating system sleeps:

The Timer Engine should detect the suspension.

Upon wake:

The user is asked whether they:

- Continued working
- Took a break

This prevents incorrectly counting sleep time as productive work.

---

# Timer Precision

Display precision:

HH:MM:SS

Internal precision:

Milliseconds

Journal precision:

Minutes

Analytics precision:

Seconds

Different consumers may use different levels of precision while sharing the same underlying timestamps.

---

# Session Recording

Each Work Session stores:

- Task Identifier
- Start Time
- End Time
- Duration

Sessions are immutable once completed.

---

# Multiple Sessions

Example:

```
Task:
Implement Timer

09:00 → 10:15

11:10 → 12:30

14:45 → 15:50
```

Produces:

Focus Time

3 Hours 40 Minutes

Number of Sessions

3

---

# Statistics

The Timer Engine provides:

Current Session Duration

Task Focus Time

Daily Focus Time

Average Session Length

Longest Session

Shortest Session

Total Sessions

These values are derived rather than manually maintained whenever possible.

---

# Event Publishing

The Timer Engine publishes events.

Examples:

Timer Started

Timer Paused

Timer Resumed

Timer Stopped

Session Completed

Task Completed

Other modules subscribe to these events.

The Timer Engine never updates the UI directly.

---

# Performance Requirements

The Timer Engine should:

Consume minimal CPU.

Perform minimal disk writes.

Run continuously.

Remain accurate over long periods.

Operate correctly even after running for multiple consecutive days.

---

# Failure Handling

The Timer Engine should recover from:

Application crash

Power failure

System restart

Unexpected shutdown

Sleep

Hibernate

No completed session should ever be lost.

---

# Design Principles

The Timer Engine should be:

Accurate

Predictable

Recoverable

Independent

Deterministic

Invisible

The user should rarely think about the timer.

It should quietly observe work while allowing the user to focus entirely on execution.

---

# Final Principle

The Timer Engine is not a stopwatch.

It is the historical recorder of the user's work.

Every journal, statistic, timeline, and reflection ultimately depends upon the integrity of the information captured by this engine.