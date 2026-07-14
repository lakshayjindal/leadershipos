# Deadlines

## Purpose

Deadlines provide temporal awareness for tasks.

They answer one question:

> **"When should this task ideally be completed?"**

Deadlines help users manage time without introducing unnecessary pressure.

Leadership OS treats deadlines as guidance rather than enforcement.

---

# Philosophy

A deadline should help the user make better decisions.

It should never become a source of anxiety.

Leadership OS exists to support execution, not punish missed schedules.

Missing a deadline is information, not failure.

---

# Deadline Types

Leadership OS supports two types of deadlines.

## Absolute Deadlines

An exact point in time.

Examples

```
10:30 AM

2:00 PM

5:45 PM

9:00 PM
```

Absolute deadlines are stored internally as timestamps.

---

## Relative Deadlines

Deadlines relative to the user's daily schedule.

Examples

```
Before Lunch

Before Dinner

End of Day
```

Relative deadlines are automatically converted into timestamps using the configured work schedule.

Example

```
Dinner Time

7:30 PM

↓

Before Dinner

7:30 PM
```

---

# Optional Feature

Deadlines are optional.

Tasks without deadlines are fully supported.

Leadership OS should never require a deadline during task creation.

---

# Assigning Deadlines

Deadlines may be assigned:

- During Morning Planning
- While editing a task
- At any point during the day

Changing a deadline should never affect:

- Focus Time
- Work Sessions
- Completion History

---

# Deadline States

A deadline exists in one of four states.

## No Deadline

No deadline assigned.

No reminders.

No countdown.

---

## Upcoming

Current time is before the deadline.

The Overlay may display:

```
Due in 2h 15m
```

---

## Due

Current time has reached the deadline.

The task remains active.

Leadership OS records that the deadline has been reached.

No automatic state changes occur.

---

## Overdue

Current time exceeds the deadline.

The task remains fully editable.

The user may continue working normally.

Being overdue should never:

- stop the timer
- archive the task
- reduce priority
- generate repeated warnings

---

# Deadline Countdown

If a task has a deadline, the overlay may display a live countdown.

Example

```
Current Task

Implement Credits

Due In

01:42:15
```

The countdown is informational.

It should remain subtle.

---

# Notifications

Deadlines may generate notifications.

Supported events include:

Upcoming Deadline

Example

```
Due in 30 minutes.
```

Deadline Reached

Example

```
Deadline reached.

Continue when appropriate.
```

Overdue

Example

```
Task is overdue.
```

Each notification should occur only once.

Leadership OS should never repeatedly remind the user.

---

# Editing Deadlines

Users may modify deadlines at any time.

Examples

```
5:00 PM

↓

7:00 PM
```

or

```
Before Dinner

↓

End of Day
```

Historical work should remain unchanged.

---

# Removing Deadlines

Removing a deadline simply returns the task to the "No Deadline" state.

No other task information changes.

---

# Deadline Indicators

Deadlines should be visible in:

- Daily Planner
- Task List
- Overlay
- Task Details
- Search Results

Visibility should remain subtle.

The deadline should never dominate the interface.

---

# Deadline Ordering

Users may sort tasks by deadline.

Default ordering:

```
Earliest

↓

Latest

↓

No Deadline
```

Tasks without deadlines always appear after dated tasks when sorting by deadline.

---

# Deadline Validation

Leadership OS validates deadlines before saving.

Examples

Valid

```
5:30 PM
```

Invalid

```
25:61 PM
```

Relative deadlines must correspond to configured schedule events.

Example

```
Before Dinner
```

requires

```
Dinner Time
```

to exist in the user's configuration.

---

# End-of-Day Behavior

If a task remains unfinished after its deadline:

Leadership OS asks the user what should happen.

Options include:

- Carry Forward
- Reschedule
- Archive
- Delete

The application should never automatically modify deadlines during carry forward.

The user decides.

---

# Analytics

Future versions may provide:

- Average deadline accuracy
- Frequently missed deadlines
- Deadline completion trends
- Average completion before deadline
- Deadline distribution

These reports are intended for reflection rather than evaluation.

---

# Time Zones

Leadership OS operates entirely in the user's local time zone.

No timezone conversions are required in Version 1.

Future synchronization features may introduce timezone awareness.

---

# Relative Deadline Resolution

Relative deadlines are resolved using configuration.

Example

```
Configuration

Lunch

1:00 PM

↓

Task

Before Lunch

↓

Resolved Deadline

1:00 PM
```

Changing Lunch Time automatically updates unresolved relative deadlines.

---

# Missed Deadlines

Missing a deadline has no automatic consequences.

Leadership OS intentionally avoids:

- Negative scoring
- Failure messages
- Productivity penalties
- Automatic priority changes
- Automatic rescheduling

The purpose of deadlines is awareness.

The user remains responsible for deciding how to respond.

---

# Accessibility

Deadline information should be distinguishable without relying solely on color.

Recommended indicators include:

- Icons
- Labels
- Typography
- Countdown text

Users with color vision deficiencies should receive the same information.

---

# Future Expansion

Potential future features include:

- Multiple deadlines per task
- Soft vs Hard deadlines
- Milestones
- Time blocking
- Calendar integration
- Deadline templates
- AI-assisted scheduling

These additions should preserve the simplicity of the Version 1 deadline system.

---

# Design Principles

Deadlines should be:

Optional.

Informative.

Flexible.

Non-intrusive.

Predictable.

Leadership OS should help users remain aware of time without making time the center of attention.

---

# Final Principle

A deadline is a promise to yourself—not a rule enforced by the software.

Leadership OS should quietly remind the user of that promise while respecting that priorities change, unexpected work appears, and productive days rarely follow a perfect schedule.