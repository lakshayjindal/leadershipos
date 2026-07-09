# Data Model

## Purpose

This document defines the logical data model for Leadership OS.

The data model represents the core information required by the application. It is independent of any specific database technology or programming language.

The goal is to identify the entities that exist within Leadership OS, the information they contain, and the relationships between them.

Implementation details such as SQL tables, ORM models, or serialization formats are intentionally excluded.

---

# Data Model Overview

Leadership OS revolves around six primary entities.

- Day
- Task
- Work Session
- Break Session
- Reflection
- Configuration

Together, these entities represent everything required to reconstruct a complete working day.

---

# Entity Relationship Overview

```
Day
│
├── Tasks (1:N)
│      │
│      └── Work Sessions (1:N)
│
├── Break Sessions (1:N)
│
├── Reflection (1:1)
│
└── Daily Summary (1:1)

Configuration (Independent)
```

---

# Entity: Day

## Purpose

Represents one calendar day.

Every task, session, break, and reflection belongs to exactly one Day.

A Day acts as the primary container for all work performed during that date.

---

## Attributes

Unique Identifier

Date

Start Time

End Time

Current Status

Created Timestamp

Updated Timestamp

---

## Relationships

One Day contains many Tasks.

One Day contains many Break Sessions.

One Day contains one Reflection.

One Day contains one Daily Summary.

---

# Entity: Task

## Purpose

Represents a unit of work.

Tasks are the primary objects the user interacts with throughout the day.

---

## Attributes

Unique Identifier

Title

Description

Priority

Status

Deadline

Estimated Duration

Actual Duration

Creation Time

Activation Time

Completion Time

Display Order

Notes

---

## Relationships

One Task belongs to one Day.

One Task contains many Work Sessions.

---

# Entity: Work Session

## Purpose

Represents one uninterrupted period of focused work on a task.

A task may contain many work sessions.

Example:

Task:
Implement Overlay

Work Sessions:

09:15 → 10:05

11:30 → 12:10

15:20 → 16:00

The total task duration is calculated from all work sessions.

---

## Attributes

Unique Identifier

Task Identifier

Start Time

End Time

Duration

Paused Duration

Created Timestamp

---

## Relationships

Each Work Session belongs to one Task.

---

# Entity: Break Session

## Purpose

Represents intentional non-working time.

Breaks are independent of tasks.

---

## Attributes

Unique Identifier

Break Type

Start Time

End Time

Duration

Notes (Optional)

---

## Supported Types

Lunch

Dinner

Tea

Personal

Meeting

Custom

---

## Relationships

Every Break belongs to one Day.

---

# Entity: Reflection

## Purpose

Represents the answers provided during the End-of-Day Review.

There is exactly one Reflection per Day.

---

## Attributes

Unique Identifier

Accomplishments

Challenges

Tomorrow's First Task

Additional Notes

Completion Timestamp

---

## Relationships

Reflection belongs to one Day.

---

# Entity: Daily Summary

## Purpose

Stores calculated information for a completed day.

This entity exists to simplify reporting and journal generation.

---

## Attributes

Total Planned Tasks

Completed Tasks

Carried Tasks

Archived Tasks

Deleted Tasks

Total Focus Time

Total Break Time

Completion Percentage

Longest Focus Session

Number of Work Sessions

Generated Markdown Path

Archive Timestamp

---

## Relationships

One Summary belongs to one Day.

---

# Entity: Configuration

## Purpose

Stores application preferences.

Configuration is independent of any specific day.

---

## Attributes

Working Hours

Lunch Time

Dinner Time

Overlay Position

Overlay Opacity

Theme

Markdown Vault Path

Journal Directory

Keyboard Shortcuts

Notification Preferences

Startup Behavior

---

# Enumerations

## Task Status

Pending

Active

Completed

Archived

Deleted

Carried Forward

---

## Task Priority

Critical

High

Medium

Low

---

## Application State

Startup

Planning

Working

Break

Idle

Review

Shutdown

---

## Break Type

Lunch

Dinner

Tea

Meeting

Personal

Custom

---

# Derived Values

The following values should never be manually entered.

Instead, they are calculated automatically.

Task Duration

Focus Time

Break Duration

Completion Percentage

Longest Session

Average Session Length

Total Productive Time

Daily Statistics

---

# Identity Rules

Every primary entity must have a stable unique identifier.

Identifiers must never change once assigned.

Relationships between entities should always use identifiers rather than titles or dates.

---

# Lifecycle

Day

Created

↓

Tasks Created

↓

Work Sessions Recorded

↓

Break Sessions Recorded

↓

Reflection Completed

↓

Summary Generated

↓

Markdown Exported

↓

Archived

---

# Persistence Requirements

The application must persist:

Tasks

Sessions

Breaks

Reflections

Configuration

Daily Summaries

Application State

No information should exist solely in memory.

---

# Future Expansion

The model should support future entities without modifying existing ones.

Possible additions include:

Projects

Goals

Habits

Tags

Analytics

Attachments

Plugins

Future entities should reference existing entities rather than duplicate information.

---

# Design Philosophy

Leadership OS stores facts rather than interpretations.

Facts include:

- what task existed
- when work started
- when work ended
- what the user wrote

Everything else—including statistics, reports, trends, and analytics—should be derived from those facts rather than stored independently whenever possible.