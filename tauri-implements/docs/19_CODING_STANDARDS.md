# Document 19 — Coding Standards

## Purpose

This document defines the coding standards for Leadership OS.

The objective is to produce a codebase that is easy to read, easy to maintain, and consistent regardless of whether code is written by humans or AI assistants.

Code is read far more often than it is written.

Every implementation should optimize for readability and maintainability over cleverness.

---

# Core Principles

Every piece of code should strive to be:

- Readable
- Predictable
- Testable
- Modular
- Reusable
- Explicit
- Consistent

The simplest correct implementation is usually the best implementation.

---

# General Rules

## Prioritize Clarity

Prefer:

```rust
fn calculate_remaining_time(...)
```

Over:

```rust
fn calc(...)
```

Names should describe intent rather than implementation.

---

## Small Functions

Functions should generally perform one task.

Good:

```text
load_configuration()

restore_workspace()

generate_daily_plan()
```

Bad:

```text
initialize_everything()
```

If a function requires extensive comments to explain what it does, it is probably doing too much.

---

## Avoid Deep Nesting

Prefer early returns.

Bad:

```text
if condition {
    if another_condition {
        if third_condition {
            ...
        }
    }
}
```

Good:

```text
if !condition {
    return;
}

if !another_condition {
    return;
}

...
```

Flat code is easier to understand.

---

## Eliminate Duplication

If similar logic appears in multiple places:

- Extract a function.
- Extract a service.
- Extract a shared component.

Copy-paste should rarely survive code review.

---

# Naming Conventions

Names should describe business concepts.

Examples:

```
TaskService

JournalService

HistoryRepository

DailyPlanner

NotificationManager

SearchIndex
```

Avoid vague names.

Bad:

```
Helper

Utils

Manager2

Thing

DataHandler
```

---

# Module Organization

Modules should be organized by feature.

Example:

```
timer/

journal/

history/

planner/

search/

notifications/
```

Avoid large generic folders such as:

```
utils/

common/

misc/

helpers/
```

These often become dumping grounds.

---

# File Size

Prefer:

- Small modules.
- Focused files.

As a general guideline:

- Files over ~500 lines should be reviewed for opportunities to split responsibilities.
- Extremely small files are acceptable if they improve clarity.

---

# Rust Standards

## Prefer Strong Types

Model the domain explicitly.

Prefer:

```rust
TaskId

ProjectId

Duration

Priority
```

Over:

```rust
String

u32

i64
```

Domain types improve correctness and readability.

---

## Avoid `unwrap()` and `expect()`

Production code should not assume success.

Prefer:

```rust
?

match

if let

Result
```

Reserve `unwrap()` and `expect()` for tests or situations where failure truly indicates a programming error.

---

## Use `Result` for Recoverable Errors

Functions that can fail should return:

```rust
Result<T, Error>
```

Avoid using panic-based control flow.

---

## Keep Enums Exhaustive

Prefer expressive enums over boolean flags.

Good:

```rust
SessionState

Running

Paused

Break

Completed
```

Bad:

```rust
is_running

is_break
```

Enums make invalid states harder to represent.

---

## Prefer Immutable Data

Variables should be immutable unless mutation is necessary.

Minimize mutable state.

---

## Avoid Global Mutable State

Shared mutable state increases complexity.

Prefer explicit ownership and dependency injection.

---

## Traits for Behavior

Use traits to define behavior rather than tightly coupling implementations.

Example:

```text
NotificationProvider

CalendarProvider

StorageBackend
```

This makes future integrations easier.

---

## Async

Use asynchronous operations for:

- File I/O
- Database operations
- Search indexing
- Imports
- Exports
- Calendar synchronization

Avoid blocking the UI thread.

---

## Documentation

Public APIs should include concise documentation explaining:

- Purpose
- Parameters
- Return values
- Possible errors

Documentation should explain *why*, not restate *what* the code already says.

---

# Frontend Standards

## Components

Components should have one responsibility.

Avoid large components responsible for:

- Fetching data.
- Managing state.
- Rendering.
- Business logic.

Split responsibilities when necessary.

---

## State

Avoid duplicated frontend state.

Prefer reading from centralized application state.

Derived values should be computed rather than stored.

---

## Business Logic

Business rules belong in Rust.

The frontend should primarily:

- Display data.
- Capture user input.
- Trigger commands.
- Render state.

---

## Styling

Avoid inline styles.

Use shared design tokens and reusable component styles.

Visual consistency should come from the component library rather than individual screens.

---

## Accessibility

Every interactive element should:

- Be keyboard accessible.
- Provide a visible focus state.
- Include accessible labels where appropriate.
- Support screen readers.

Accessibility is part of the definition of complete.

---

# Error Handling

Errors should never be silently ignored.

Handle errors by:

- Recovering.
- Returning them.
- Logging them.
- Displaying an appropriate message.

Ignoring an error should always be an intentional decision.

---

# Logging

Logs should be meaningful.

Good:

```
Search index rebuilt successfully.
```

Bad:

```
Function entered.
```

Avoid excessive logging.

Logs should explain meaningful events rather than every execution step.

---

# Comments

Code should explain itself whenever possible.

Use comments to explain:

- Why a decision was made.
- Non-obvious business rules.
- References to external behavior.

Avoid comments that merely repeat the code.

Bad:

```text
Increment counter.
```

Good:

```text
The timer intentionally ignores system sleep to preserve
actual focused work rather than wall-clock duration.
```

---

# Testing

New business logic should generally include corresponding tests.

Bug fixes should include regression tests whenever practical.

Tests should verify observable behavior rather than implementation details.

---

# Dependencies

Before adding a dependency, ask:

- Does the standard library already solve this?
- Can an existing dependency solve it?
- Is this dependency actively maintained?
- Is the functionality substantial enough to justify another dependency?

Prefer fewer, well-maintained dependencies.

---

# Performance

Optimize only after measuring.

Avoid premature optimization.

However:

- Avoid unnecessary allocations.
- Avoid duplicate work.
- Avoid blocking operations.
- Avoid loading unnecessary data.

Reasonable efficiency should be the default.

---

# Git Standards

Commits should be:

- Small.
- Focused.
- Descriptive.

Each commit should represent a single logical change.

Examples:

```
Implement timer persistence

Add journal search indexing

Refactor notification scheduling
```

Avoid combining unrelated changes into a single commit.

---

# AI Coding Guidelines

AI-generated code should:

- Follow the documented architecture.
- Reuse existing services and components.
- Avoid creating duplicate functionality.
- Preserve naming consistency.
- Produce readable code over compact code.
- Leave the codebase cleaner than it was found.

If documentation and existing code disagree, documentation should generally be considered the source of truth unless an intentional architectural change has been made.

---

# Code Review Checklist

Before considering work complete, verify:

- Naming is clear.
- Functions are appropriately sized.
- Business logic is correctly located.
- Error handling is complete.
- Tests are present where appropriate.
- Accessibility requirements are met.
- Documentation remains accurate.
- No unnecessary duplication has been introduced.
- Performance remains acceptable.
- The implementation aligns with the documented product behavior.

---

# Refactoring

Improve the code when touching it.

Examples:

- Better naming.
- Smaller functions.
- Reduced duplication.
- Improved readability.

Large architectural refactors should remain separate from feature development unless they are necessary for correctness.

---

# Final Principle

Every line of code should make the next developer's job easier.

Whether that developer is a teammate, an AI assistant, or your future self, the code should communicate its intent clearly, follow consistent patterns, and fit naturally within the overall architecture of Leadership OS.

Consistency is a feature. Readability is an investment. Maintainability is the long-term goal.