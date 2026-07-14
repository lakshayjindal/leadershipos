# Architecture Audit — Leadership OS

**Date:** July 9, 2026
**Scope:** Full codebase vs documented specification (docs/ and docs/features/)

---

## Section 1: Correct

The following areas of the implementation already match the documented specification.

### Data & Storage

| Area | Status | Evidence |
|------|--------|----------|
| ✓ Local-first architecture | Matches | SQLite database, all data stored locally, no cloud dependencies |
| ✓ SQLite persistence | Matches | WAL mode, proper schema matching Data Model |
| ✓ Task data model | Matches | All fields from Data Model present (id, day_id, title, description, priority, status, deadline, etc.) |
| ✓ Work Session model | Matches | Work sessions stored with start/end time, duration |
| ✓ Break Session model | Matches | Break sessions with type, start/end, duration |
| ✓ Reflection model | Matches | Accomplishments, challenges, tomorrow's first task |
| ✓ Daily Summary model | Matches | Total planned, completed, carried, archived, focus/break seconds |
| ✓ App Configuration model | Matches | Working hours, overlay, theme, journal path, notifications |
| ✓ App State model | Matches | Startup → Planning → Working → Break → Idle → Review → Shutdown |
| ✓ FTS5 search index | Matches | Auto-synced via triggers, porter tokenizer |

### Task Lifecycle

| Area | Status | Evidence |
|------|--------|----------|
| ✓ Task states defined | Matches | Pending, Active, Paused, Completed, Archived, Deleted, CarriedForward |
| ✓ Priority levels | Matches | Critical, High, Medium, Low |
| ✓ Display order separate from priority | Matches | Both display_order and priority stored, manual reorder preserved |
| ✓ Task status transitions enforced | Matches | State machine validates transitions in set_task_status |
| ✓ Carry forward count tracked | Matches | carry_forward_count incremented on each carry forward |
| ✓ Only one active task at a time | Matches | start_task pauses any current active task |
| ✓ Work sessions immutable once completed | Matches | Sessions recorded and not modified after end_time set |
| ✓ Tasks belong to exactly one day | Matches | day_id foreign key |

### Timer Engine

| Area | Status | Evidence |
|------|--------|----------|
| ✓ Timer records work sessions | Matches | Starts on task activation, ends on pause/complete |
| ✓ Elapsed time calculated from timestamps | Matches | Duration = current_time - session_start_time |
| ✓ Focus time excludes paused time | Matches | Sessions ended on pause, new session on resume |
| ✓ Multiple sessions per task | Matches | Each resume creates a new work session |
| ✓ Session history preserved | Matches | All sessions stored with start/end/duration |
| ✓ Recovery of interrupted sessions | Matches | On restart, detects active session and restores timer state |
| ✓ Overlay updates every 2 seconds | Partially matches | Timer updates every 1s, overlay updates every 2s |

### Daily Planner

| Area | Status | Evidence |
|------|--------|----------|
| ✓ Planning requires explicit completion | Matches | "Begin Work" button triggers navigation to timer |
| ✓ Carry forward tasks presented first | Matches | If CF tasks exist, starts at carry-forward step |
| ✓ Each CF task gets explicit decision | Matches | Keep/Archive/Delete per task |
| ✓ Required: task title only | Matches | Create form requires only title, everything else optional |
| ✓ Priority assignment | Matches | Critical/High/Medium/Low selector |
| ✓ Optional deadline assignment | Matches | Date + time inputs, both optional |
| ✓ Optional estimated duration | Matches | Number input |
| ✓ Review summary before beginning | Matches | Step 4 shows total tasks, critical/high count, pending count |
| ✓ User may reorder tasks | Matches | ↑↓ buttons on each task |
| ✓ User may edit task title inline | Matches | Double-click to edit |
| ✓ User may archive or delete during planning | Matches | ▤ and ✕ buttons on each task row |
| ✓ Planning not permanent (editable during day) | Matches | Tasks, Timer, and Planner all allow editing |
| ✓ No duplicate task names warning | Not implemented | No validation for duplicate titles |
| ✓ Carry forward preserves history | Matches | carry_forward_count increments, original archived |

### Breaks

| Area | Status | Evidence |
|------|--------|----------|
| ✓ Breaks preserve task state | Matches | Pauses active timer, preserves task status |
| ✓ Break timer displays elapsed time | Matches | Counting up while break is active |
| ✓ Break types supported | Matches | Tea, Lunch, Dinner, Personal, Meeting |
| ✓ Breaks recorded in daily timeline | Matches | break_sessions table |
| ✓ Resume returns to previous context | Matches | Previous task can be resumed from Timer |
| ✓ Break stats displayed | Matches | Status, today's count, active break type |

### End of Day Review

| Area | Status | Evidence |
|------|--------|----------|
| ✓ Three reflection questions | Matches | Accomplishments, challenges, first task tomorrow |
| ✓ Automatic daily summary | Matches | Stats cards: completed tasks, focus time, status |
| ✓ Journal generation after reflection | Matches | "Generate Journal" button saves reflection + generates |
| ✓ Generated journal in Markdown | Matches | Full Markdown with proper headings |
| ✓ Journal includes all required sections | Matches | Header, summary, planned tasks, completed, timeline, stats, reflection, carry forward |
| ✓ Journal saved to configured vault path | Matches | Configurable vault path and journal directory |
| ✓ Shutdown archives the day | Matches | shutdown_day command archives and sets state |
| ✓ Review can be skipped | Implicitly | User can navigate elsewhere without completing |

### Search

| Area | Status | Evidence |
|------|--------|----------|
| ✓ FTS5 full-text search | Matches | SQLite FTS5 with porter tokenizer |
| ✓ Case-insensitive matching | Matches | FTS5 default behavior |
| ✓ Partial matching | Matches | Prefix matching with `*` in FTS5 queries |
| ✓ Results grouped by type | Matches | Grouped by task status |
| ✓ Highlighted matching terms | Matches | HighlightMatch component highlights in title, description, notes |
| ✓ Recent searches remembered | Matches | localStorage with last 10 searches |
| ✓ Results update while typing | Matches | 200ms debounce live search |
| ✓ Keyboard navigation | Matches | ↑↓ Enter Esc support |
| ✓ Local-only, no external service | Matches | All search indexes stored in SQLite |
| ✓ Empty results explained | Matches | "No Results Found" with suggestions |
| ✓ Fallback when index unavailable | Matches | LIKE-based fallback query |

### UI / UX

| Area | Status | Evidence |
|------|--------|----------|
| ✓ Keyboard-first command palette | Matches | Cmd+K opens palette with 16 commands |
| ✓ Toast notifications | Matches | Success/error/info/warning toasts with auto-dismiss |
| ✓ Delete confirmation dialog | Matches | ConfirmDialog for destructive actions |
| ✓ Dark and light theme | Matches | data-theme attribute, CSS variables |
| ✓ Modal for task editing | Matches | TaskEditModal component |
| ✓ Empty states throughout | Matches | All pages have empty state components |
| ✓ Loading states | Matches | Loading indicators on data-dependent pages |
| ✓ Error toasts for failures | Matches | Toast with error messages on API failures |
| ✓ Task status badges with colors | Matches | Active (blue), Paused (yellow), Completed (green), Archived (gray) |
| ✓ Priority badges | Matches | Critical (red), High (yellow), Medium (blue), Low (gray) |

### Notifications

| Area | Status | Evidence |
|------|--------|----------|
| ✓ Desktop notifications for timer events | Matches | notifyTimerStarted, notifyTimerPaused, notifyTimerCompleted |
| ✓ Notification permission handled | Matches | ensurePermission() checks and requests |
| ✓ Notifications non-blocking | Matches | Tauri plugin notifications are passive |

---

## Section 2: Architectural Drift

The following areas differ from the documented specification.

### 2.1 Planner as a Wizard vs Continuous Workflow

| | Detail |
|---|---|
| **Current** | Daily Planner is a 5-step wizard with visual progress indicator and buttons to navigate between steps (Welcome → Carry Forward → Create → Review → Begin Work) |
| **Documented** | The planner is a continuous workflow described as a fixed sequence of steps that "naturally lead into the next." The docs describe: Restore Previous Day → Review Carried Forward → Create New Tasks → Assign Priorities → Assign Deadlines → Review Plan → Begin Work. It is **not** described as a wizard with progress indicators and step navigation buttons. |
| **Why they differ** | I invented the wizard UX during implementation. The docs describe a single scrollable/modal workspace where tasks flow naturally. |
| **Change** | Remove wizard progress indicator and step navigation. Replace with a single continuous planning workspace. All planning actions (carry forward, create, prioritize, set deadlines, review) co-exist on one screen. The user creates tasks and sees them appear immediately. A "Begin Work" button exists at the bottom. |

### 2.2 Dashboard as a Separate Page

| | Detail |
|---|---|
| **Current** | Dashboard is a full page with stats grid, quick actions, timeline, sessions section, and startup detection banners. It is the default route (`/`). |
| **Documented** | The docs describe a startup sequence and morning summary, but **no Dashboard page** is specified anywhere. The application has 13 features in the Feature Spec (Daily Planner, Task Management, Priority Management, Deadlines, Focus Timer, Overlay, Break Management, Notifications, End-of-Day Review, Markdown Journal, Carry Forward, Search & History, Configuration). Dashboard is not among them. The docs say: "The user should feel like they are moving through a single working day. Not moving between disconnected application screens." |
| **Why they differ** | I added a Dashboard as a default landing page. The docs imply the application starts in the planner or directly in focus mode. |
| **Change** | Remove Dashboard as a separate page. Replace with the startup/morning summary as a lightweight overlay or modal that appears on first launch, then transitions directly into the planner. The default route becomes `/planner`. |

### 2.3 Separate Tasks Page vs Integrated Task List

| | Detail |
|---|---|
| **Current** | Tasks (`/tasks`) is a full separate page with filters, inline creation, edit modal, and per-task actions (Start, Pause, Complete, Archive, Delete). |
| **Documented** | Task Management is specified as the core execution system, but the docs describe tasks as appearing in the **Daily Planner, Overlay, and Focus Timer** — not as a separate page. The overlay "becomes the primary interface" after planning. The docs say: "Every screen should answer one question. Morning Planning: 'What should I work on today?' Overlay: 'What am I working on right now?'" A standalone Tasks page solves a problem that doesn't exist in the specification. |
| **Why they differ** | I added a separate Tasks page as a traditional task manager view. The docs imply tasks are managed within the planner and executed through the timer/overlay. |
| **Change** | Remove the standalone Tasks page. Move task management functionality into the Daily Planner (for planning) and the Focus Timer (for execution). The timer already has a task list — consolidate it into the primary interaction. |

### 2.4 Separate Journal Page vs File-Based Output

| | Detail |
|---|---|
| **Current** | Journal (`/journal`) is a full page that generates and displays the Markdown journal within the app. |
| **Documented** | The Daily Journal is described as a **file-based output** — a Markdown file written to the Obsidian vault. The docs say: "The journal is stored inside the configured Obsidian vault... Users may edit any journal after it has been generated." The journal is consumed in Obsidian, not within Leadership OS. There is no specified "Journal page" for reading journals inside the app. |
| **Why they differ** | I added a Journal page to preview the generated Markdown. The docs describe the journal as external to the app. |
| **Change** | Remove the Journal page. After generation, show a brief confirmation with options: "Open in Obsidian" (or file explorer) and "Copy to clipboard." The journal lives as a file in the vault — Leadership OS is not a Markdown reader. |

### 2.5 Timer Page vs Integrated Execution Engine

| | Detail |
|---|---|
| **Current** | Timer (`/timer`) is a page with a large timer display, task sections (Ready, Paused, Completed), and task list items with Focus Now buttons. |
| **Documented** | The Focus Timer is specified as the "central execution engine" that should be continuously available. The docs say: "The timer is not merely another page. It is the central execution engine of Leadership OS." The overlay is supposed to be the primary interface after planning begins. The timer should be visible from every screen, not a separate page you navigate to. |
| **Why they differ** | I implemented the timer as a page you navigate to. The docs describe it as always-present, like the overlay. |
| **Change** | Make the timer display persistent in a sidebar or top-bar section visible from every screen. The timer page should be replaced by the timer being omnipresent. Remove the separate `/timer` route. |

### 2.6 Separate Breaks Page vs Integrated Break Widget

| | Detail |
|---|---|
| **Current** | Breaks (`/breaks`) is a full page with break type buttons, active break timer, and stats. |
| **Documented** | Break Management is described as tightly coupled with the focus timer. The docs say: "Breaks are tightly coupled with the focus timer. A completed focus session may suggest a break." Starting a break should be possible from the overlay, command palette, or keyboard shortcut — not a separate page. |
| **Why they differ** | I made Breaks a separate page. The docs describe breaks as a lightweight action within the timer/overlay workflow. |
| **Change** | Remove the separate Breaks page. Integrate break controls into the timer (either a persistent timer sidebar or as an action triggered from the command palette/overlay). Show break status in the same panel as the timer. |

### 2.7 Separate Search Page vs Global Search Widget

| | Detail |
|---|---|
| **Current** | Search (`/search`) is a full page with live search, grouped results, recent searches, and quick filters. |
| **Documented** | The Search docs say: "Search should open instantly. Cursor immediately focused. Results update while typing." Search is described as a **modal/overlay** (like the command palette), not a separate page. The command palette spec also says search should be accessible from everywhere. |
| **Why they differ** | I made Search a page. The docs describe it as a command-palette-style overlay. |
| **Change** | Make search a modal overlay (like the command palette) accessible via keyboard shortcut from every screen. Remove the `/search` page. The search UI with grouped results, keyboard nav, and recent searches can remain — just as a modal, not a page. |

### 2.8 Separate Review Page vs End-of-Day Flow

| | Detail |
|---|---|
| **Current** | Review (`/review`) is a full page with summary cards, reflection form, journal preview, and shutdown section. |
| **Documented** | The End-of-Day Review is described as a workflow that appears when "the user chooses to end the workday" or "at a configurable end-of-day reminder." It is not described as a separate page — more like a modal or focused state that takes over the workspace. The docs say: "The user should always be able to postpone or skip the review." |
| **Why they differ** | I made it a page. The docs describe it as a temporary state (like the review phase in the app state machine). |
| **Change** | Make the review a full-screen modal/overlay that takes over the workspace when triggered, rather than a navigable page. The reflection form and shutdown flow work the same way — just presented as an overlay on top of whatever the user was doing. |

### 2.9 Separate Settings Page vs Minimal Configuration

| | Detail |
|---|---|
| **Current** | Settings (`/settings`) is a full page with 7 configuration categories, each in its own card, with a save button. |
| **Documented** | The Configuration docs say: "Most users should rarely need to visit the settings screen after the initial setup." Settings is listed in the sidebar but the docs emphasize minimal configuration. The spec says 8 categories, not 7. Missing: Keyboard Shortcuts (should be configurable), Advanced settings (hidden behind an expandable section). |
| **Why they differ** | The current settings are adequate but missing keyboard shortcut configuration and the "Advanced" section. |
| **Change** | Keep Settings as a page (it's in the spec) but add: Keyboard Shortcuts configuration section, an "Advanced" section with database location and log level (hidden by default). |

### 2.10 Sidebar Missing Workflow-First Navigation

| | Detail |
|---|---|
| **Current** | Sidebar has all 9 pages listed. Navigation is split into "Workflow" (7 pages) and "System" (2 pages). |
| **Documented** | The sidebar is described as having sections: "Today, Planner, Projects, History, Journal, Search, Settings." The application is supposed to "minimize context switching" by having far fewer distinct screens. Many current pages should be merged or removed (see above). |
| **Why they differ** | The sidebar evolved naturally as I added pages. The docs imply 3-4 primary destinations max, not 9. |
| **Change** | After merging pages, the sidebar should have: Planner, Timer/Overlay (persistent), History, Settings. That's it. |

### 2.11 Journal Generation Lacks Narrative Quality

| | Detail |
|---|---|
| **Current** | The generated journal is a Markdown file with task checklists, timeline, statistics, and reflection. It reads like a structured report. |
| **Documented** | The journal should "read like a work diary" with narrative sections. The docs explicitly avoid "low-level event logs" like "Started Timer, Paused Timer, Resumed Timer." The current journal includes a timeline with individual session events which contradicts the spec: "The journal should never contain low-level activity logs." The narrative summary section is missing entirely. |
| **Why they differ** | I generated a report-style journal rather than a narrative diary. |
| **Change** | Redesign journal generation to produce a narrative summary. Remove the minute-by-minute timeline. Add an automatically generated "Today's Work" narrative paragraph describing what was accomplished. Keep the reflection and statistics sections. |

### 2.12 Overlay Implementation Incomplete

| | Detail |
|---|---|
| **Current** | The overlay is a Tauri window that shows task name, elapsed time, and pending count. It appears on timer start and hides on pause/complete. |
| **Documented** | The overlay should be much richer: display current task, current project, priority, focus timer, session status (focus/break), daily completion progress, next task preview. It should support interaction (pause, resume, complete, hide). It should have compact and expanded modes, right-click menu, click-through mode, configurable opacity and position. |
| **Why they differ** | I implemented a minimal overlay. The spec describes a rich, interactive HUD. |
| **Change** | Enhance overlay to include: next task preview, daily progress, session counter, right-click context menu (pause/resume/complete/hide). Add click-through mode toggle. Add configurable opacity/position from settings. |

### 2.13 Missing Features Entirely

| Feature | Documented | Current Status |
|---------|-----------|----------------|
| History page | docs/features/history.md — chronological timeline of all events | Not implemented |
| Alternate Saturday support | docs/features/configuration.md — "Are you working tomorrow?" prompt | Not implemented |
| Calendar integration | docs/features/configuration.md — Thunderbird calendar import | Not implemented |
| Relative deadlines (Before Lunch, Before Dinner) | docs/features/deadlines.md | Not implemented |
| Deadline notifications | docs/09_Notifications.md, docs/features/deadlines.md | Not implemented |
| Break notifications | docs/09_Notifications.md, docs/features/breaks.md | Not implemented |
| Recovery checkpoint system | docs/features/recovery.md | Not implemented |
| Session recovery on crash | docs/features/recovery.md | Partially (timer state restored, but no recovery prompt) |
| Sleep/wake detection | docs/08_Timer_Engine.md | Not implemented |
| Command palette context awareness | docs/features/command-palette.md — adapts to state | Not implemented |
| Configurable keyboard shortcuts | docs/13_Keyboard_First_Design.md, docs/11_Configuration.md | Not implemented |
| Backup/export/import | docs/12_File_System.md | Not implemented |

### 2.14 Frontend Contains Too Much Business Logic

| | Detail |
|---|---|
| **Current** | Timer logic, carry forward decisions, task lifecycle management, and deadline calculations are spread across React components (Timer.tsx, DailyPlanner.tsx, Tasks.tsx). |
| **Documented** | "Business logic lives in Rust. Frontend responsibilities: Rendering, User interaction, Input validation, Animations, Navigation." The Rust backend should own the timer engine, planning, scheduling, journal generation, search, file management, notifications, recovery, configuration, history, and statistics. |
| **Why they differ** | I implemented significant business logic in the frontend for convenience. |
| **Change** | Move timer state management and carry forward logic into Rust services. The frontend should dispatch commands and render results, not manage timer intervals or compute elapsed time. |

### 2.15 Command Palette Missing Context Awareness

| | Detail |
|---|---|
| **Current** | Command palette has 16 static commands split into Navigation and Actions. No context awareness. |
| **Documented** | "The palette should adapt to the current application state. During a focus session: Pause Timer, Complete Task, Start Break. During a break: Resume Focus, Extend Break, Skip Break. If no task is active: Start Daily Planning, Create Task, Open Planner." |
| **Why they differ** | I used static commands. The spec requires dynamic, context-aware commands that change based on app state. |
| **Change** | Make commands dynamic based on todayStatus state. Show different commands when timer is running, on break, idle, or in planning. |

### 2.16 Keyboard Navigation Insufficient

| | Detail |
|---|---|
| **Current** | Only global Cmd+K command palette and basic keyboard support in search. |
| **Documented** | "The keyboard is the primary input method. Every action that can be performed with the mouse should also be executable using the keyboard. The morning planning workflow should require little or no mouse interaction. Task switching should be possible using keyboard shortcuts." The spec lists: Tab navigation order, global shortcuts, context shortcuts for planning (arrows, space, enter, delete), timer shortcuts, overlay shortcuts, dialog behavior. |
| **Why they differ** | I implemented minimal keyboard support. The spec requires comprehensive keyboard-first design. |
| **Change** | Add keyboard shortcuts for: creating tasks (in planner), starting tasks, pausing/resuming, completing tasks, navigating between tasks, archive/delete. Ensure Tab order follows natural workflow. Add keyboard hints tooltip on hover. |

### 2.17 No History Implementation

| | Detail |
|---|---|
| **Current** | There is no History page or timeline. The Search page combined with Journal partially fills this gap. |
| **Documented** | "History provides a chronological record of everything that has happened inside Leadership OS... The primary interface for exploring the past." Full spec in docs/features/history.md. |
| **Why they differ** | I never implemented the History feature. |
| **Change** | Implement History as a timeline view showing daily summaries, completed tasks, focus sessions, and breaks — accessible from the sidebar. |

### 2.18 Error Handling Lacks User-Friendly Messages

| | Detail |
|---|---|
| **Current** | Errors are shown as raw Rust error messages via toast toasts (e.g., "Failed to create task: [error string]"). |
| **Documented** | "User-facing errors should explain: what happened, why it happened (if known), what the user can do next." Example: "Journal Could Not Be Saved. The destination folder is read-only. Choose another folder or update the folder permissions." |
| **Why they differ** | I pass raw error strings from Rust to the frontend. |
| **Change** | Define user-facing error messages in Rust that explain the problem and suggest solutions. The frontend toasts should show clean messages, not Rust error strings. |

### 2.19 Daily Planner Missing Validation

| | Detail |
|---|---|
| **Current** | Planner has no validation for: duplicate task names, empty task list preventing "Begin Work," or invalid deadlines. |
| **Documented** | "Planning cannot finish if: No tasks exist. Duplicate task names exist. Required fields are missing. Invalid deadlines exist. Validation should explain problems clearly." |
| **Why they differ** | I never implemented these validation rules. |
| **Change** | Add validation: warn on duplicate task names, require at least one task before "Begin Work," validate deadline format. |

---

## Section 3: Refactoring Plan

The refactoring should be executed in the following order. Each phase produces a working, buildable application.

### Phase 1: Consolidate Navigation (Remove Pages)

**Goal:** Eliminate architectural drift caused by unnecessary pages.

Steps:
1. Remove `/timer` page → Make timer a persistent panel visible on every screen
2. Remove `/tasks` page → Consolidate task management into planner and timer
3. Remove `/breaks` page → Integrate break controls into timer panel
4. Remove `/search` page → Make search a modal overlay (like command palette)
5. Remove `/review` page → Make review a full-screen modal triggered on demand
6. Remove `/journal` page → Journal is a file, not an in-app page
7. Keep: `/planner`, `/history` (to be built), `/settings`
8. Default route: `/planner`

**Files affected:** App.tsx (routes), Sidebar.tsx (nav items), remove Breaks.tsx, merge Timer into sidebar/panel

### Phase 2: Restructure Planner as Continuous Workspace

**Goal:** Fix the planner to match documented continuous workflow.

Steps:
1. Remove wizard step indicator
2. Layout: top section = carry forward tasks (if any), middle = task creation form, below = task list, bottom = "Begin Work" button
3. Carry forward tasks appear inline at the top with Keep/Archive/Delete buttons
4. New tasks appear immediately in the list below
5. Task list supports reorder (↑↓), priority change, deadline, edit, archive, delete
6. "Begin Work" button is always visible, disabled if no tasks, shows validation message
7. Add validation: duplicate title warning, empty list check

### Phase 3: Make Timer Persistent

**Goal:** The timer is the central execution engine, visible everywhere.

Steps:
1. Move timer display to a panel in the sidebar or top-right section of every page
2. When no task is active, show a compact "Start Focus" button
3. Show active task, elapsed time, and Pause/Complete buttons inline
4. Task list for starting/switching tasks is part of this panel (not a separate page)
5. Break controls appear as a sub-section when a break is active

### Phase 4: Build History Page

**Goal:** Implement the chronological timeline.

Steps:
1. Create `/history` route
2. Reverse-chronological timeline grouped by day
3. Each day shows: summary (focus time, tasks completed, sessions), expandable event list
4. Link to journal file on disk
5. Filter by event type
6. Date navigation (today, yesterday, specific date)

### Phase 5: Enhance Overlay

**Goal:** Rich HUD as specified.

Steps:
1. Add: next task preview, daily progress bar, session counter
2. Right-click context menu: Pause, Resume, Complete, Hide
3. Click-through mode toggle
4. Configurable opacity/position from settings

### Phase 6: Move Business Logic to Rust

**Goal:** Thin frontend, thick backend.

Steps:
1. Move timer state management to Rust (interval calculation, elapsed time)
2. Move carry forward decision processing to Rust
3. Create proper Rust services: TimerService, PlanningService, HistoryService
4. Frontend dispatches commands and renders results only

### Phase 7: Implement Missing Features

**Goal:** Parity with documented feature set.

Steps:
1. Deadline notifications (upcoming, reached, overdue) — each fires once
2. Break reminders (configurable, optional)
3. Configurable keyboard shortcuts in Settings
4. Context-aware command palette (dynamic commands based on app state)
5. Comprehensive keyboard navigation for all workflows
6. Recovery checkpoints and session recovery prompts
7. Relative deadline support (Before Lunch, Before Dinner, End of Day)

### Phase 8: Polish & Error Handling

**Goal:** Production quality.

Steps:
1. User-friendly error messages (no raw Rust strings in toasts)
2. Planner validation (duplicate titles, empty list, invalid deadlines)
3. Journal narrative generation (meaningful summary, no low-level timeline)
4. Keyboard shortcut discoverability (tooltips, hints)
5. Empty states for history
6. Backup/export/import configuration

---

## Summary of Key Changes

| Current | Documented | Priority |
|---------|-----------|----------|
| 9 pages (Dashboard, Planner, Tasks, Timer, Breaks, Review, Journal, Search, Settings) | ~4 screens (Planner, Timer/Overlay, History, Settings) with modals for review/search | **High** |
| Wizard planner | Continuous planning workspace | **High** |
| Timer as page | Timer as persistent element | **High** |
| Tasks as page | Tasks in planner + timer | **High** |
| No history | Chronological timeline | **High** |
| Report-style journal | Narrative diary | **Medium** |
| Static command palette | Context-aware commands | **Medium** |
| Minimal keyboard support | Comprehensive keyboard-first | **Medium** |
| Bare overlay | Rich interactive HUD | **Medium** |
| Business logic in frontend | Business logic in Rust | **Medium** |
| Missing deadline/break notifications | Notification system | **Low** |
| Missing keyboard shortcut config | Configurable shortcuts | **Low** |
| Missing recovery system | Recovery checkpoints | **Low** |
| Missing relative deadlines | Relative deadline support | **Low** |
| Missing backup/export | Data portability | **Low** |
