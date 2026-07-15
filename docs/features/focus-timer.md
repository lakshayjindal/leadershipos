# Focus Timer

## Purpose

The Focus Timer measures intentional work.

Unlike a traditional Pomodoro timer, the Focus Timer does not tell the user **when to work**. Instead, it records **when the user is actually working**.

Its primary responsibility is to build an accurate history of focused work while providing gentle awareness of time.

The timer is a recorder, not a taskmaster.

---

# Philosophy

Time should be observed, not controlled.

Leadership OS trusts the user to decide:

- when to start working
- when to take breaks
- when to stop

The timer exists to answer:

> **"How long did I actually spend working on this?"**

rather than

> **"Have I worked long enough?"**

---

# Core Responsibilities

The Focus Timer is responsible for:

- Measuring active work.
- Tracking focus sessions.
- Recording break durations.
- Updating the overlay.
- Contributing statistics.
- Providing timeline events.
- Supporting journal generation.

The timer should never pressure the user.

---

# Timer States

The timer operates in one of the following states.

```
Idle

↓

Running

↓

Paused

↓

Running

↓

Stopped
```

Only one state may be active at a time.

---

# Idle

The timer is inactive.

Characteristics:

- No active task.
- No elapsed time.
- Waiting for user action.

This is the default state after application startup.

---

# Running

A task is actively being worked on.

The timer increments continuously.

Information recorded:

- Start Time
- Elapsed Time
- Current Task
- Session Duration

Only one timer may be running at any time.

---

# Paused

The user has temporarily stopped working.

Examples:

- Tea break
- Phone call
- Quick discussion
- Context switch

Paused time is **not** counted as Focus Time.

The current work session remains open until resumed or stopped.

---

# Stopped

The work session has ended.

Stopping the timer:

- Records session duration.
- Saves elapsed time.
- Updates task statistics.
- Creates a timeline event.

Stopping does not necessarily complete the task.

---

# Starting the Timer

The timer starts when:

- A task becomes Active.
- The user explicitly starts work.

Starting the timer performs:

- Record session start time.
- Update application state.
- Update overlay.
- Begin elapsed time tracking.

---

# Pausing the Timer

The user may pause work at any time.

Examples:

- Tea break
- Lunch
- Dinner
- Unexpected interruption

Paused duration should be recorded separately.

Focus Time should exclude paused periods.

---

# Resuming

Resuming continues the existing work session.

The timer resumes from the previous elapsed value.

No new task is created.

---

# Stopping

Stopping ends the current work session.

The timer records:

- End Time
- Session Duration
- Focus Duration

The timer returns to the Idle state unless another task is immediately started.

---

# Automatic Stops

The timer may stop automatically when:

- Task is completed.
- User switches tasks.
- End-of-Day Review begins.

Automatic stopping should never discard elapsed work.

---

# Work Sessions

Every uninterrupted period of focused work is recorded as a Work Session.

Example

```
Task

Implement Credits

Sessions

09:00 – 10:30

11:00 – 12:10

14:15 – 15:00
```

Total Focus Time is the sum of all work sessions.

---

# Session Recording

Each session stores:

- Task
- Start Time
- End Time
- Focus Duration
- Pause Duration

Sessions become immutable once completed.

---

# Overlay Integration

While running, the overlay displays:

Current Task

Elapsed Focus Time

Optional Deadline Countdown

Example

```
Implement Credits

01:42:15

Due 5:00 PM
```

The overlay updates continuously.

---

# Break Integration

Starting a break automatically pauses the timer.

Ending a break resumes it.

Breaks are recorded separately from work sessions.

Examples:

- Tea Break
- Lunch
- Dinner

---

# Task Switching

Switching tasks performs:

```
Stop Current Session

↓

Save Statistics

↓

Activate New Task

↓

Start New Timer
```

Task switching should require minimal interaction.

---

# Time Resolution

The timer records time with second-level precision.

Displayed values:

```
HH:MM:SS
```

Internal storage may use milliseconds if supported.

---

# Accuracy

The timer should remain accurate even if:

- Application loses focus.
- Window is minimized.
- Overlay is hidden.
- User switches applications.

Leadership OS measures work, not window activity.

---

# Recovery

If the application unexpectedly closes:

Leadership OS restores:

- Active Task
- Timer State
- Elapsed Time

The user should be asked whether to continue the recovered session.

No recorded work should be lost.

---

# Daily Statistics

The Focus Timer contributes:

- Total Focus Time
- Total Break Time
- Number of Sessions
- Average Session Length
- Longest Session
- Shortest Session

These statistics appear in the Daily Journal.

---

# Session History

Every completed session becomes part of the historical timeline.

Example

```
09:00 Started

10:30 Tea Break

10:45 Resume

12:15 Completed
```

The timeline is generated automatically.

---

# Performance Requirements

The timer should:

- Update once per second.
- Consume minimal CPU resources.
- Continue running accurately over long sessions.

Drift should be negligible over an entire workday.

---

# Accessibility

Timer information should remain readable at all times.

Users should be able to:

- Start
- Pause
- Resume
- Stop

using only the keyboard.

---

# Future Expansion

Future versions may introduce:

- Pomodoro Mode
- Deep Work Sessions
- Session Goals
- Focus Streaks
- Idle Detection
- Automatic Pause Suggestions
- Calendar Integration

These features should remain optional.

The default timer should always preserve its simple, manual workflow.

---

# Design Principles

The Focus Timer should be:

Accurate.

Reliable.

Lightweight.

Non-intrusive.

Always available.

The timer should quietly observe work without attempting to manage or optimize the user's behavior.

---

# Final Principle

The Focus Timer exists to measure attention, not enforce discipline.

Leadership OS trusts the user to decide when meaningful work begins and ends.

Its responsibility is to preserve an honest record of focused effort, allowing every work session to become part of the user's long-term history without introducing unnecessary structure or interruption.