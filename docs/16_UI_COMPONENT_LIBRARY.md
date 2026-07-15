# Document 16 — UI Component Library

## Purpose

This document defines the reusable user interface components that make up Leadership OS.

The goal is consistency.

Every screen should feel like it belongs to the same application because it is composed from the same small set of building blocks.

If a new screen requires inventing new components, it should first be considered whether an existing component can be reused or extended.

---

# Design Philosophy

The interface should feel:

- Calm
- Minimal
- Functional
- Dense without feeling crowded
- Keyboard-first
- Information-first

Components should prioritize clarity over decoration.

Leadership OS is a productivity tool, not a marketing website.

---

# Design Principles

Every component should be:

- Accessible
- Keyboard navigable
- Theme aware
- Responsive
- Reusable
- Stateless whenever practical

Business logic should never exist inside UI components.

---

# Color Philosophy

Color communicates meaning, not decoration.

Suggested semantic colors:

| Meaning | Purpose |
|---------|----------|
| Primary | Primary actions |
| Success | Completed work |
| Warning | Deadlines approaching |
| Error | Problems requiring attention |
| Neutral | General interface |

Avoid assigning meaning purely through color.

Icons and text should reinforce every visual cue.

---

# Typography

Use typography to create hierarchy.

Levels:

```
Application Title

↓

Page Title

↓

Section Title

↓

Card Title

↓

Body Text

↓

Secondary Text

↓

Metadata
```

Avoid excessive font sizes.

Most information should fit comfortably without scrolling.

---

# Spacing

Spacing should follow a consistent scale.

Example:

```
4px

8px

12px

16px

24px

32px
```

Avoid arbitrary spacing values.

---

# Buttons

## Primary Button

Purpose:

The primary action on a screen.

Examples:

- Start Focus
- Save
- Complete Review

There should rarely be more than one primary button per view.

---

## Secondary Button

Used for supporting actions.

Examples:

- Cancel
- Edit
- Skip
- Export

---

## Icon Button

Used where the action is obvious.

Examples:

- Search
- Settings
- Delete
- Refresh
- Close

Every icon-only button must include an accessible label.

---

# Text Input

Used for:

- Task titles
- Notes
- Search
- Journal
- Configuration

Requirements:

- Keyboard focus indicator
- Placeholder text
- Validation messages
- Clear disabled state

---

# Search Box

Specialized text input.

Features:

- Instant search
- Clear button
- Keyboard shortcuts
- Optional search suggestions

Used by:

- Global Search
- Command Palette
- History
- Projects

---

# Dropdown

Used for selecting from predefined values.

Examples:

- Priority
- Project
- Theme
- Timer Duration

Avoid dropdowns when fewer than four options exist.

---

# Checkbox

Used for independent boolean options.

Examples:

- Enable Overlay
- Launch at Startup
- Auto Start Timer

---

# Toggle Switch

Reserved for frequently changed settings.

Examples:

- Focus Mode
- Click Through Overlay
- Notifications

---

# Card

The card is the primary content container.

Cards may represent:

- Task
- Project
- Daily Summary
- Statistics
- Journal
- Deadline

Cards should be visually lightweight.

---

# Task Card

Displays:

- Title
- Priority
- Project
- Deadline
- Estimated Time
- Status

Actions should appear only when needed.

---

# Project Card

Displays:

- Project Name
- Active Tasks
- Progress
- Last Updated

Projects should emphasize ongoing work rather than statistics.

---

# Statistic Card

Displays one key metric.

Examples:

```
Focused Time

5h 20m
```

```
Completed Tasks

8
```

These cards should be easy to scan.

---

# Progress Bar

Used when showing completion.

Examples:

- Daily progress
- Project completion
- Import progress

Avoid using progress bars for timers.

---

# Progress Ring

Reserved for time-based information.

Examples:

- Focus Timer
- Break Timer

This component visually communicates remaining time at a glance.

---

# Timer Display

The timer is one of the application's most important components.

Displays:

- Remaining time
- Elapsed time
- Session type
- Running state

It should be immediately recognizable throughout the application.

---

# Sidebar

The sidebar provides primary navigation.

Typical sections:

```
Today

Planner

Projects

History

Journal

Search

Settings
```

The sidebar should remain compact and predictable.

---

# Top Bar

Displays:

- Current page
- Search
- Quick actions
- Command Palette shortcut

Avoid cluttering the top bar.

---

# Modal

Reserved for decisions requiring immediate attention.

Examples:

- Delete confirmation
- Recovery
- Export options

Avoid using modals for routine workflows.

---

# Dialog

Used for structured interaction.

Examples:

- Create Project
- Edit Task
- Configure Timer

Dialogs may contain forms.

---

# Notification Toast

Temporary informational messages.

Examples:

```
Task Completed
```

```
Backup Finished
```

They should disappear automatically unless user action is required.

---

# Empty State

Every empty screen should explain:

- Why it is empty.
- What the user can do next.

Example:

```
No Tasks Today

Create your first task or generate today's plan.
```

---

# Loading State

Loading indicators should communicate progress without blocking interaction unnecessarily.

Prefer:

- Skeleton placeholders
- Progress indicators

Avoid indefinite spinners whenever possible.

---

# Error State

Every error component should explain:

- What happened
- What can be done
- Optional recovery action

Never display raw technical errors to the user.

---

# Timeline Component

Used by:

- History
- Journal preview
- Daily summary

The timeline should emphasize meaningful events rather than every recorded action.

---

# Calendar Component

Used for:

- Deadline selection
- Date navigation
- Planning

Leadership OS is not a calendar application.

The calendar should remain lightweight.

---

# Markdown Viewer

Used for:

- Journals
- Documentation
- Notes

Requirements:

- Syntax highlighting
- Tables
- Checklists
- Code blocks
- Internal links (future)

---

# Overlay Widget

The floating overlay is a specialized component.

Displays:

- Current task
- Timer
- Progress
- Next task

It should remain readable even in its smallest size.

---

# Command Palette

A dedicated reusable component.

Consists of:

- Search input
- Command list
- Keyboard navigation
- Command descriptions

It should be usable throughout the application.

---

# Data Table

Reserved for information where tabular presentation improves readability.

Examples:

- Search results
- Statistics
- Configuration lists

Avoid using tables for everyday task management.

---

# Keyboard Focus

Every interactive component must provide a visible focus indicator.

Users should always know:

- What is focused.
- What Enter will activate.
- How to move to the next element.

Keyboard usability is a core design requirement.

---

# Responsive Behavior

Components should adapt gracefully.

Examples:

Desktop

```
Sidebar

Main Content

Inspector
```

Small Window

```
Sidebar collapses

Main Content expands
```

Compact Overlay

```
Only timer and task
```

The interface should degrade gracefully rather than simply shrinking.

---

# Animation Principles

Animations should communicate state changes.

Examples:

- Expand
- Collapse
- Fade
- Progress

Avoid decorative animations.

Respect reduced-motion accessibility settings.

---

# Component Composition

Complex screens should be composed from existing components.

Example:

```
Daily Planner

├── Sidebar
├── Top Bar
├── Task Cards
├── Statistic Cards
├── Progress Ring
└── Action Buttons
```

New screens should rarely require entirely new UI elements.

---

# Future Components

Potential additions include:

- Kanban Board
- Gantt Timeline
- Calendar Agenda
- AI Assistant Panel
- Plugin Panel
- Activity Heatmap
- Habit Tracker
- Dashboard Widgets
- Rich Markdown Editor
- Multi-Workspace Switcher

These components should only be introduced when a genuine need arises.

---

# Final Principle

The UI should disappear behind the user's work.

Users should spend their time thinking about **their tasks**, not about **the interface**.

Every component should reduce friction, promote consistency, and support sustained focus throughout the working day.