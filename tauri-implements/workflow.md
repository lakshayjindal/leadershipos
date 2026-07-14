# Leadership OS — User Workflow

This document describes the exact user flow of Leadership OS as currently implemented. It reflects how a user interacts with the application throughout a full working day.

---

## Application Structure

Leadership OS is a single-page application with 9 pages, navigated via a sidebar. The app has a dark/light theme, a command palette (`Cmd+K`), and a timer overlay window.

### Navigation

The sidebar is divided into two sections:

**Workflow** (primary pages):
| Page | Route | Purpose |
|------|-------|---------|
| Dashboard | `/` | Overview, stats, quick actions, startup detection |
| Planner | `/planner` | Guided morning planning in 5 steps |
| Tasks | `/tasks` | Full task management with filters |
| Timer | `/timer` | Focus timer with task execution |
| Breaks | `/breaks` | Break management (tea, lunch, dinner, etc.) |
| Review | `/review` | End-of-day reflection and shutdown |
| Journal | `/journal` | Generated Markdown journal preview |

**System** (utility pages):
| Page | Route | Purpose |
|------|-------|---------|
| Search | `/search` | FTS5 full-text search with live results |
| Settings | `/settings` | Configuration for work hours, timer, theme, etc. |

The sidebar also shows the current app state (idle, planning, working, break, etc.) and a task completion counter at the bottom.

---

## Phase 1 — Startup

**Trigger:** User opens the application.

**What happens:**
1. The app loads today's status and configuration from the backend
2. A loading screen ("Loading Leadership OS...") is shown while data loads
3. The theme (dark/light) is applied from saved config

**What the user sees on the Dashboard:**

If the previous day has unfinished tasks (detected via carry-forward check):
```
┌──────────────────────────────────────────────┐
│ ↻ Previous Day Needs Attention                │
│ 3 tasks were left unfinished. Review and      │
│ decide what to carry forward.                 │
│                                [Review Tasks] │
└──────────────────────────────────────────────┘
```

If today hasn't been planned yet (no tasks exist):
```
┌──────────────────────────────────────────────┐
│ Good Morning                                 │
│ Your day hasn't been planned yet.            │
│ Plan your tasks to begin focused work.       │
│                           [📋 Start Planning]│
└──────────────────────────────────────────────┘
```

If there's an active task from a previous session:
```
┌──────────────────────────────────────────────┐
│ CURRENTLY WORKING                             │
│ Write Q2 Report                    [⏱ Open  │
│ Priority: [high]                    Timer]   │
└──────────────────────────────────────────────┘
```

---

## Phase 2 — Morning Planning

**Accessed from:** Sidebar → Planner (📋) or Dashboard → "Start Planning"

The Daily Planner guides the user through a **5-step wizard** with a visual progress indicator at the top showing: `Start → Carry Forward → Plan → Review → Begin Work`

### Step 1: Welcome 🌅

The user sees:
- A greeting ("Good Morning" / "Good Afternoon" / "Good Evening")
- A brief description of the planning process
- A "Start Planning →" button
- A "Skip to Review" button (if tasks already exist)

The app automatically routes to:
- **Carry Forward** step if unfinished tasks exist from previous days
- **Welcome** step if no tasks exist yet
- **Review** step if tasks already exist for today

### Step 2: Carry Forward ↻

Triggered when tasks from previous days are found.

**What the user sees:**
```
┌──────────────────────────────────────────────┐
│ ↻ Unfinished Tasks Found                      │
│ 2 tasks from previous days need a decision    │
│                                                │
│ ┌──────────────────────────────────────────┐  │
│ │ [high] Write Q2 Report        [✓ Keep]   │  │
│ │                          [▤ Archive]     │  │
│ │                          [✕ Delete]      │  │
│ └──────────────────────────────────────────┘  │
│ ┌──────────────────────────────────────────┐  │
│ │ [med] Fix login bug         [✓ Keep]     │  │
│ │ ↻ x2                        [▤ Archive]  │  │
│ │                             [✕ Delete]   │  │
│ └──────────────────────────────────────────┘  │
│                                [Skip All]     │
│                    [Apply Decisions (2)]      │
└──────────────────────────────────────────────┘
```

**User actions:**
- For each task, choose: ✓ Keep (bring into today), ▤ Archive (set aside), or ✕ Delete
- Click "Apply Decisions" to process all at once
- Click "Skip All" to skip this step

**System behavior:**
- "Keep" → copies the task to today with `carried_forward` status and incremented `carry_forward_count`
- "Archive" → sets the original task status to `archived`
- "Delete" → sets the original task status to `deleted`
- A toast confirms: "Processed N carried forward tasks"

### Step 3: Create Tasks ✏️

**What the user sees:**
```
┌──────────────────────────────────────────────┐
│ ✏️ New Task                                   │
│                                                │
│ What do you want to accomplish?               │
│ ┌──────────────────────────────────────────┐  │
│ │ Write Q2 Report                          │  │
│ └──────────────────────────────────────────┘  │
│                                                │
│ Description (optional)                         │
│ ┌──────────────────────────────────────────┐  │
│ │ Summarize Q1 data and outline Q2 goals   │  │
│ └──────────────────────────────────────────┘  │
│                                                │
│ Priority    Est. Duration (min)   Deadline     │
│ ┌──────┐    ┌───────────────┐    ┌────┬────┐  │
│ │High │    │ 45            │    │date│time│  │
│ └──────┘    └───────────────┘    └────┴────┘  │
│                                                │
│ [+ Add Task]     [Done Planning → Review]      │
└──────────────────────────────────────────────┘
```

**User actions:**
- Enter a task title (required)
- Optionally: description, priority (default: Medium), estimated duration, deadline (date + time)
- Click "+ Add Task" to add it to the list
- Click "Done Planning → Review" when finished

As tasks are added, they appear below in a list with priority badges and ↑↓ buttons for reordering.

### Step 4: Review & Prioritize 📋

**What the user sees:**
```
┌──────────────────────────────────────────────┐
│ 📋 Review Your Plan                           │
│ 4 tasks planned · Reorder to set priority     │
│                                                │
│ 1 [high] Write Q2 Report    [↑] [↓] [▤] [✕]  │
│ 2 [crit] Fix login bug      [↑] [↓] [▤] [✕]  │
│ 3 [med]  Update docs        [↑] [↓] [▤] [✕]  │
│ 4 [low]  Clean up code      [↑] [↓] [▤] [✕]  │
│                                                │
│ ┌──────────┬──────────────┬──────────┐        │
│ │Total Tasks│Critical/High │ Pending  │        │
│ │    4     │      2       │    4     │        │
│ └──────────┴──────────────┴──────────┘        │
└──────────────────────────────────────────────┘
```

**User actions:**
- Reorder with ↑↓ buttons
- Archive (▤) or Delete (✕) any task
- Double-click titles to rename inline
- Click "← Add More Tasks" to return to creation
- Click "✓ Begin Work →" to proceed

### Step 5: Begin Work 🚀

**What the user sees:**
```
┌──────────────────────────────────────────────┐
│ 🚀 Plan Complete                              │
│ 4 tasks ready. Time to execute.               │
│                                                │
│ [⏱ Start Focus Timer]  [☐ View All Tasks]     │
└──────────────────────────────────────────────┘
```

**User actions:**
- Click "Start Focus Timer" → navigates to `/timer`
- Click "View All Tasks" → navigates to `/tasks`

---

## Phase 3 — Focused Work

**Accessed from:** Sidebar → Timer (⏱), Planner → "Begin Work", or Dashboard → "Start Focus Timer"

### Timer Page

**Initial state (no active task):**
- Large timer display showing `0:00`
- Message: "Select a task below to start focusing"
- Tasks grouped into sections: "Ready to Focus", "Paused", "Completed"

**Starting a task:**
1. User clicks "Focus Now" on any pending task
2. Timer starts counting up every second
3. The timer card gets a blue border with an animated shimmer gradient
4. Current task name and start time appear below the timer
5. A desktop notification fires: "Focus started: [task name]"
6. A floating overlay window appears showing the task, elapsed time, and pending count
7. The overlay updates every 2 seconds

**During focused work:**
```
┌──────────────────────────────────────────────┐
│ ─────────────── 42:15 ────────────────────   │  ← shimmer gradient
│                                                │
│ Current Task                                   │
│ Write Q2 Report                    [high]      │
│ Started at 09:15:00                            │
│                                                │
│ [⏸ Pause]  [✓ Complete]                       │
│                                                │
│ 🔲 Timer overlay is active — click Pause or   │
│    Complete to dismiss                         │
└──────────────────────────────────────────────┘
```

**Task switching:**
1. User clicks "Focus Now" on a different pending task
2. The current task is automatically paused (session ended, status → paused)
3. A new work session starts for the selected task
4. The overlay updates immediately

**Pausing:**
1. User clicks "⏸ Pause"
2. Timer stops, work session is saved with duration
3. Overlay updates to "paused" state
4. Overlay is hidden after 2 seconds
5. Desktop notification: "Paused [task name] · [duration]"
6. Task status changes to `paused`
7. "▶ Resume" and "Unassign" buttons appear

**Completing:**
1. User clicks "✓ Complete"
2. Timer stops, completion timestamp recorded
3. Task moves to "Completed" section
4. Overlay is hidden
5. Desktop notification: "Completed [task name] · [duration]"
6. Next pending task is available to start

### Timer Overlay

A separate Tauri window that appears when a timer is running:

- **Borderless**, always-on-top, skips taskbar
- Shows: task name, elapsed time (HH:MM:SS), status (running/paused)
- Updates every 2 seconds
- Auto-hides when task is paused or completed
- Re-appears on app restart if a timer was running

---

## Phase 4 — Break Management

**Accessed from:** Sidebar → Breaks (☕)

### Starting a Break

**What the user sees:**
```
┌──────────────────────────────────────────────┐
│ Start a Break                                 │
│                                                │
│ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐  │
│ │  ☕    │ │  🍽   │ │  🌙   │ │  🧘   │  │
│ │ Tea    │ │ Lunch  │ │ Dinner │ │Personal│  │
│ │ Break  │ │        │ │        │ │        │  │
│ └────────┘ └────────┘ └────────┘ └────────┘  │
│ ┌────────┐                                     │
│ │  📋   │                                     │
│ │Meeting│                                     │
│ └────────┘                                     │
└──────────────────────────────────────────────┘
```

**System behavior:**
- The active task timer is automatically paused
- App state changes to `break`
- The break timer starts counting up

### During a Break

A yellow-bordered card shows:
- Break type icon and name
- Elapsed break time (counting up every second)
- Start time
- "▶ Resume Work" button

### Ending a Break

1. User clicks "▶ Resume Work"
2. Break session is saved with duration
3. App state returns to `working`
4. Previous task can be resumed from the Timer page

Stats shown: Status (On Break/Working), Today's Breaks count, Active Break type.

---

## Phase 5 — End of Day Review

**Accessed from:** Sidebar → Review (📝)

### Summary Display

Three cards at the top show:
- Completed Tasks (e.g., "3/5")
- Focus Time (e.g., "2h 30m")
- Status ("Pending Review" or "✓ Journaled")

### Reflection Form

Three structured questions:

1. **What did you accomplish today?** (textarea)
2. **What slowed you down today?** (textarea)  
3. **First thing to do tomorrow** (text input)

### Actions

- **"💾 Save Reflection"** — saves answers to the database
- **"📔 Generate Journal"** — saves reflection + generates Markdown journal

### Generated Journal Preview

The journal is displayed in a monospace card and includes:
- Date and day name
- Start/finish time
- Summary statistics (planned, completed, carried, focus time, break time)
- Planned tasks checklist
- Completed work with timestamps
- Timeline of all work sessions
- Work statistics table
- Reflection answers
- Carry forward items

### Shutdown

**"🚀 End Day & Shutdown"** button:
1. Saves reflection
2. Generates journal (saved to Obsidian vault if configured)
3. Ends any active work sessions
4. Sets day end time and status to `completed`
5. Sets app state to `shutdown`
6. Shows completion screen:

```
┌──────────────────────────────────────────────┐
│ 🌟 Day Complete                               │
│ Today's work has been archived. Your journal  │
│ has been saved.                               │
│                                                │
│ [Back to Dashboard]  [📔 View Journal]         │
└──────────────────────────────────────────────┘
```

---

## Phase 6 — Journal & History

**Accessed from:** Sidebar → Journal (📔)

Shows the generated Markdown journal for today. If no journal exists yet, prompts the user to complete the End of Day Review first.

Features:
- "📔 Generate Journal" button
- "📋 Copy" button to copy the Markdown to clipboard
- Monospace preview with scrolling

---

## Phase 7 — Search & History

**Accessed from:** Sidebar → Search (🔍) or `Cmd+K` → type "search"

### Live Search

- **200ms debounce** — results appear while typing, no button press needed
- **FTS5 full-text search** — searches title, description, and notes with prefix matching
- **LIKE fallback** — if FTS5 returns no results or query is short, falls back to LIKE search

### Search Results

Results are **grouped by status** in this order:
1. **Active** — currently being worked on
2. **Pending** — waiting to start
3. **Paused** — temporarily stopped
4. **Completed** — finished today
5. **Archived** — set aside

Each result shows:
- Title with highlighted matching terms
- Priority badge
- Status badge
- Duration (if tracked)
- Deadline (if set)
- Carry-forward count (if applicable)
- Date created
- Description/notes excerpts with highlighted matches

### Keyboard Navigation

| Key | Action |
|-----|--------|
| ↑↓ | Navigate results |
| Enter | Submit search / open result |
| Esc | Clear query and blur input |

### Recent Searches

- Last 10 searches stored in localStorage
- Displayed as clickable chips when search bar is empty
- "Clear" button to remove all recent searches

### Quick Filters

Buttons for quick searches: "High Priority", "Recent", "Completed", "Active"

---

## Task Management

**Accessed from:** Sidebar → Tasks (☐)

### Task List

All tasks for today displayed with:
- Checkbox (toggle complete/pending)
- Title (click to open edit modal)
- Priority badge (critical/high/medium/low)
- Status badge (● Working, ⏸ Paused, ✓ Done, ▤ Archived, ○ Pending)
- Duration (if tracked)
- Estimated duration (if set)
- Deadline (if set)

### Task Filters

Buttons above the list: All, Active, Pending, Completed, Archived

### Task Actions

Per task:
- **Pending** → "Start" button
- **Active** → "Pause" and "✓ Done" buttons
- **Paused** → "Resume" button
- **Completed** → "Reopen" button (sets back to pending)
- All non-active/completed → "Archive" and "Delete" buttons

### Create Task

Inline form with title and priority, or the full edit modal with:
- Title, description, priority, deadline (date + time), estimated duration, notes

### Edit Task

Modal with all fields. Save requires `Ctrl+Enter` or clicking "Save Changes". Toast confirms success or shows error.

### Delete Confirmation

Danger-styled dialog with task name: "Are you sure you want to delete [task]? This action cannot be undone."

---

## Settings

**Accessed from:** Sidebar → Settings (⚙)

### Configuration Categories

**Work Schedule:**
- Working Hours Start/End (time pickers)
- Lunch Time, Dinner Time (time pickers)

**Timer & Breaks:**
- Short Break Duration (minutes)
- Long Break Duration (minutes)
- Sessions Before Long Break
- Deadline Reminder (minutes before)

**Appearance:**
- Theme: Dark / Light
- Overlay Opacity (slider 0.2–1.0)
- Overlay Position: Top/Bottom × Left/Right

**Journal:**
- Markdown Vault Path (file path)
- Journal Directory name

**Notifications:**
- Enable Notifications (checkbox)
- Break Reminders (checkbox)
- Launch at System Startup (checkbox)

---

## Command Palette

**Trigger:** `Cmd+K` or `Ctrl+K`

### Navigation Commands
| Command | Shortcut |
|---------|----------|
| Dashboard | G D |
| Daily Planner | G P |
| Tasks | G T |
| Focus Timer | G M |
| Breaks | G B |
| End-of-Day Review | G R |
| Journal | G J |
| Search & History | G S |
| Settings | G , |

### Quick Actions
| Command | Shortcut |
|---------|----------|
| Create New Task | N |
| Start Focus Timer | S |
| Start Break | B |
| End Day & Review | E |
| Toggle Overlay | O |
| Search Tasks | / |

**Navigation:** ↑↓ to move, Enter to execute, Esc to close.

---

## Task Lifecycle (State Machine)

Every task follows a predefined state machine enforced by the backend:

```
                  ┌─────────┐
                  │ Created │
                  └────┬────┘
                       │
                       ▼
                  ┌─────────┐
         ┌───────│ Pending │───────┐
         │       └────┬────┘       │
         │            │            │
         ▼            ▼            ▼
    ┌────────┐  ┌─────────┐  ┌──────────┐
    │Archived│  │ Active  │  │ Deleted  │
    └────────┘  └──┬──┬──┘  └──────────┘
                    │  │
           ┌────────┘  └────────┐
           ▼                    ▼
      ┌────────┐          ┌───────────┐
      │ Paused │          │ Completed │
      └──┬──┬──┘          └─────┬─────┘
         │  │                   │
         │  │                   ▼
         │  └───────┐     ┌────────┐
         │          │     │ Closed │
         │          │     └────────┘
         ▼          ▼
     ┌────────┐ ┌──────────┐
     │ Active │ │ Archived │
     └────────┘ └──────────┘

Carried Forward:
  carried_forward → active | pending | archived | deleted
```

**Allowed transitions:**
| From | To |
|------|----|
| pending | active, archived, deleted |
| active | paused, completed, archived |
| paused | active, completed, archived |
| completed | pending (reopen), closed |
| carried_forward | active, pending, archived, deleted |

**Rules:**
- Only one task can be active at a time
- Starting a new task automatically pauses the current one
- Completed tasks can be reopened (set back to pending)
- Deletion requires confirmation
- Carried tasks show a ↻ counter for each time they've been carried

---

## Daily Cycle Summary

```
┌─────────────────────────────┐
│         STARTUP             │
│  • Restore today's data     │
│  • Detect previous day      │
│    incompleteness           │
│  • Show carry-forward alert │
└──────────┬──────────────────┘
           ▼
┌─────────────────────────────┐
│     MORNING PLANNING        │
│  • Welcome screen           │
│  • Carry forward decisions  │
│  • Create tasks             │
│  • Review & reorder         │
│  • Begin work               │
└──────────┬──────────────────┘
           ▼
┌─────────────────────────────┐
│       FOCUSED WORK          │
│  • Start timer on a task    │
│  • Timer counts up          │
│  • Overlay appears          │
│  • Notifications fire       │
│  • Pause / Switch / Complete│
└──────────┬──────────────────┘
           │
    ┌──────┴──────┐
    ▼              ▼
┌────────┐  ┌─────────────┐
│ BREAK  │  │ TASK SWITCH │
│ • Tea  │  │ • Pause cur │
│ • Lunch│  │ • Start new │
│ • etc. │  └─────────────┘
│Resume→ │       │
└────────┘       ▼
           ┌──────────────┐
           │ WORK CONTINUE│
           └──────────────┘
           │
           ▼
┌─────────────────────────────┐
│    END OF DAY REVIEW        │
│  • 3 reflection questions   │
│  • Save reflection          │
│  • Generate journal         │
│  • Shutdown & archive       │
└─────────────────────────────┘
```

---

## Data Persistence

All data is stored locally in a SQLite database (`leadership-os.db`) with WAL mode:

| Table | Purpose |
|-------|---------|
| `days` | One row per calendar day |
| `tasks` | All tasks with status, priority, timestamps |
| `work_sessions` | Individual focus sessions per task |
| `break_sessions` | Break periods per day |
| `reflections` | End-of-day reflection answers |
| `daily_summaries` | Calculated daily statistics |
| `configurations` | Key-value settings |
| `app_state` | Current application state |
| `tasks_fts` | FTS5 full-text search index |

**Search index (`tasks_fts`):**
- Automatically synchronized with `tasks` table via triggers
- Uses porter tokenizer with unicode support
- Prefix matching enabled for partial word search
- Automatically rebuilt on schema initialization if empty
