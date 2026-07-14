# Task Priority

## Purpose

Task Priority defines the relative importance of tasks within a working day.

Its purpose is to help the user decide **what deserves attention first**, not to dictate a rigid execution order.

Priority is a planning tool, not a scheduling constraint.

Leadership OS uses priority to improve decision-making while always leaving the final choice to the user.

---

# Philosophy

Priority answers one question:

> **"If I could complete only one more task today, which one should it be?"**

Priority measures importance—not urgency, difficulty, or estimated effort.

A small but critical task should rank above a large but low-impact task.

---

# Priority Levels

Leadership OS supports four priority levels.

## Critical

Highest importance.

Characteristics:

- Blocks other work.
- Time-sensitive.
- High impact.
- Significant consequences if delayed.

Examples:

- Fix production outage.
- Submit tax documents.
- Deploy urgent hotfix.

---

## High

Important work that should ideally be completed today.

Characteristics:

- Important to current objectives.
- May have deadlines.
- Delaying creates future pressure.

Examples:

- Review pull requests.
- Complete feature implementation.
- Prepare client presentation.

---

## Medium

Useful work that contributes to progress but is not immediately important.

Examples:

- Documentation.
- Refactoring.
- Code cleanup.
- Learning tasks.

Medium priority tasks often fill available time after higher-priority work has been completed.

---

## Low

Nice-to-have work.

Examples:

- Organize files.
- UI polishing.
- Optional improvements.
- Small experiments.

Low priority tasks should never prevent higher-priority work from being completed.

---

# Priority vs Deadline

Priority and deadlines represent different concepts.

Priority answers:

"What is most important?"

Deadline answers:

"When should it be finished?"

Example:

Task

```
Fix Documentation
```

Priority

High

Deadline

End of Day

Example:

Task

```
Renew Passport
```

Priority

Critical

Deadline

Two weeks from now

The application must treat these independently.

---

# Priority vs Execution Order

Priority is not execution order.

Users remain free to complete tasks in any sequence.

Example

```
Priority

Critical
Fix Production Bug

High
Review Pull Requests

Medium
Update Documentation

Low
Organize Downloads
```

The user may choose to complete Documentation before Pull Requests.

Leadership OS should support this without warning or judgment.

---

# Default Priority

New tasks should receive:

Medium

unless explicitly specified by the user.

This provides sensible behavior while minimizing required input during task creation.

---

# Changing Priority

Priority may be changed at any time.

Changing priority should:

- Update the task immediately.
- Preserve task history.
- Never affect recorded work sessions.
- Never alter completion timestamps.

Changing priority is a planning decision, not a historical event.

---

# Visual Representation

Priority should be recognizable at a glance.

Recommended visual indicators include:

Critical

Highest emphasis.

High

Strong emphasis.

Medium

Normal emphasis.

Low

Subtle emphasis.

Color should reinforce meaning but should never be the only indicator.

Users with color vision deficiencies must still distinguish priorities through typography or icons.

---

# Sorting Behavior

Users may sort tasks by priority.

Default order:

```
Critical

↓

High

↓

Medium

↓

Low
```

Within the same priority, Display Order determines presentation.

---

# Filtering

Users may filter tasks by priority.

Supported filters:

- Critical
- High
- Medium
- Low

Multiple priorities may be selected simultaneously.

---

# Overlay Behavior

The overlay should display the priority of the current task.

The representation should remain subtle.

The overlay exists to communicate focus rather than urgency.

---

# Notifications

Priority alone should never trigger notifications.

Notifications are driven by:

- Deadlines
- Application State
- User actions

Priority is informational.

---

# Journal Integration

The Daily Journal should preserve the priority assigned at the time the task was completed.

This provides historical context when reviewing previous work.

Example

```md
- [x] Implement Credits System
  Priority: High
```

---

# Analytics

Future versions may use priority for reporting.

Examples include:

- Critical tasks completed.
- High-priority completion rate.
- Average completion time by priority.
- Distribution of work across priorities.

Analytics should describe behavior rather than evaluate it.

---

# Validation Rules

Every task must have exactly one priority.

Valid values are:

- Critical
- High
- Medium
- Low

Unknown priority values should never be accepted.

---

# Future Expansion

Future versions may support:

- Custom priority labels.
- Numeric priorities.
- Project-specific priorities.
- Dynamic priorities.
- AI-assisted prioritization.

These features should remain optional and must not replace the four standard priority levels by default.

---

# Design Principles

Task Priority should be:

Simple.

Understandable.

Flexible.

Consistent.

Supportive.

Priority exists to help the user make better decisions—not to pressure them into following a predefined order.

---

# Final Principle

Priority is a guide, not a command.

Leadership OS should help users recognize what matters most while respecting that real work is dynamic and that the user—not the application—always makes the final decision about what to work on next.