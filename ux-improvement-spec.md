# UX Improvement Specification — Leadership OS

> **Created:** 2026-07-08
> **Status:** Draft spec (no implementation yet)

---

## 1. Current Bugs & Root Causes

### 1.1 Timer fails to start on first click

**Observed:** Clicking "Start" on a pending task does nothing visible. If you restart the app, the timer is running.

**Root cause (Dashboard.tsx):**
- `handleStartTask` calls `api.startTaskTimer(task.id)` which updates the task status to "active" on the backend
- It sets `activeTaskId` via context, which causes `activeTask` to recompute from the stale `tasks` array
- But the `tasks` array in context still has the task's status as "pending"
- The timer effect checks `activeTask?.status === "active"` — which is false because `tasks` wasn't updated
- On app reload, `loadSession` fetches fresh tasks from the backend where status is "active" — so the timer works

**Fix:** After calling `startTaskTimer`, update the task's status in the local `tasks` array from "pending" to "active".

### 1.2 No desktop or in-app notifications fire

**Observed:** No notification popups appear when time estimates are exceeded. The in-app modal also doesn't show.

**Root cause (double):**
1. **Permissions (Tauri):** `src-tauri/capabilities/default.json` only includes `"core:default"` and `"opener:default"` — missing `"notification:default"` permission required by `@tauri-apps/plugin-notification`.
2. **Timer not actually running** (see 1.1) — so `elapsedSeconds` never reaches the estimated threshold, so the notification code never executes.

**Fix:** Add `"notification:default"` to capabilities + fix timer bug.

### 1.3 Current task can't be resumed on app restart

**Observed:** If the app is restarted while a task is active, `loadSession` finds the active task and sets `activeTaskId` but does NOT restore the elapsed time. The timer shows `00:00` and starts from zero, losing the already-accumulated time.

**Fix:** On load, query the active time entry from the backend, calculate elapsed seconds from `start_time`, and set that as the initial `elapsedSeconds`.

---

## 2. Workflow Improvements

### 2.1 Hybrid flow: guided morning, freeform rest-of-day

| Phase | Behavior |
|-------|----------|
| **Morning setup** | Guided: Welcome → Planning → Commitment → Start Day (existing flow, keep as-is) |
| **During the day** | Dashboard is the home. User can freely: navigate to settings, view stats, add tasks |
| **End of day** | "End day" button from any screen via persistent header bar |

### 2.2 Freely navigate while timer runs

- Timer continues counting in the background regardless of which page you're on
- A **persistent mini-timer** shows in a top bar / header area visible on all pages (not just Dashboard)
- The mini-timer shows: current task name, elapsed time, estimated time, Pause/Complete buttons

### 2.3 Add tasks mid-day from anywhere

- **Persistent quick-add** available from the auto-hide sidebar
- Clicking the **sidebar task icon** (or a dedicated "+" button) opens a quick-add popover/modal:
  - Task title (text input)
  - Priority (3-option select)
  - Estimated duration (number input)
- On submit, the task is created in the current session and appears in the Dashboard's pending list
- User can also return to the **Planning view** via sidebar to bulk-edit, reorder, or delete tasks mid-day

### 2.4 Auto-hide sidebar

- Sidebar starts collapsed (thin icon strip, ~48px wide)
- Expands on hover or click to show labels: Home, Tasks, Settings
- Contains: nav links + quick-add button + mini-timer (when a task is active)
- Follows Design.md philosophy: "Navigation should disappear. Users should think about content, not navigation."

---

## 3. Design Guidelines

### 3.1 Design Philosophy

Follow `~/Documents/project/Design.md` strictly. Key tenets:
- **Spacious, not cramped** — generous whitespace, no packed layouts
- **Intentional** — every pixel has a purpose
- **Calm and premium** — quiet, confident, not flashy
- **Consistent spacing** — 8px system already in `index.css`, must be used everywhere
- **Hierarchy** — obvious visual rhythm: large → medium → small sections
- **Typography-driven** — typography is the primary design language

### 3.2 Current violations to fix

| Issue | Details |
|-------|---------|
| Inconsistent margins | Some pages use `px-8`, others use varying padding. Ensure all pages use consistent horizontal padding via a shared layout container |
| Cramped feeling | Reduce content density: increase vertical spacing between sections, reduce number of elements shown at once |
| Card overload | Current Dashboard uses cards for everything. Replace some card groups with clean list sections (per Design.md: "Cards should not become the entire layout") |
| Footer crowding | The bottom action bars feel cramped. Give them more breathing room (`py-6` or `py-8` instead of `py-5`) |
| Empty states | Replace "No tasks for today" with more encouraging, guiding empty states that teach the user what to do next |
| Missing transitions | Add subtle fade/slide transitions when switching between views and when showing/hiding the notification modal |

### 3.3 Micro-interactions to add

- **Button press:** Slight transform scale(0.97) on mousedown, release on mouseup
- **Checkbox animation:** Smooth checkmark draw animation when marking tasks complete
- **Progress bar:** Animate width changes with ease-out
- **Timer digit change:** Subtle opacity shift on second changes
- **Sidebar expand:** Smooth width transition (150ms ease)
- **Notification modal:** Fade in + slight scale up from center, backdrop blur
- **Task start:** Brief highlight pulse on the started task card
- **Navigation transitions:** Page content fades in (100ms)

---

## 4. Timer & Time Management

### 4.1 Core timer behavior

- One task active at a time
- Starting a new task auto-pauses the current one (already implemented, but broken)
- Timer counts up from 0 when a task starts
- When paused, elapsed time is preserved — does NOT reset to 0
- When resumed, timer continues from where it left off
- Completed tasks show total actual_duration in the completed list

### 4.2 Time-up notification (fix)

- When `elapsedSeconds >= estimatedSeconds`, trigger:
  1. In-app modal overlay (already exists, but doesn't show due to timer bug)
  2. Desktop push notification (needs notification permission fix)
  3. Repeat reminder every N minutes (user-configurable in settings, already implemented)
- Modal actions:
  - **Finish** — marks task complete
  - **+15 minutes** — adds 15 min to estimate, resets elapsed
  - **+30 minutes** — adds 30 min to estimate, resets elapsed
  - **Still working** — dismisses modal, resets elapsed, continues timing
  - **Switch task** — marks task skipped, opens task selection (navigate to pending tasks)

### 4.3 Persistent mini-timer (new)

When a task is active and you're on a non-Dashboard page:

```
┌─────────────────────────────────────────────────────┐
│  ● Working on: [task name]    12:34 / 45m    ⏸  ✓  │
└─────────────────────────────────────────────────────┘
```

- Shown as a slim bar at the top of the content area (below the app header)
- Visible on: Planning, Settings, any future screens
- Not shown on: Welcome (no active session), Loading, Reflection (day is ending)
- Contains: task name (truncated), elapsed timer, estimated time, Pause & Complete buttons

---

## 5. Task Management Improvements

### 5.1 Sidebar quick-add popover

```
When sidebar icon is clicked:
┌────────────────────────┐
│  Add Task              │
│                        │
│  [Task title _________]│
│                        │
│  [Priority ▼] [30m ▼] │
│                        │
│  [Cancel]  [Add Task]  │
└────────────────────────┘
```

- Non-blocking popover (closes on click outside or on submit)
- Pre-fills estimate from settings' `default_task_duration_minutes`
- On submit: creates task via API, updates local tasks array, shows brief toast confirmation

### 5.2 Return to Planning view

- Add "Plan" or "Tasks" button to the sidebar
- Opens the full Planning view with all existing tasks
- User can add, edit, delete, reorder tasks
- "Review plan" button on Planning page becomes "Return to Dashboard" when session is active
- "Return to Dashboard" does NOT change session status — just navigates back

### 5.3 Dashboard task list improvements

- Pending tasks show as a clean list (not cards) — per Design.md
- Active task shows as a prominent, elevated section at the top
- Completed tasks are collapsed by default with a show/hide toggle
- Drag-to-reorder is aspirational; reorder buttons (up/down) remain for now

---

## 6. Notification Fix Plan

### 6.1 Tauri permissions

**File:** `src-tauri/capabilities/default.json`

Add `"notification:default"` to the permissions array so the system notification API is available at runtime.

### 6.2 Desktop notification calls

Move the notification logic (which is duplicated in both `handleStartTask` and the notification alarm) into a single shared helper. Add a user-facing toggle in Settings to enable/disable desktop notifications.

### 6.3 In-app fallback

- When desktop notification can't fire (permission denied, unsupported platform), the in-app modal is the primary alert mechanism
- Add a subtle toast/banner system for non-critical notifications (task started, task completed)

---

## 7. Settings Page Additions

| Setting | Current | Add |
|---------|---------|-----|
| Desktop notifications | Not present | Toggle: Enable/disable desktop notifications (default: on) |
| Quick-add defaults | Not present | Default priority and duration for quick-add |

---

## 8. Keyboard Shortcuts (Balanced Approach)

Basic shortcuts for power users, not required for navigation:

| Shortcut | Action |
|----------|--------|
| `N` | Quick-add task (from Dashboard) |
| `Space` | Pause/Resume current task |
| `Enter` | Complete current task |
| `Esc` | Close modal / popover |
| `1` / `2` / `3` | Set priority (U&I / Important / Urgent) when adding task |

---

## 9. Implementation Priority

### P0 — Critical (must fix)
1. Fix timer start bug (update tasks array after API call)
2. Fix notification permissions in Tauri capabilities
3. Fix timer restore on app restart
4. Unblock navigation — timer runs on all pages

### P1 — High (core experience)
5. Persistent mini-timer bar
6. Quick-add task from sidebar
7. Return to Planning view mid-day
8. Auto-hide sidebar

### P2 — Medium (polish)
9. Fix all margin/spacing inconsistencies per Design.md
10. Add micro-interactions and transitions
11. Improved empty states
12. Add keyboard shortcuts

### P3 — Nice to have
13. Drag-to-reorder tasks
14. Toast notification system
15. Desktop notifications toggle in Settings

---

*This spec was created through interviews with the project owner. No code changes have been made yet.*
