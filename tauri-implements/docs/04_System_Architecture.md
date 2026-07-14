# System Architecture

## Purpose

This document defines the architectural design of Leadership OS.

Rather than describing implementation details, it defines the major subsystems, their responsibilities, and how they interact with one another.

Leadership OS follows a modular architecture where every subsystem owns a single responsibility. Communication between subsystems should remain explicit and predictable.

---

# Architectural Principles

The architecture must satisfy the following principles:

- Single Responsibility
- Local First
- Offline by Default
- Event Driven
- Modular
- Recoverable
- Testable
- Extensible

Every module should solve exactly one problem.

---

# High-Level Architecture

```
┌────────────────────────────────────────────────────────────┐
│                        Leadership OS                       │
└────────────────────────────────────────────────────────────┘
                            │
                            ▼
                ┌─────────────────────────┐
                │      User Interface      │
                └─────────────────────────┘
                            │
                            ▼
                ┌─────────────────────────┐
                │    Application Core      │
                └─────────────────────────┘
                            │
        ┌─────────────┬─────────────┬─────────────┐
        ▼             ▼             ▼             ▼
 Task Engine     Timer Engine   Journal Engine   Notification Engine
        │             │             │             │
        └─────────────┴─────────────┴─────────────┘
                            │
                            ▼
                ┌─────────────────────────┐
                │     Persistence Layer    │
                └─────────────────────────┘
                            │
                            ▼
                SQLite Database / Markdown Files
```

---

# System Components

Leadership OS is composed of the following major components.

---

# 1. User Interface

## Responsibility

Provide all user interaction.

The UI should contain no business logic.

Responsibilities include:

- Morning planning
- Overlay
- Dialogs
- Settings
- Keyboard shortcuts
- Daily review
- Visual feedback

The UI communicates only with the Application Core.

---

# 2. Application Core

## Responsibility

Acts as the central coordinator.

Every user action passes through the Application Core.

Responsibilities include:

- State management
- Workflow transitions
- Validation
- Event dispatching
- Command execution

The Application Core contains the primary business logic.

It should not directly access the database.

---

# 3. Task Engine

## Responsibility

Manage the lifecycle of tasks.

Responsibilities include:

- Create tasks
- Update tasks
- Delete tasks
- Activate tasks
- Complete tasks
- Carry tasks forward
- Prioritize tasks

The Task Engine owns all task-related logic.

---

# 4. Timer Engine

## Responsibility

Track productive work sessions.

Responsibilities include:

- Start timer
- Pause timer
- Resume timer
- Stop timer
- Record sessions
- Calculate durations

The Timer Engine should remain independent from the UI.

---

# 5. Journal Engine

## Responsibility

Generate permanent daily records.

Responsibilities include:

- Collect daily statistics
- Build Markdown
- Save notes
- Maintain timeline
- Export history

The Journal Engine writes only after the End-of-Day Review.

---

# 6. Notification Engine

## Responsibility

Monitor important events and display notifications.

Examples include:

- Upcoming deadlines
- End-of-day reminder
- Planning reminder
- Break reminders

The Notification Engine never owns business logic.

It only reacts to events.

---

# 7. Persistence Layer

## Responsibility

Read and write data.

The persistence layer hides storage implementation details from the rest of the application.

Responsibilities include:

- Save tasks
- Save settings
- Save timers
- Load previous state
- Recover after crashes

The rest of the application should never know how data is physically stored.

---

# 8. Configuration Manager

## Responsibility

Maintain application settings.

Examples include:

- Working hours
- Lunch time
- Dinner time
- Theme
- Overlay position
- Vault location
- Keyboard shortcuts

Configuration changes should immediately become available to the application.

---

# 9. State Manager

## Responsibility

Maintain the current state of Leadership OS.

Possible states include:

- Startup
- Planning
- Working
- Break
- Idle
- Review
- Shutdown

Only one state may be active at any given time.

The State Manager controls valid transitions.

---

# 10. Event Bus

## Responsibility

Allow modules to communicate without direct dependencies.

Examples:

Task Completed

↓

Timer Stops

↓

Journal Timeline Updates

↓

Overlay Refreshes

↓

Notification Evaluates Deadline

Instead of calling each module directly, the Application Core emits events.

Modules subscribe only to events they care about.

---

# Data Flow

A typical task completion follows this sequence.

```
User

↓

User Interface

↓

Application Core

↓

Task Engine

↓

Event Bus

↓

Timer Engine
Journal Engine
Overlay
Notification Engine

↓

Persistence Layer

↓

SQLite
```

Every action follows this pattern.

---

# Startup Sequence

```
Application Launch

↓

Load Configuration

↓

Load Database

↓

Restore Previous State

↓

Recover Active Session

↓

Initialize Modules

↓

Display Morning Planning
```

---

# Shutdown Sequence

```
End-of-Day Review

↓

Generate Markdown

↓

Save Tasks

↓

Save Settings

↓

Persist Application State

↓

Exit
```

---

# Dependency Rules

Modules may only communicate through approved interfaces.

```
UI
 │
 ▼
Application Core
 │
 ├──────────────┐
 ▼              ▼
Task Engine   Timer Engine
 │              │
 └──────┬───────┘
        ▼
 Event Bus
        ▼
Persistence Layer
```

Direct communication between unrelated modules should be avoided.

Example:

The Timer Engine should never directly update the Overlay.

Instead:

Timer Engine

↓

Event Bus

↓

Overlay receives update

---

# Storage Strategy

Leadership OS maintains two forms of storage.

## Structured Storage

SQLite

Used for:

- tasks
- timers
- settings
- application state
- sessions

---

## Human Readable Storage

Markdown

Used for:

- daily journals
- historical records
- long-term archive

SQLite stores operational data.

Markdown stores historical knowledge.

---

# Error Recovery

The application should recover gracefully from unexpected failures.

Recovery includes:

- unfinished timers
- incomplete tasks
- interrupted shutdown
- power failure
- application crash

No user data should be lost.

---

# Future Expansion

The architecture should support additional modules without changing existing ones.

Examples:

- Analytics Engine
- AI Reflection Assistant
- Calendar Integration
- Reporting Engine
- Plugin System

These should integrate through the Event Bus and Application Core rather than modifying existing modules.

---

# Summary

Leadership OS follows a modular, event-driven architecture where each subsystem owns a single responsibility.

The Application Core coordinates workflow, specialized engines perform domain-specific work, and the Persistence Layer guarantees durability.

This separation ensures the application remains maintainable, extensible, and resilient as new capabilities are introduced.