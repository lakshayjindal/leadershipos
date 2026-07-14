# ARCHITECTURE V2 — Leadership OS Final Architectural Reconciliation

**Date:** July 9, 2026
**Source documents:** All docs/ and docs/features/, especially 20_WORKSPACE_LAYOUT.md

---

## 1. Overall Architectural Philosophy

Leadership OS is **one workspace** — not a collection of pages, not a multi-screen application.

The interface is **state-driven**, not navigation-driven. The application has exactly one layout with four permanent regions. The regions that are always visible (Sidebar, Execution Panel, Top Bar, Status Bar) never disappear. Only the Main Workspace changes, and it changes smoothly based on the user's current state.

The closest analogy is **VS Code**: one window, persistent sidebars, a main editing area that changes based on context, and a status bar that provides at-a-glance information. The user never feels like they are "navigating" to a different application.

---

## 2. The Four Permanent Regions

```
┌────────────────────────────────────────────────────────────────────────────┐
│ TOP BAR                                                                    │
├──────────────┬───────────────────────────────────┬─────────────────────────┤
│              │                                   │                         │
│              │                                   │                         │
│  SIDEBAR     │        MAIN WORKSPACE             │    EXECUTION PANEL      │
│  (180px)     │        (flexible width)            │    (300-360px)          │
│              │                                   │                         │
│              │                                   │                         │
│              │                                   │                         │
├──────────────┴───────────────────────────────────┴─────────────────────────┤
│ STATUS BAR                                                                 │
└────────────────────────────────────────────────────────────────────────────┘
```

### Region 1 — Top Bar (persistent, ~48px)

**Left:** State indicator (colored dot + label: Planning / Working / Break / Review / Idle)
**Center:** Current task name (if active) — shows even when working in History or Settings
**Right:** Quick action icons (search, command palette, settings)

Never shows: page titles, breadcrumbs, navigation links.

### Region 2 — Sidebar (persistent, ~180px)

Three items only:
- **Today** — returns to the current day's workspace in the correct state
- **History** — replaces only the Main Workspace; Execution Panel remains visible
- **Settings** — replaces only the Main Workspace; Execution Panel remains visible

Bottom section (lightweight info):
```
Working
4 / 8 Complete
Focus: 2h 34m
```

No graphs, no cards, no notifications, no badges.

### Region 3 — Main Workspace (state-driven, flexible width)

This is the largest region. It changes depending on the current application state. It never disappears — sections expand or collapse smoothly.

**Planning state:**
- Expanded: Carry Forward, New Task, Today's Tasks
- Collapsed: Execution info (handled by Execution Panel)

**Working state:**
- Expanded: Current Task info, Today's Tasks (task queue)
- Collapsed: Task Creation

**Break state:**
- Main workspace barely changes — only task list remains
- Only the execution controls change (in the Execution Panel)

**Review state:**
- Expands to occupy almost the entire workspace (reflection deserves immersion)
- Execution Panel minimizes

**History:**
- History view replaces the Main Workspace
- Execution Panel remains visible (user can see today's execution while browsing past)

**Settings:**
- Settings view replaces the Main Workspace
- Execution Panel remains visible (running timer never disappears)

### Region 4 — Execution Panel (persistent, 300-360px)

This is the **heart of Leadership OS**. Everything else supports this panel. It is always visible and never disappears.

**Contents (top to bottom):**

1. **Current Task**
   ```
   Implement Overlay
   High Priority
   ```

2. **Focus Timer** (large, easy to read)
   ```
   00:42:18
   ```

3. **Session Information**
   - Started: 09:15
   - Elapsed: 42:18
   - Estimated: 60 min

4. **Today's Progress**
   ```
   ██████░░░░  74%
   4 / 8 Tasks
   ```

5. **Next Task**
   ```
   Notifications
   ```

6. **Actions**
   - Working state: [Pause] [Complete] [Start Break]
   - Break state: [Resume] [End Break]
   - Idle state: [Start Task] or "No active task. Start one from Today's Plan."

**Behavior by state:**

| State | Execution Panel Shows |
|-------|----------------------|
| Planning | Idle state: "No active task. Start one from Today's Plan." |
| Working | Timer running + task info + Pause/Complete/Start Break |
| Break | Break timer + Resume/End Break (different from working controls) |
| Review | Minimized (workspace takes priority) |
| History | Remains visible (shows today's state regardless of History view) |
| Settings | Remains visible (timer keeps running) |
| Idle | "No active task" message |

### Region — Status Bar (persistent, very thin)

Shows only:
- Total Focus Time today
- Completed Tasks count
- Keyboard hint: `Cmd+K`
- Background activity indicator (subtle)

---

## 3. Overlay Components

These appear **above** the workspace. They never replace it.

| Component | Trigger | Behavior |
|-----------|---------|----------|
| **Search** | `Cmd+Shift+F` or icon | Full overlay, cursor focused, Esc dismisses |
| **Command Palette** | `Cmd+K` | Centered modal, keyboard navigable, Esc dismisses |
| **Task Edit** | Double-click task | Modal, Cmd+Enter saves, Esc cancels |
| **Delete Confirm** | Delete action | Danger modal with task name |
| **Recovery** | Unexpected startup | Modal explaining recovered state |
| **Morning Greeting** | First launch of day | Auto-dismiss overlay (3s) |
| **Review** | End of day trigger | Takes over Main Workspace (not an overlay) |

---

## 4. Application States & Transitions

```
STARTUP
  │
  ├─ (recovery needed) → Recovery Overlay
  │
  └─ Morning Greeting (3s)
       │
       ▼
    PLANNING ──── (Begin Work) ────▶ WORKING
       ▲                               │
       │                      ┌────────┼────────┐
       │                      │        │        │
       │                      ▼        ▼        ▼
       │                   COMPLETE  PAUSE    START BREAK
       │                      │        │        │
       │                      ▼        ▼        ▼
       │                   WORKING   IDLE     BREAK
       │                      (next     │        │
       │                      task)    │        │
       │                      │        │        │
       │                      │        ▼        │
       │                      │     REVIEW      │
       │                      │        │        │
       │                      │        ▼        │
       │                      │   SHUTDOWN      │
       │                      │                 │
       └──────────────────────┴─── (Resume) ────┘
```

### State Details

**Planning** — Workspace shows planning layout. Execution Panel shows idle state.
**Working** — Timer runs in Execution Panel. Workspace shows task queue.
**Break** — Break timer in Execution Panel. Workspace remains mostly unchanged.
**Idle** — Workspace shows calm waiting state. Execution Panel shows "No active task."
**Review** — Review takes over Main Workspace. Execution Panel minimizes.
**Shutdown** — Confirmation overlay. Then app ready to close.

---

## 5. Architectural Decisions & Justifications

### Why the Execution Panel exists and what it contains

**Documentation basis:** 20_WORKSPACE_LAYOUT.md defines this as "the heart of Leadership OS" — always visible, never disappears, contains Current Task, Timer, Progress, Next Task, and Actions.

**Rationale:** The three questions the interface must answer ("What am I working on? How long have I been working? What should I do next?") are all answered by this panel. It must always be visible because the user should never have to navigate to find the timer or current task.

### Why History and Settings are the only dedicated views

**Documentation basis:** "History and Settings replace only the Main Workspace, never the entire application." The Execution Panel remains visible because a running timer should never disappear.

**Rationale:** History represents exploration of the past (a different cognitive mode). Settings is a meta-activity configured once. Both are accessed infrequently and intentionally separated from daily execution.

### Why the Sidebar has only 3 items

**Documentation basis:** "The Sidebar represents major contexts, not individual features." The docs explicitly list: Today, History, Settings.

**Rationale:** More items would encourage page-navigation thinking. Three items reinforce the concept of a single workspace with occasional context switches.

### Why the Review takes over the entire workspace

**Documentation basis:** "Review is the only state that is allowed to occupy almost the entire workspace. Reflection deserves uninterrupted attention."

**Rationale:** Reflection is the closing ritual of the workday. It should feel immersive, not like filling out a form in a corner.

### Why Search and Command Palette are overlays

**Documentation basis:** Overlays "appear above the workspace. Never replace it." Search docs: "Should open instantly. Cursor immediately focused."

**Rationale:** The user should never navigate to a search page. Search should be available from any state without losing context.

---

## 6. What This Means for the Current Implementation

### Architecture Conflicts (Must Fix)

| # | Current Implementation | V2 Architecture | Severity |
|---|----------------------|-----------------|----------|
| 1 | 9-page router with Routes | Single workspace, state-driven | **Critical** |
| 2 | Timer as a page (`/timer`) | Timer in persistent Execution Panel | **Critical** |
| 3 | Tasks as a page (`/tasks`) | Tasks in workspace (planning) + task queue (working) | **Critical** |
| 4 | Breaks as a page (`/breaks`) | Break state in Execution Panel | **Critical** |
| 5 | Review as a page (`/review`) | Review state in Main Workspace | **Critical** |
| 6 | Search as a page (`/search`) | Search overlay | **Critical** |
| 7 | Journal as a page (`/journal`) | File-based; preview in review overlay | **Critical** |
| 8 | Dashboard as default route (`/`) | No dashboard — startup transitions to planning | **Critical** |
| 9 | Sidebar has 9 items | Sidebar has 3 items (Today, History, Settings) | **High** |
| 10 | No Execution Panel component | New component needed | **High** |
| 11 | Top bar shows page title | Top bar shows state + current task | **High** |
| 12 | Layout: sidebar + main content | Layout: sidebar + main workspace + execution panel + top bar + status bar | **High** |
| 13 | No Status Bar | Status bar needed | **Medium** |
| 14 | Frontend owns timer logic | Timer in Rust (backend) | **Medium** |
| 15 | No History view | History view needed | **Medium** |
| 16 | Static command palette | Context-aware command palette | **Medium** |
| 17 | Missing keyboard shortcuts | Comprehensive keyboard support | **Medium** |
| 18 | Journal generates report-style | Journal generates narrative-style | **Low** |
| 19 | Missing overlay features (next task, progress, compact mode) | Enhanced overlay | **Low** |

### Features Preserved As-Is (No Change Needed)

- Local-first SQLite storage ✓
- Task state machine (Rust backend) ✓
- Carry forward workflow ✓
- Task creation with required title only ✓
- Priority levels (Critical, High, Medium, Low) ✓
- Optional deadline (date + time) ✓
- Optional estimated duration ✓
- Display order separate from priority ✓
- Work session recording ✓
- Break types (tea, lunch, dinner, personal, meeting) ✓
- FTS5 full-text search ✓
- Toast notification system ✓
- Command palette (needs context-awareness enhancement) ✓
- Dark/light theme ✓
- Delete confirmation ✓
- Keyboard navigation in search ✓
- Tauri overlay window ✓

---

## 7. Detailed Implementation Plan

### Phase 1: Layout Restructure (Single Workspace)

**Goal:** Replace the 9-page router with the 4-region single workspace layout.

**Steps:**

1. **Create `ExecutionPanel.tsx`** — Persistent right-side panel (300-360px)
   - Shows: Current Task, Timer, Session Info, Progress Bar, Next Task, Actions
   - State-driven: changes based on planning/working/break/idle states
   - During break: shows break timer instead of focus timer
   - During idle: shows "No active task" message
   - During review: minimizes/minifies
   - During history/settings: remains fully visible

2. **Rewrite `App.tsx` layout** — Remove `react-router-dom Routes` pattern
   - Replace with state machine: `currentState: AppState`
   - Layout: `<TopBar /> <div class="workspace"> <Sidebar /> <MainWorkspace /> <ExecutionPanel /> </div> <StatusBar />`
   - `MainWorkspace` renders the correct component based on state
   - No "navigation" — just state transitions

3. **Rewrite `Sidebar.tsx`** — 3 items only: Today, History, Settings
   - "Today" transitions workspace to planning or working state
   - "History" and "Settings" replace only Main Workspace
   - Bottom section: state label, task count, focus time

4. **Rewrite `TopBar.tsx`** — Remove page title, show state indicator + current task name + quick action icons

5. **Create `StatusBar.tsx`** — Thin bar at bottom: focus time, completed tasks, Cmd+K hint

6. **Update `index.css`** — Add CSS variables for execution-panel-width

7. **Remove route-based pages:**
   - `Dashboard.tsx` → functionality absorbed into startup transition + planning state
   - `Tasks.tsx` → task management in planning workspace + working workspace
   - `Timer.tsx` → functionality moved to ExecutionPanel
   - `Breaks.tsx` → functionality moved to ExecutionPanel (break state)
   - `Review.tsx` → becomes a workspace state component
   - `Journal.tsx` → removed; preview shown in review state
   - `SearchHistory.tsx` → becomes SearchOverlay component

**Files to create:** `ExecutionPanel.tsx`, `StatusBar.tsx`, `MainWorkspace.tsx`
**Files to rewrite:** `App.tsx`, `Sidebar.tsx`, `TopBar.tsx`, `App.css`
**Files to remove:** All page components (they become state components or overlays)

### Phase 2: State Components

**Goal:** Replace page components with state-driven workspace components.

1. **Create `PlanningWorkspace.tsx`** (replaces DailyPlanner.tsx)
   - Carry forward section (collapsible, auto-expanded if tasks exist)
   - Task creation form (title only, expandable for details)
   - Task list (reorderable, inline priority changes)
   - "Begin Work" transitions to working state
   - No wizard, no step indicators — continuous workspace

2. **Create `WorkingWorkspace.tsx`** (replaces Tasks.tsx + Timer.tsx functionality)
   - Current task highlighted
   - Task queue (pending tasks sorted by priority/order)
   - Completed tasks (collapsed section)
   - "Focus Now" on each pending task starts execution
   - Task creation form collapsed by default

3. **Create `BreakWorkspace.tsx`** (minimal — task list remains, controls in execution panel)
   - Shows the same task queue as Working state
   - Break indicator in workspace (subtle)

4. **Create `ReviewWorkspace.tsx`** (takes over Main Workspace)
   - Daily summary cards
   - 3 reflection text areas
   - Save + Generate Journal + End Day buttons

5. **Create `HistoryView.tsx`** — Chronological timeline
   - Reverse-chronological, grouped by day
   - Daily summaries with expandable events
   - Filter by type
   - Date navigation
   - Execution Panel remains visible

6. **Create `SettingsView.tsx`** — Move existing Settings into the new layout
   - Execution Panel remains visible

7. **Create `IdleWorkspace.tsx`** — Calm waiting state
   - "Good morning/afternoon" greeting
   - Suggested next action: "Start Planning" or "Resume Last Task"

### Phase 3: Overlay Components

**Goal:** Make Search, Command Palette, and dialogs true overlays.

1. **Convert `SearchHistory.tsx`** → `SearchOverlay.tsx`
   - Full-screen overlay with backdrop
   - Input auto-focused on open
   - Grouped results, keyboard navigation
   - Esc to dismiss, returns to previous workspace state
   - Trigger: `Cmd+Shift+F` or search icon in Top Bar

2. **Enhance `CommandPalette.tsx`** — Add context awareness
   - Commands change based on current state:
     - Planning: "Create Task", "Begin Work", "Open Settings"
     - Working: "Pause Timer", "Complete Task", "Start Break"
     - Break: "Resume Work", "End Break"
     - Idle: "Start Planning", "Create Task"
   - Show dynamic shortcuts

3. **Create `RecoveryOverlay.tsx`** — Recovery prompt on unexpected startup
   - Shows what was recovered
   - Resume/Discard options

4. **Create `MorningGreeting.tsx`** — Auto-dismiss overlay for first launch
   - "Good morning. 7 tasks planned." (3s auto-dismiss)
   - Shows carry forward count if applicable

### Phase 4: Enhance Execution Panel

**Goal:** Feature-complete execution panel.

1. Add next task preview
2. Add daily progress bar (tasks completed / total)
3. Add session counter (Session #3)
4. Right-click context menu: Pause, Resume, Complete, Hide Overlay, Open Workspace
5. Click-through mode toggle (small icon)
6. Configurable opacity from Settings

### Phase 5: Move Business Logic to Rust

**Goal:** Thin frontend, thick backend.

1. Move timer calculation to Rust service
2. Create TimerService in Rust that manages intervals and emits events
3. Frontend subscribes to timer events and renders
4. Move carry forward decision processing to Rust
5. Create SearchService in Rust

### Phase 6: Keyboard & Polish

**Goal:** Comprehensive keyboard-first experience.

1. Tab order: Workspace → Execution Panel → Sidebar → Status Bar
2. Workspace keyboard shortcuts: arrows navigate tasks, Space to select, Enter to edit, Delete to delete
3. Execution panel shortcuts: P, C, B (Pause, Complete, Break)
4. Global shortcuts: Cmd+1 for Today, Cmd+2 for History, Cmd+3 for Settings
5. Tooltip hints on hover for all shortcuts
6. Smooth CSS transitions for state changes (expand/collapse with 200-300ms)
7. Review immersive entrance animation

### Phase 7: Missing Features

**Goal:** Parity with documented feature set.

1. History complete implementation
2. Deadline notifications (upcoming, reached, overdue)
3. Configurable keyboard shortcuts in Settings
4. Planner validation (duplicate title warning, empty list check)
5. Narrative journal generation (no low-level event timeline)
6. User-friendly error messages (no raw Rust strings in toasts)
7. Backup/export/import

---

## 8. Implementation Order

Each phase produces a working, buildable application.

| Phase | Est. Effort | Delivers |
|-------|-------------|----------|
| **1 — Layout Restructure** | High | Single workspace with 4 regions, no page navigation |
| **2 — State Components** | High | All workspace states functional (planning, working, break, review, idle) |
| **3 — Overlays** | Medium | Search, recovery, greeting as overlays |
| **4 — Execution Panel** | Medium | Feature-complete execution panel |
| **5 — Rust Logic** | Medium | Timer and business logic in backend |
| **6 — Keyboard & Polish** | Low | Comprehensive keyboard support + animations |
| **7 — Missing Features** | Low-Medium | History, notifications, validation, narrative journal |

---

## 9. Visual Hierarchy Verification

Every UI decision must answer these three questions:

> **What am I working on?** → Current Task in Execution Panel (largest text)
> **How long have I been working?** → Timer in Execution Panel (second largest)
> **What should I do next?** → Next Task in Execution Panel + Task Queue in Workspace

If a component does not help answer one of these questions, it does not belong in the primary interface.
