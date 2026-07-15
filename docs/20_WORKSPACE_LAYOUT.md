# Document 20 — Workspace Layout

## Purpose

This document defines the physical layout of Leadership OS.

Unlike the feature documents, this document is concerned with **where information lives**, **how it changes throughout the day**, and **how the workspace should feel**.

The goal is that a user never feels like they are navigating between applications.

Instead, the application continuously reshapes itself around the user's current work.

---

# Core Philosophy

Leadership OS is **one workspace**.

Not a collection of pages.

The user should mentally feel like they are sitting at a desk.

Throughout the day:

- different tools become more important,
- different information becomes visible,
- different actions become available,

but the desk itself never changes.

---

# The Workspace

The application consists of four permanent regions.

```
┌────────────────────────────────────────────────────────────────────┐
│ Top Bar                                                           │
├──────────────┬──────────────────────────────┬──────────────────────┤
│              │                              │                      │
│              │                              │                      │
│ Sidebar      │      Main Workspace          │   Execution Panel    │
│              │                              │                      │
│              │                              │                      │
├──────────────┴──────────────────────────────┴──────────────────────┤
│ Status Bar                                                        │
└────────────────────────────────────────────────────────────────────┘
```

The user should recognize this layout immediately.

Nothing should unexpectedly move.

---

# Region 1 — Sidebar

Purpose:

Navigation between major contexts.

Not between features.

The sidebar should remain extremely small.

Items:

- Today
- History
- Settings

Nothing more.

The sidebar should never become a feature list.

---

Bottom section:

Display only lightweight information.

Example:

```
Working

4 / 8 Complete

Focus

2h 34m
```

No graphs.

No notifications.

No cards.

---

# Region 2 — Main Workspace

This is the largest region.

It changes depending on the current application state.

The workspace never disappears.

Instead, sections expand or collapse.

---

## Planning

Expanded

- Carry Forward
- New Task
- Today's Tasks

Collapsed

- Execution Information

---

## Working

Expanded

- Current Task

- Today's Tasks

Collapsed

- Task Creation

The user should still see today's plan.

Nothing disappears.

---

## Break

The workspace remains visible.

Only the execution controls change.

The task list remains available.

The application should never feel paused.

Only the work session is paused.

---

## Review

Review is the only state that is allowed to occupy almost the entire workspace.

Reflection deserves uninterrupted attention.

---

# Region 3 — Execution Panel

This is the heart of Leadership OS.

Everything else supports this panel.

The panel is always visible.

It should never disappear.

Width:

Approximately 300–360 px.

Contents:

---

Current Task

```
Implement Overlay

High Priority
```

---

Focus Timer

```
00:42:18
```

Large.

Easy to read.

---

Session Information

Started

Elapsed

Estimated

---

Today's Progress

```
██████░░░░

4 / 8 Tasks
```

---

Next Task

```
Notifications
```

---

Actions

Pause

Complete

Start Break

---

During a break

Replace

Pause

Complete

with

Resume

End Break

---

When idle

Replace the timer with

```
No active task

Start one from Today's Plan.
```

---

This panel should feel like the operating system's command center.

---

# Region 4 — Status Bar

Very small.

Shows only:

- Focus Time
- Completed Tasks
- Keyboard Hint
- Background Activity

Nothing else.

---

# Workspace States

The workspace changes smoothly.

Never abruptly.

---

Planning

Task creation expanded.

Execution panel idle.

---

Working

Task creation collapses.

Execution panel expands.

Current task highlighted.

---

Break

Execution panel changes.

Main workspace barely changes.

---

Review

Main workspace expands.

Execution panel minimizes.

---

History

History replaces only the Main Workspace.

Sidebar remains.

Execution Panel remains visible.

This allows the user to browse history while still seeing today's execution state.

---

Settings

Settings replace only the Main Workspace.

Execution panel remains visible.

A running timer should never disappear because the user opened Settings.

---

# Persistence Rules

Always visible:

Sidebar

Execution Panel

Top Bar

Status Bar

---

Temporary

Search

Command Palette

Recovery

Confirmation Dialogs

Task Editor

Morning Greeting

End-of-Day Review

These appear above the workspace.

Never replace it.

---

# Visual Hierarchy

The eye should naturally follow:

Current Task

↓

Timer

↓

Today's Plan

↓

Everything Else

Never place decorative elements above execution information.

---

# Animation Principles

Animations should communicate state.

Never decoration.

Examples:

Planning → Working

Task creation gently collapses.

Execution panel expands.

Timer fades in.

---

Working → Break

Timer changes color.

Buttons change.

Everything else remains fixed.

---

Break → Working

Reverse animation.

---

Review

Workspace gently fades.

Reflection slides upward.

No dramatic transitions.

---

# Resizing

Sidebar

Never resizes.

Execution Panel

Can resize within limits.

Minimum

280 px

Maximum

420 px

Main Workspace receives remaining width.

---

# Responsive Behaviour

Very small windows

Execution Panel collapses into a bottom drawer.

Sidebar becomes icon-only.

No information should be lost.

Only repositioned.

---

# Keyboard Focus

Default focus

Current workspace.

Not sidebar.

Tab order

Workspace

↓

Execution Panel

↓

Sidebar

↓

Status Bar

Search

Command Palette

Dialogs

must trap focus correctly.

---

# Design Principles

The interface should feel:

Calm.

Intentional.

Predictable.

Minimal.

Professional.

Everything should support execution.

Nothing should compete with the current task.

---

# One Sentence Rule

When the user looks at Leadership OS, their eyes should immediately know:

**What am I working on?**

**How long have I been working?**

**What should I do next?**

The interface exists to answer those three questions with as little thinking as possible.
