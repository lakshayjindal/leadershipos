# Document 15 — Implementation Rules

## Purpose

This document defines the engineering principles that every implementation of Leadership OS must follow.

The previous documents describe **what the application should do**.

This document describes **how it should be built**.

These rules exist to ensure the codebase remains maintainable, predictable, performant, and consistent regardless of whether code is written by humans or AI assistants.

When implementation decisions conflict with these rules, these rules take precedence unless explicitly documented otherwise.

---

# Core Philosophy

Leadership OS is:

- Local-first
- Offline-first
- Keyboard-first
- Privacy-first
- Performance-first

Every implementation decision should reinforce these principles.

---

# Architecture Principles

## Single Source of Truth

Every piece of data should have exactly one owner.

Avoid duplicate state.

Bad

```
Task stored in database

↓

Copied into UI state

↓

Copied into timer

↓

Copied into overlay
```

Good

```
Database

↓

Repository

↓

Application State

↓

Views
```

The UI should observe state, not own it.

---

## Business Logic Lives in Rust

The frontend should contain as little business logic as possible.

Frontend responsibilities:

- Rendering
- User interaction
- Input validation
- Animations
- Navigation

Rust responsibilities:

- Timer engine
- Planning
- Scheduling
- Journal generation
- Search
- File management
- Notifications
- Recovery
- Configuration
- History
- Statistics

If logic could reasonably be reused elsewhere, it belongs in Rust.

---

## Thin Tauri Commands

Tauri commands should act as bridges.

Bad

```
Command

↓

500 lines of logic
```

Good

```
Command

↓

Service

↓

Repository

↓

Storage
```

Commands should be small and easy to understand.

---

## Feature-Oriented Architecture

Organize code by feature rather than technical layer whenever practical.

Example:

```
timer/

planning/

journal/

notifications/

search/
```

Avoid large generic folders filled with unrelated code.

---

# State Management

## Centralized Application State

Application state should be centralized.

Avoid independent copies of the same information.

Changes should propagate naturally through the application.

---

## Derived State

Store only fundamental data.

Everything else should be computed.

Bad

```
completed_tasks

remaining_tasks

completion_percentage
```

Good

```
tasks

↓

Compute everything else
```

Derived state should never become stale.

---

## Immutable Thinking

Prefer replacing state over mutating it.

Small immutable updates are easier to reason about than widespread mutation.

---

# Data Storage

## Local First

Everything should work without an internet connection.

Network access should never be required for normal operation.

---

## Human Readable

Whenever practical:

- Markdown
- JSON
- TOML

should be preferred over opaque binary formats.

Users should always be able to inspect their own data.

---

## Stable File Structure

Avoid changing file formats frequently.

Backward compatibility is preferred.

Migration should always be possible.

---

# Error Handling

## Never Panic During Normal Operation

Unexpected user input should never crash the application.

Errors should be handled gracefully.

---

## Recover Instead of Failing

Whenever possible:

```
Recover

↓

Warn

↓

Continue
```

instead of

```
Crash

↓

Lose Data
```

---

## User-Friendly Errors

Internal errors may be technical.

User-facing errors should explain:

- what happened
- why it happened (if known)
- what the user can do next

---

# Performance

## Startup Must Feel Instant

Expensive work should happen after the UI becomes usable.

Prefer:

```
Open UI

↓

Load essentials

↓

Background initialization
```

instead of blocking startup.

---

## Lazy Loading

Load information only when needed.

Do not eagerly load years of journals, history, or search indexes during startup.

---

## Efficient Rendering

Only update UI components whose data actually changed.

Avoid unnecessary redraws.

---

## Efficient Search

Search should remain responsive even with many years of data.

Indexes should update incrementally.

---

# Asynchronous Operations

Long-running work should not block the UI.

Examples:

- search indexing
- backups
- journal generation
- imports
- exports
- calendar synchronization
- recovery validation

The application should remain responsive during background work.

---

# Separation of Responsibilities

A component should have one clear responsibility.

Example:

```
Timer Engine

↓

Only manages timing.
```

Not:

```
Timer

Planning

Notifications

Overlay

Statistics
```

Small focused modules are easier to maintain.

---

# Service Layer

Complex features should expose a service.

Example:

```
JournalService

TimerService

PlanningService

SearchService

NotificationService

HistoryService
```

Services coordinate behavior.

Repositories manage storage.

The UI presents results.

---

# Repository Layer

Repositories should be responsible only for persistence.

Example:

```
TaskRepository

JournalRepository

SettingsRepository
```

Repositories should not contain business logic.

---

# Event-Driven Communication

Where practical, major application events should be published rather than tightly coupled.

Examples:

```
Task Completed

↓

Journal updates

↓

Statistics update

↓

History updates

↓

Overlay refresh
```

This reduces dependencies between features.

---

# Configuration

Configuration should influence behavior, not implementation.

Avoid scattering configuration checks throughout the codebase.

Instead:

```
Configuration

↓

Service

↓

Behavior
```

---

# Testing

Core business logic should be independently testable.

Priority:

1. Timer engine
2. Planner
3. Journal generation
4. Search
5. Recovery
6. Statistics

UI testing is valuable but should not replace testing business logic.

---

# Logging

Logs are for developers, not users.

Log:

- unexpected errors
- recovery events
- background tasks
- synchronization

Do not log every user interaction.

Logs should help diagnose problems without becoming noise.

---

# Accessibility

Accessibility should be considered part of the implementation, not an afterthought.

Keyboard navigation should work everywhere.

Every action should be possible without using a mouse.

---

# Security

Leadership OS stores personal knowledge.

Implementation should prioritize:

- local storage
- least privilege
- safe file handling
- secure defaults

No data should leave the device without explicit user action.

---

# Extensibility

Design features so future additions require extending existing systems rather than replacing them.

Examples:

- new notification providers
- additional calendar integrations
- AI assistance
- synchronization
- plugins

The architecture should make future features straightforward to integrate.

---

# Simplicity

Prefer the simpler implementation when both solutions satisfy the requirements.

Avoid premature optimization.

Avoid unnecessary abstractions.

Avoid clever code.

Readable code is usually better than shorter code.

---

# Consistency

Similar problems should have similar solutions.

If one feature uses a particular architectural pattern, other features should generally follow the same pattern.

Consistency is more valuable than finding the perfect solution for each individual case.

---

# AI Implementation Guidelines

AI assistants contributing to Leadership OS should follow these principles:

- Read the relevant documentation before implementing a feature.
- Prefer extending existing systems over creating new ones.
- Do not invent behavior that contradicts the documented specifications.
- Avoid duplicate implementations of existing functionality.
- Keep functions small and focused.
- Write self-explanatory code.
- Preserve backward compatibility whenever practical.
- Favor maintainability over short-term convenience.
- If implementation details are ambiguous, choose the solution that best aligns with the project's core philosophy: **local-first, offline-first, keyboard-first, privacy-first, and performance-first.**

---

# Final Principle

When making implementation decisions, always optimize for the developer who will read this code one year from now.

Code is written once but maintained many times.

Leadership OS should be a codebase that is easy to understand, easy to extend, and difficult to break.