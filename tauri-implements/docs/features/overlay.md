# Feature Specification — Overlay

## Purpose

The Overlay provides persistent awareness of the current work without requiring the user to switch back to the main application.

It exists to answer one question at any moment:

> **"What should I be working on right now?"**

Rather than functioning as a notification, the overlay acts as a quiet heads-up display (HUD) for the current work session.

The overlay should remain informative without becoming distracting.

---

# Design Goals

The overlay should:

- Always remain lightweight.
- Never interrupt the user's work.
- Be readable at a glance.
- Require little or no interaction.
- Stay synchronized with the current application state.
- Consume minimal system resources.

The overlay is intended to reduce context switching, not increase it.

---

# When the Overlay Appears

The overlay should be available whenever the application is running.

Users may configure whether it:

- starts automatically,
- remains hidden,
- or is always visible.

Visibility behavior is configurable.

---

# Window Characteristics

The overlay should be:

- Always on top (optional setting).
- Click-through when locked (optional).
- Borderless.
- Small.
- Draggable.
- Resizable within reasonable limits.
- Independent from the main application window.

Closing the main application window should not necessarily close the overlay.

---

# Primary Information

The overlay should display only information that helps the current work session.

By default this includes:

- Current task
- Current project
- Current priority
- Focus timer
- Current session status
- Current mode (Focus / Break)
- Daily completion progress

Example:

```
────────────────────────────
Implement Timer Engine

Project: Leadership OS

Priority: High

⏱ 18:42 / 25:00

████████░░░░ 74%

Focus Session #3

Today's Progress
7 / 12 Tasks Complete

Next:
Write Notification Engine
────────────────────────────
```

---

# Task Information

The current task section should display:

- task title
- priority indicator
- project (if applicable)
- estimated duration
- elapsed duration
- remaining duration

Long titles should truncate gracefully.

---

# Timer Display

The timer is the visual centerpiece.

It should clearly communicate:

- elapsed time
- remaining time
- session type
- paused/running state

The timer should update every second.

---

# Session State

Possible states include:

- Idle
- Planning
- Focus Session
- Break
- Paused
- Review

The current state should always be visible.

Example:

```
Focus Session
```

or

```
Break (03:15 remaining)
```

---

# Progress Display

Daily progress should provide immediate awareness.

Possible metrics:

- tasks completed
- planned tasks
- completed focus sessions
- total focused time
- remaining planned work

Example:

```
Today's Progress

8 / 11 Tasks

3h 42m Focus

2 Sessions Remaining
```

---

# Next Task Preview

When the current task finishes, the overlay should already indicate what comes next.

Example:

```
Next

Refactor Timer Engine
```

This removes the need to reopen the application after every completed task.

---

# Compact Mode

Users may enable a compact overlay.

Example:

```
Implement Timer

18:22

74%
```

or

```
⏱ 12:18
Current:
Task Scheduling
```

Compact mode prioritizes minimal screen space.

---

# Expanded Mode

Expanded mode provides additional context.

Possible sections:

- task
- project
- timer
- progress
- today's statistics
- next task

---

# Overlay Sizes

Suggested presets:

Small

```
Task

12:41
```

Medium

```
Task

Project

Timer

Progress
```

Large

```
Task

Project

Priority

Timer

Statistics

Next Task

Daily Progress
```

Users may freely resize the window.

---

# Visual Indicators

The overlay should communicate state visually.

Examples:

Focus

```
● Focus
```

Paused

```
⏸ Paused
```

Break

```
☕ Break
```

Completed

```
✓ Complete
```

No flashing animations should be used.

---

# Interaction

The overlay should support lightweight interaction.

Possible actions:

- Pause timer
- Resume timer
- Complete task
- Skip task
- Start next task
- Open main window
- Hide overlay

No complex editing should occur inside the overlay.

---

# Right Click Menu

Example menu:

```
Open Leadership OS

Pause Timer

Resume Timer

Complete Task

Start Break

Hide Overlay

Settings

Exit
```

---

# Keyboard Shortcuts

The overlay should respond to global shortcuts.

Examples:

```
Start Focus

Pause

Resume

Complete Task

Show Overlay

Hide Overlay

Toggle Click Through
```

Exact shortcuts are defined in Configuration.

---

# Click-Through Mode

When enabled:

- mouse events pass through the overlay
- overlay remains visible
- keyboard shortcuts continue working

This prevents accidental interaction while coding or writing.

---

# Transparency

Users may configure overlay opacity.

Suggested range:

```
20%

40%

60%

80%

100%
```

Transparency should not reduce readability excessively.

---

# Position Memory

The overlay should remember:

- monitor
- position
- size
- opacity
- compact/expanded mode
- click-through state

These settings should persist across restarts.

---

# Multi-Monitor Support

The overlay should:

- remember the selected monitor
- reopen on the same monitor
- handle disconnected monitors gracefully

If the previous monitor is unavailable, the overlay should appear on the primary display.

---

# Auto Hide

Optional behaviors include:

- hide when idle
- hide during fullscreen applications
- hide during presentations
- fade after inactivity

Users control all automatic behavior.

---

# Performance Requirements

The overlay must be extremely lightweight.

It should:

- consume minimal CPU
- use very little memory
- avoid unnecessary redraws
- update only changing components
- remain responsive under heavy workload

The overlay should never noticeably impact system performance.

---

# Accessibility

Users should be able to configure:

- font size
- opacity
- color theme
- scaling
- compact mode
- keyboard-only interaction

The overlay should remain readable on both light and dark desktops.

---

# Failure Behavior

If synchronization with the main application fails:

- display the last known state
- indicate synchronization loss
- automatically reconnect when possible

The overlay should never crash independently.

---

# Future Enhancements

Potential future additions include:

- mini calendar
- current deadline countdown
- upcoming meetings
- weather
- music controls
- AI coaching suggestions
- live productivity metrics
- floating notes
- clipboard history
- multiple overlays
- per-monitor overlays
- project-specific overlays

These features are intentionally excluded from the initial implementation to preserve simplicity.