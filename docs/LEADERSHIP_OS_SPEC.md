# Leadership OS — Implementation Specification

> **Version:** 2.0  
> **Date:** July 20, 2026  
> **Platform:** Desktop (Linux, macOS, Windows)  
> **Framework:** Flet (Flutter-based)  
> **Language:** Python 3.10+  
> **Package Manager:** uv  
> **Storage:** SQLite + JSON + TOML  
> **License:** MIT

---

## Table of Contents

1. [Vision & Philosophy](#1-vision--philosophy)
2. [Technical Stack](#2-technical-stack)
3. [Project Structure](#3-project-structure)
4. [Data Model](#4-data-model)
5. [System Architecture](#5-system-architecture)
6. [UI Layout & Design](#6-ui-layout--design)
7. [Feature Specifications](#7-feature-specifications)
8. [Keyboard Shortcuts](#8-keyboard-shortcuts)
9. [System Tray & Overlay](#9-system-tray--overlay)
10. [Configuration System](#10-configuration-system)
11. [Error Handling & Recovery](#11-error-handling--recovery)
12. [Testing Strategy](#12-testing-strategy)
13. [Implementation Phases](#13-implementation-phases)
14. [Coding Standards](#14-coding-standards)

---

## 1. Vision & Philosophy

Leadership OS is a **local-first personal execution system** that reduces cognitive overhead by acting as an external executive system rather than a traditional productivity application.

### Core Principles (Non-Negotiable)

| # | Principle | Implementation Implication |
|---|-----------|---------------------------|
| 1 | **Local First** | All data in SQLite/JSON/TOML on disk. Zero network calls. |
| 2 | **Keyboard First** | Every action via keyboard shortcuts. Mouse optional. |
| 3 | **Zero Friction** | Minimum interaction for every action. No unnecessary dialogs. |
| 4 | **Execution Over Organization** | Help user DO work, not organize endlessly. |
| 5 | **One Current Task** | Exactly one task is Active at any time. |
| 6 | **Passive Awareness** | Dashboard, not notification system. |
| 7 | **Minimal Visual Noise** | Only essential information visible at all times. |
| 8 | **Reflection Is Part of Work** | Daily review is mandatory, brief, structured. |
| 9 | **Preserve Everything** | Nothing overwritten or lost. Permanent history. |
| 10 | **Reduce Cognitive Load** | Highest principle. User should never wonder what to do next. |

### Success Criteria

- User plans day in under 5 minutes
- User stays focused without constant app switching
- Any previous workday recalled in seconds
- Work resumes after interruptions without friction
- Complete history built over months and years
- Zero dependency on cloud services

---

## 2. Technical Stack

### Chosen Technologies

| Layer | Technology | Rationale |
|-------|-----------|-----------|
| **UI Framework** | Flet (Flutter-based) | Rich widget library, responsive layout, Material Design 3, async event loop, hot-reload, cross-platform (desktop + web + mobile) |
| **UI Styling** | Programmatic (Python) | All UI built via `ft.Container`, `ft.Column`, `ft.Row`, etc. No KV files needed — Flet uses Python-native UI construction |
| **Desktop** | Flet (Flutter Window) | Native desktop window via Flutter embedder, resizable, async |
| **System Tray** | `pystray` (cross-platform) | Cross-platform tray icon via pystray + Pillow for icon generation. Consistent API on Linux, macOS, Windows. |
| **Database** | SQLite via `sqlite3` stdlib | All structured data: tasks, sessions, breaks, reflections, summaries |
| **App State** | JSON (`state.json`) | Runtime state: current app state, active task, timer info, window position |
| **Config** | TOML (`config.toml`) | User configuration: working hours, theme, vault path, shortcuts |
| **Dependency Mgmt** | `uv` | Fast, reproducible builds, virtual environments |
| **Testing** | `pytest` | Full test suite with coverage reports |
| **Linting** | `ruff` | Fast Python linter and formatter |
| **Type Checking** | `pyright` | Static type analysis for better code quality |

### Python Version

- **Minimum:** Python 3.10
- **Recommended:** Python 3.12+

### Dependencies (pyproject.toml)

```toml
[project]
name = "leadership-os"
version = "0.1.0"
requires-python = ">=3.10"
dependencies = [
    "flet>=0.25.0",             # Flutter-based UI framework
    "pystray>=0.19.0",          # System tray (cross-platform)
    "Pillow>=10.0.0",           # Icon generation for tray
    "tomli-w>=1.0.0",           # TOML config writing (stdlib tomllib used for reading)
    "tomli>=2.0.0",             # TOML config reading (Python < 3.11)
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "pytest-cov>=5.0.0",
    "ruff>=0.5.0",
    "pyright>=1.1.0",
]
```

---

## 3. Project Structure

```
leadership-os/
├── main.py                          # Entry point
├── pyproject.toml                   # Project config, dependencies
├── uv.lock                          # Lockfile
├── .python-version                  # Python version pin
│
├── src/leadership_os/               # Main package
│   ├── __init__.py
│   ├── app.py                       # KivyMD App subclass, lifecycle
│   │
│   ├── core/                        # Business logic (no UI)
│   │   ├── __init__.py
│   │   ├── models.py               # Data classes (Day, Task, Session, etc.)
│   │   ├── enums.py                # TaskStatus, Priority, AppState, BreakType
│   │   ├── database.py             # SQLite operations
│   │   ├── state_manager.py        # AppState transitions, JSON state
│   │   ├── task_engine.py          # Task CRUD, lifecycle transitions
│   │   ├── timer_engine.py         # Work session tracking, elapsed time
│   │   ├── break_engine.py         # Break session management
│   │   ├── journal_engine.py       # Markdown journal generation
│   │   ├── event_bus.py            # Observer pattern for cross-module events
│   │   └── recovery.py             # Startup recovery logic
│   │
│   ├── config/                      # Configuration management
│   │   ├── __init__.py
│   │   ├── config_manager.py       # TOML config read/write/defaults
│   │   └── defaults.py             # Default configuration values
│   │
│   ├── ui/                          # Flet UI layer
│   │   ├── __init__.py
│   │   ├── theme.py                # Custom color palette, Flet theme builder
│   │   ├── screens/                # Screen placeholder
│   │   │   ├── __init__.py
│   │   ├── widgets/                # Reusable UI components (Flet)
│   │   │   ├── __init__.py
│   │   │   ├── task_card.py        # Task display card (build_task_card)
│   │   │   ├── timer_display.py    # Large timer with progress ring (build_timer_display)
│   │   │   ├── progress_bar.py     # Daily progress indicator (build_progress_bar)
│   │   │   ├── sidebar.py          # Left navigation (build_sidebar)
│   │   │   ├── execution_panel.py  # Right panel: timer, task, actions (build_execution_panel)
│   │   │   ├── status_bar.py       # Bottom status bar (build_status_bar)
│   │   │   ├── top_bar.py          # Top navigation bar (build_top_bar)
│   │   │   └── task_form.py        # Task creation/edit form (build_task_form)
│   │   └── kv/                     # KV files (obsolete after Flet migration)
│   │       ├── __init__.py
│   │
│   ├── tray/                        # System tray integration
│   │   ├── __init__.py
│   │   └── tray_manager.py         # Cross-platform tray via pystray
│   │
│   └── utils/                       # Shared utilities
│       ├── __init__.py
│       ├── time_utils.py           # Time formatting, calculations
│       ├── path_utils.py           # Cross-platform path handling
│       └── validators.py           # Input validation
│
├── tests/                           # Test suite
│   ├── __init__.py
│   ├── conftest.py                 # Shared fixtures
│   ├── unit/
│   │   ├── __init__.py
│   │   ├── test_models.py
│   │   ├── test_task_engine.py
│   │   ├── test_timer_engine.py
│   │   ├── test_break_engine.py
│   │   ├── test_journal_engine.py
│   │   ├── test_database.py
│   │   ├── test_state_manager.py
│   │   ├── test_config_manager.py
│   │   ├── test_event_bus.py
│   │   └── test_recovery.py
│   ├── integration/
│   │   ├── __init__.py
│   │   ├── test_planning_flow.py
│   │   ├── test_work_session_flow.py
│   │   ├── test_journal_generation.py
│   │   └── test_daily_workflow.py
│   └── fixtures/
│       ├── sample_tasks.json
│       └── sample_config.toml
│
├── docs/                            # Documentation (existing)
│   └── ... (existing doc files)
│
└── data/                            # Runtime data directory (development only)
    ├── leadership_os.db            # SQLite database
    ├── state.json                  # Runtime state
    ├── config.toml                 # User configuration
    └── logs/
        └── leadership_os.log       # Application logs
```

**Production data paths (XDG compliant):**
- Linux: `~/.local/share/leadership-os/`
- macOS: `~/Library/Application Support/leadership-os/`
- Windows: `%APPDATA%\leadership-os\`

The `data/` directory at project root is for **development only**. Production paths are determined at runtime based on OS.

---

## 4. Data Model

### Entity Relationship

```
Day (1)
├── Tasks (N)
│   └── Work Sessions (N)
├── Break Sessions (N)
├── Reflection (1)
└── Daily Summary (1)

Configuration (Independent)
```

### Entity: Day

```python
@dataclass
class Day:
    id: str               # UUID
    date: str             # YYYY-MM-DD
    start_time: str       # HH:MM:SS or None
    end_time: str         # HH:MM:SS or None
    status: str           # "active" | "completed" | "archived"
    created_at: str       # ISO timestamp
    updated_at: str       # ISO timestamp
```

### Entity: Task

```python
@dataclass
class Task:
    id: str               # UUID
    day_id: str           # Foreign key to Day
    title: str            # Required, non-empty, max 200 chars
    description: str      # Optional
    priority: str         # "critical" | "high" | "medium" | "low"
    status: str           # See valid statuses below
    deadline: str         # ISO timestamp or None
    estimated_minutes: int  # Optional
    actual_seconds: int   # Sum of all work sessions
    created_at: str
    activated_at: str     # First time task became active
    completed_at: str     # When completed
    display_order: int    # For manual reordering
    notes: str            # Optional
```

**Valid Status Transitions:**
```
pending → active, archived, deleted
active → paused, completed, archived, deleted
paused → active, completed, archived
completed → closed (automatic at day end)
carried_forward → active, pending, archived, deleted
```

**IMPORTANT: Break behavior.** When the app enters BREAK state, the active task's status changes to "paused" (Active → Paused transition). When the break ends, the task transitions back to "active" (Paused → Active) and a new work session is created.

**Task Ordering:** Tasks are sorted by `display_order` (ascending) as primary key, then by `priority` (Critical → High → Medium → Low) as secondary key. When the user reorders via Ctrl+Up/Down, `display_order` values are re-calculated to preserve the new order while maintaining integer gaps (e.g., 10, 20, 30) for future insertions.

### Entity: Work Session

```python
@dataclass
class WorkSession:
    id: str               # UUID
    task_id: str          # Foreign key to Task
    start_time: str       # ISO timestamp
    end_time: str         # ISO timestamp or None (if running)
    duration_seconds: int # Calculated from start/end
    created_at: str
```

### Entity: Break Session

```python
@dataclass
class BreakSession:
    id: str
    day_id: str           # Foreign key to Day
    break_type: str       # "lunch" | "dinner" | "tea" | "personal" | "meeting" | "custom"
    start_time: str
    end_time: str         # Or None if running
    duration_seconds: int
    notes: str            # Optional
```

### Entity: Reflection

```python
@dataclass
class Reflection:
    id: str
    day_id: str           # Foreign key to Day
    accomplishments: str  # What did you accomplish?
    challenges: str       # What slowed you down?
    tomorrow_first: str   # First thing tomorrow
    additional_notes: str # Optional
    created_at: str
```

### Entity: Daily Summary

```python
@dataclass
class DailySummary:
    id: str
    day_id: str
    total_planned: int
    completed: int
    carried_forward: int
    archived: int
    deleted: int
    total_focus_seconds: int
    total_break_seconds: int
    completion_percentage: float
    longest_session_seconds: int
    session_count: int
    journal_rel_path: str  # Relative to vault (e.g., "Daily Notes/2026-07-14.md")
    generated_at: str
```

**NOTE:** `journal_rel_path` is stored as a relative path. The full path is computed at read time using the current vault config. This prevents broken paths if the user changes their vault location.

### SQLite Schema

```sql
-- Schema version for migration tracking
CREATE TABLE IF NOT EXISTS schema_version (
    version INTEGER NOT NULL
);
INSERT INTO schema_version (version) VALUES (1);

CREATE TABLE IF NOT EXISTS days (
    id TEXT PRIMARY KEY,
    date TEXT NOT NULL UNIQUE,
    start_time TEXT,
    end_time TEXT,
    status TEXT NOT NULL DEFAULT 'active',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS tasks (
    id TEXT PRIMARY KEY,
    day_id TEXT NOT NULL,
    title TEXT NOT NULL,
    description TEXT DEFAULT '',
    priority TEXT NOT NULL DEFAULT 'medium',
    status TEXT NOT NULL DEFAULT 'pending',
    deadline TEXT,
    estimated_minutes INTEGER,
    actual_seconds INTEGER DEFAULT 0,
    created_at TEXT NOT NULL,
    activated_at TEXT,
    completed_at TEXT,
    display_order INTEGER DEFAULT 0,
    notes TEXT DEFAULT '',
    FOREIGN KEY (day_id) REFERENCES days(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS work_sessions (
    id TEXT PRIMARY KEY,
    task_id TEXT NOT NULL,
    start_time TEXT NOT NULL,
    end_time TEXT,
    duration_seconds INTEGER DEFAULT 0,
    created_at TEXT NOT NULL,
    FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS break_sessions (
    id TEXT PRIMARY KEY,
    day_id TEXT NOT NULL,
    break_type TEXT NOT NULL,
    start_time TEXT NOT NULL,
    end_time TEXT,
    duration_seconds INTEGER DEFAULT 0,
    notes TEXT DEFAULT '',
    FOREIGN KEY (day_id) REFERENCES days(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS reflections (
    id TEXT PRIMARY KEY,
    day_id TEXT NOT NULL UNIQUE,
    accomplishments TEXT DEFAULT '',
    challenges TEXT DEFAULT '',
    tomorrow_first TEXT DEFAULT '',
    additional_notes TEXT DEFAULT '',
    created_at TEXT NOT NULL,
    FOREIGN KEY (day_id) REFERENCES days(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS daily_summaries (
    id TEXT PRIMARY KEY,
    day_id TEXT NOT NULL UNIQUE,
    total_planned INTEGER DEFAULT 0,
    completed INTEGER DEFAULT 0,
    carried_forward INTEGER DEFAULT 0,
    archived INTEGER DEFAULT 0,
    deleted INTEGER DEFAULT 0,
    total_focus_seconds INTEGER DEFAULT 0,
    total_break_seconds INTEGER DEFAULT 0,
    completion_percentage REAL DEFAULT 0.0,
    longest_session_seconds INTEGER DEFAULT 0,
    session_count INTEGER DEFAULT 0,
    journal_rel_path TEXT DEFAULT '',  -- Relative to vault, computed full path at read time
    generated_at TEXT NOT NULL,
    FOREIGN KEY (day_id) REFERENCES days(id) ON DELETE CASCADE
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_tasks_day_id ON tasks(day_id);
CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);
CREATE INDEX IF NOT EXISTS idx_work_sessions_task_id ON work_sessions(task_id);
CREATE INDEX IF NOT EXISTS idx_break_sessions_day_id ON break_sessions(day_id);
CREATE INDEX IF NOT EXISTS idx_daily_summaries_day_id ON daily_summaries(day_id);
```

**Database Migrations:** Schema version is tracked via `schema_version` table. When schema changes in future versions, migration scripts will be added to `src/leadership_os/core/migrations/`. Each migration increments the version number and applies ALTER TABLE or other schema changes.

---

## 5. System Architecture

### Architecture Layers

```
┌──────────────────────────────────────────────────────────────┐
│                    UI Layer (Flet)                           │
│  build_* functions · Flet Controls · Flet Theme               │
├──────────────────────────────────────────────────────────────┤
│                    Application Core                          │
│  State Manager · Event Bus · Config Manager                  │
├──────────────────────────────────────────────────────────────┤
│              Engines (Business Logic)                        │
│  Task Engine · Timer Engine · Break Engine · Journal Engine  │
├──────────────────────────────────────────────────────────────┤
│                    Persistence Layer                         │
│  Database (SQLite) · State (JSON) · Config (TOML)           │
├──────────────────────────────────────────────────────────────┤
│                    Platform Layer                            │
│  System Tray (pystray) · Window Management · OS Integrations │
└──────────────────────────────────────────────────────────────┘
```

### Application States

```python
class AppState:
    STARTUP = "startup"        # App loading, recovery check
    PLANNING = "planning"      # Morning planning active
    WORKING = "working"        # Focused work on a task
    BREAK = "break"            # On a break
    IDLE = "idle"              # No active task, waiting
    REVIEW = "review"          # End-of-day review
    SHUTDOWN = "shutdown"      # Saving and exiting
```

**Valid Transitions:**
```
STARTUP → PLANNING, WORKING (if day already planned)
PLANNING → WORKING
WORKING → BREAK, IDLE, REVIEW
BREAK → WORKING
IDLE → WORKING, REVIEW
REVIEW → SHUTDOWN
SHUTDOWN → STARTUP (on next launch)
```

**Break Behavior Detail:** When the app enters BREAK state:
1. Active task status: Active → Paused
2. Current work session: closed with end time
3. Break session: created and started
4. On break end: Paused → Active, new work session created

### Event Bus

Cross-module communication via observer pattern. No direct module-to-module calls.

```python
# Events emitted:
TASK_CREATED = "task_created"
TASK_ACTIVATED = "task_activated"
TASK_COMPLETED = "task_completed"
TASK_PAUSED = "task_paused"
TIMER_STARTED = "timer_started"
TIMER_PAUSED = "timer_paused"
TIMER_STOPPED = "timer_stopped"
BREAK_STARTED = "break_started"
BREAK_ENDED = "break_ended"
DAY_STARTED = "day_started"
DAY_ENDED = "day_ended"
JOURNAL_GENERATED = "journal_generated"
CONFIG_CHANGED = "config_changed"
APP_STATE_CHANGED = "app_state_changed"
```

---

## 6. UI Layout & Design

### Workspace Layout

```
┌────────────────────────────────────────────────────────────────────┐
│                        Top Bar                                     │
│  [Logo]  Leadership OS          [Search] [Settings] [Cmd Palette]  │
├──────────────┬──────────────────────────────┬──────────────────────┤
│              │                              │                      │
│              │                              │  Execution Panel     │
│  Sidebar     │      Main Workspace          │  ───────────────     │
│              │   (changes by app state)     │  Current Task        │
│  ● Today     │                              │  ───────             │
│  ● History   │                              │  00:42:18            │
│  ● Settings  │                              │  ───────             │
│              │                              │  Progress: 4/8       │
│  ──────────  │                              │  ───────             │
│  Working     │                              │  Next: Task B        │
│  4/8 done    │                              │  ───────             │
│  Focus: 2h34m│                              │  [Pause] [Complete]  │
│              │                              │  [Start Break]       │
├──────────────┴──────────────────────────────┴──────────────────────┤
│  Status Bar: Focus 2h34m  │  Completed 4  │  [Esc] Help  │ Ready  │
└────────────────────────────────────────────────────────────────────┘
```

### Color Palette (Custom Theme)

```python
# Leadership OS Brand Colors (calm, professional, minimal)
# KivyMD accepts hex strings; rgba conversion handled in theme.py
COLORS = {
    # Primary
    "primary": "#4A6FA5",          # Calm blue — current task, active states
    "primary_light": "#6B8FC5",    # Lighter blue — hover states
    "primary_dark": "#3A5A8A",     # Darker blue — pressed states

    # Semantic
    "success": "#5B9A6B",          # Muted green — completed
    "warning": "#C4A35A",          # Warm amber — approaching deadlines
    "error": "#C45B5B",            # Soft red — overdue, errors
    "info": "#6BA3C4",             # Light blue — informational

    # Neutral
    "background": "#1A1A2E",       # Deep dark background
    "surface": "#232340",          # Card/panel surface
    "surface_light": "#2D2D50",    # Elevated surface
    "border": "#3A3A5C",           # Subtle borders

    # Text
    "text_primary": "#E8E8F0",     # Primary text — high contrast
    "text_secondary": "#9898B8",   # Secondary text — muted
    "text_muted": "#6868A0",       # Muted text — metadata

    # Priority
    "priority_critical": "#E05555",
    "priority_high": "#E0A055",
    "priority_medium": "#E0D055",
    "priority_low": "#9898B8",
}
```

### Typography

```
Application Title:  20sp, Bold
Page Title:         18sp, Bold
Section Title:      16sp, SemiBold
Card Title:         14sp, Medium
Body Text:          13sp, Regular
Secondary Text:     12sp, Regular
Metadata:           11sp, Light
Timer:              36sp, Mono/Bold
```

### Screen States

| App State | Main Workspace Shows | Execution Panel Shows | Sidebar Shows |
|-----------|---------------------|----------------------|---------------|
| **STARTUP** | Loading / Recovery dialog | Empty | Normal |
| **PLANNING** | Task list + creation form | Idle state | Today |
| **WORKING** | Task list (current highlighted) | Timer + task + progress | Working |
| **BREAK** | Task list (unchanged) | Break timer + resume | Break |
| **IDLE** | Task list | "No active task" message | Today |
| **REVIEW** | Reflection questions + summary | Minimized | Today |
| **HISTORY** | Day browser | Today's state preserved | History |
| **SETTINGS** | Settings form | Today's state preserved | Settings |

---

## 7. Feature Specifications

### 7.1 Startup & Recovery

**Behavior:**
1. App launches → load config → open database → check for interrupted state
2. **Single Instance:** Attempt to acquire file lock on `leadership_os.lock`. If lock exists and process is alive → focus existing window, exit new instance. If lock is stale (process died) → remove lock, proceed.
3. If previous day not properly closed → show recovery dialog
4. Recovery dialog asks: "Complete yesterday's review?" with options:
   - Complete yesterday's review
   - Skip (carry forward all tasks)
   - Cancel (restore state as-is)
5. If day is fresh → show morning planning
6. If day already planned → show working state

**`needs_review` Flag:** Set to `true` when the app is closed without completing the End-of-Day Review. On next startup, if `needs_review` is `true` and `last_session_date` differs from today, the recovery dialog is shown.

**Recovery Scenarios:**
- Active timer running → safely close session at last known time
- Break in progress → resume or discard based on user choice
- Review started but not completed → resume review
- App crashed during planning → restore partial plan

### 7.2 Morning Planning

**Workflow:**
1. Show welcome summary: yesterday's stats (completed, carried, focus time)
2. Show carried-forward tasks from previous days
3. For each carried task, offer: Continue Today / Reschedule / Archive / Delete
4. Create new tasks (minimal input: title required, everything else optional)
5. Reorder tasks by priority (Critical → High → Medium → Low)
6. Optionally assign deadlines (relative or absolute)
7. Press "Begin Work" or keyboard shortcut to start focus mode

**Task Creation Form:**
- Title (required, keyboard-focused immediately)
- Priority dropdown (default: Medium)
- Deadline picker (optional)
- Estimated duration (optional, minutes)
- Notes (optional, expandable)
- Create button (Enter key)

### 7.3 Task Management

**CRUD Operations:**
- **Create:** Morning planning or quick-add
- **Read:** Task cards in main workspace
- **Update:** Edit title, priority, deadline, notes
- **Delete:** With confirmation dialog
- **Complete:** Move to completed, auto-select next task
- **Archive:** Remove from active list, keep in history
- **Carry Forward:** Move to next day's planning

**Display Order:** Tasks sorted by `display_order` (ascending) as primary key, then by `priority` (Critical → High → Medium → Low) as secondary key. When user reorders via Ctrl+Up/Down, `display_order` values are re-calculated with integer gaps (e.g., 10, 20, 30) for future insertions.

### 7.4 Focus Timer

**Behavior:**
- Timer starts when task becomes Active
- Timer pauses when break begins or task changes
- Timer resumes when returning from break
- Timer stops when task completes

**Display:**
- Large digital display: `HH:MM:SS`
- Progress ring around timer (if estimated duration set)
- Session count indicator
- Total focus time for the day

**Accuracy:**
- Elapsed = current_time - session_start_time (NOT counter-based)
- Survives sleep/hibernate
- Recovers after crash

### 7.5 Break Management

**Supported Types:**
- Lunch (configurable time)
- Dinner (configurable time)
- Tea
- Personal
- Custom

**Behavior:**
- Starting a break: pauses active task timer (Active → Paused), creates break session
- Break display shows: break type, elapsed time, resume button
- Ending break: resumes previous task (Paused → Active), creates new work session

### 7.6 End-of-Day Review

**Workflow:**
1. User triggers review (or reminder triggers at configured time)
2. Show daily summary: tasks planned, completed, focus time, break time
3. Present 3 reflection questions:
   - "What did you accomplish today?" (textarea)
   - "What slowed you down?" (textarea)
   - "What should you do first tomorrow?" (textarea)
4. Show carry-forward tasks with action options
5. Generate and save Markdown journal
6. Archive the day
7. Set `needs_review` = false
8. Prepare for next startup

### 7.7 Markdown Journal Generation

**Structure:**
```markdown
# DayName, Month DD, YYYY

**Started:** HH:MM
**Finished:** HH:MM

## Summary

- Planned Tasks: N
- Completed: N (XX%)
- Carried Forward: N
- Focus Time: Xh Ym
- Break Time: Xh Ym

## Completed

- [x] **Task Title** (Xm)
  > Notes if any

## Incomplete

- [ ] **Task Title** — Priority

## Timeline

- 09:00 — Started **Task A**
- 10:15 — Lunch break
- 11:00 — Resumed **Task A**
- 12:30 — Completed **Task A**

---

## Reflection

### What I accomplished
[User's answer]

### What slowed me down
[User's answer]

### First thing tomorrow
[User's answer]

---

## Carry Forward

N task(s) will be carried to tomorrow:
- [ ] **Task Title** (Priority)
```

**Storage:** `~/Documents/Obsidian/Daily Notes/YYYY-MM-DD.md` (configurable path in settings)

**Journal path in DailySummary:** Stored as relative path (`Daily Notes/2026-07-14.md`). Full path is computed at read time using the current vault config. This prevents broken paths if the user changes their vault location.

---

## 8. Keyboard Shortcuts

### Global Shortcuts (In-App)

| Shortcut | Action | Context |
|----------|--------|---------|
| `Ctrl+N` | Create new task | Planning |
| `Ctrl+Enter` | Complete current task | Working |
| `Ctrl+Space` | Start/Pause task | Working/Idle |
| `Ctrl+B` | Start break | Working |
| `Ctrl+Shift+B` | End break | Break |
| `Ctrl+E` | End of day review | Any |
| `Ctrl+S` | Save (export journal) | Review |
| `Ctrl+,` | Open settings | Any |
| `Ctrl+K` | Command palette | Any |
| `Ctrl+Z` | Undo last action | Any |
| `Escape` | Close dialog / Cancel | Any |
| `Tab` | Next field | Forms |
| `Shift+Tab` | Previous field | Forms |
| `Ctrl+↑` | Move task up | Planning |
| `Ctrl+↓` | Move task down | Planning |
| `Delete` | Delete task (with confirm) | Planning |
| `Arrow Keys` | Navigate tasks | Any |

---

## 9. System Tray & Overlay

### System Tray (pystray)

Uses `pystray` for cross-platform tray icon with `Pillow` for icon generation.

**Tray Menu:**
```
Leadership OS
─────────────────
📋 Current: Implement Overlay
⏱  Focus: 2h 34m
📅 Tasks: 4/8 complete
─────────────────
▶ Pause Task
✓ Complete Task
☕ Start Break
─────────────────
📝 Open App
⚙  Settings
❌ Quit
```

### Floating Overlay Window

**Size:** ~320×180px, semi-transparent (configurable opacity)  
**Always on top:** Yes (platform-specific code via pystray + Kivy window hints)  
**Position:** Configurable, default: top-right corner  
**Content:** Standard — current task title + elapsed time + next task

**Content:**
```
┌─────────────────────────────────┐
│  ● Working    High Priority     │
│                                 │
│  Implement Overlay              │
│                                 │
│  ⏱  00:42:18                   │
│                                 │
│  Next: Notifications            │
└─────────────────────────────────┘
```

**Interactions:**
- Click to show/hide main window
- Right-click for context menu (pause, complete, break)
- Draggable to reposition
- Remembers position across restarts

---

## 10. Configuration System

### Config File: `config.toml`

```toml
[work_schedule]
start_time = "09:00"
end_time = "18:00"
lunch_time = "13:00"
dinner_time = "19:00"
work_days = ["monday", "tuesday", "wednesday", "thursday", "friday"]

[ui]
theme = "dark"                    # "dark" | "light"
overlay_opacity = 0.85           # 0.0 - 1.0
overlay_position_x = -1          # -1 = right edge
overlay_position_y = 40          # pixels from top
show_overlay = true

[journaling]
vault_path = "~/Documents/Obsidian"
journal_dir = "Daily Notes"
filename_format = "YYYY-MM-DD.md"

[notifications]
# NOTE: Notification engine is deferred to future version.
# These config options are placeholders for future use.
enabled = true
deadline_reminder_minutes = 30
break_reminder = false
end_of_day_time = "17:30"
do_not_disturb_start = ""
do_not_disturb_end = ""

[keyboard]
create_task = "ctrl+n"
complete_task = "ctrl+enter"
pause_task = "ctrl+space"
start_break = "ctrl+b"
end_break = "ctrl+shift+b"
end_day = "ctrl+e"
settings = "ctrl+,"
command_palette = "ctrl+k"

[startup]
launch_at_system_startup = false
restore_previous_session = true
minimize_to_tray = true
open_overlay_on_start = true
```

### State File: `state.json`

```json
{
  "app_state": "working",
  "current_day_id": "uuid-here",
  "active_task_id": "uuid-here",
  "active_break_id": null,
  "timer_start": "2026-07-14T09:15:00",
  "window_position": [100, 100],
  "window_size": [1200, 800],
  "overlay_position": [1800, 40],
  "last_session_date": "2026-07-14",
  "needs_review": false
}
```

**`needs_review` flag behavior:**
- Set to `true` when app closes without completing End-of-Day Review
- Cleared to `false` when review is completed or skipped
- On startup: if `true` AND `last_session_date` ≠ today → show recovery dialog
- Prevents losing incomplete work from previous day

---

## 11. Error Handling & Recovery

### Error Hierarchy

```
LeadershipOSError (base)
├── DatabaseError
│   ├── ConnectionError
│   ├── QueryError
│   └── IntegrityError
├── ConfigError
│   ├── FileNotFoundError
│   ├── ParseError
│   └── ValidationError
├── FileError
│   ├── PermissionDenied
│   ├── DiskFull
│   └── PathNotFound
├── TimerError
│   ├── SessionCorrupted
│   └── ClockDrift
└── JournalError
    ├── WriteFailed
    └── TemplateError
```

### Recovery Strategy

1. **Never crash during normal operation** — catch all exceptions
2. **Recover automatically** when possible (missing config → create defaults)
3. **Inform user** only when action is required
4. **Preserve data** above all else — save temporary copies before risky operations
5. **Log everything** to `data/logs/leadership_os.log`

### Single Instance Handling

- On startup, attempt to acquire a file lock on `leadership_os.lock`
- If lock exists and process is alive → focus existing window, exit new instance
- If lock is stale (process died) → remove lock, proceed with normal startup

### Startup Recovery Checklist

```python
def recover():
    # 1. Check database integrity
    # 2. Check for active timers from last session
    # 3. Check for incomplete reviews (needs_review flag)
    # 4. Validate state.json consistency with database
    # 5. Recover or discard orphaned sessions
    # 6. Log recovery actions
```

---

## 12. Testing Strategy

### Test Priority Order

1. **Data Integrity** — Never lose user data
2. **Business Logic** — Task lifecycle, timer calculations, state transitions
3. **Recovery** — Crash recovery, interrupted sessions
4. **Database Operations** — CRUD, queries, migrations
5. **Journal Generation** — Markdown output correctness
6. **State Management** — App state transitions
7. **Configuration** — Default values, validation, persistence
8. **UI Behavior** — Navigation, keyboard shortcuts, rendering

### Test Categories

```
tests/
├── unit/                    # ~70% of tests
│   ├── test_models.py       # Data class validation, serialization
│   ├── test_task_engine.py  # Task CRUD, transitions, validation
│   ├── test_timer_engine.py # Session tracking, elapsed calculation
│   ├── test_break_engine.py # Break start/end, pause/resume
│   ├── test_journal_engine.py # Markdown generation
│   ├── test_database.py     # SQLite operations
│   ├── test_state_manager.py # State transitions
│   ├── test_config_manager.py # Config read/write/defaults
│   ├── test_event_bus.py    # Event publish/subscribe
│   └── test_recovery.py     # Recovery scenarios
├── integration/             # ~20% of tests
│   ├── test_planning_flow.py    # Morning planning end-to-end
│   ├── test_work_session_flow.py # Task → work → complete
│   ├── test_journal_generation.py # Full journal creation
│   └── test_daily_workflow.py   # Complete day lifecycle
└── fixtures/                # ~10% — shared test data
    ├── sample_tasks.json
    └── sample_config.toml
```

### Running Tests

```bash
# Unit tests
uv run pytest tests/unit/ -v

# Integration tests
uv run pytest tests/integration/ -v

# All tests with coverage
uv run pytest tests/ --cov=src/leadership_os --cov-report=html

# Property-based tests
uv run pytest tests/ --hypothesis-seed=0

# Linting
uv run ruff check src/ tests/

# Type checking
uv run pyright src/
```

### Key Test Cases

```python
# Task Engine
def test_create_task_validates_title_not_empty()
def test_create_task_validates_title_max_length()
def test_task_transitions_pending_to_active()
def test_only_one_active_task_allowed()
def test_complete_task_records_timestamp()
def test_archive_removes_from_planning()
def test_carry_forward_moves_to_next_day()
def test_display_order_recalculated_on_reorder()

# Timer Engine
def test_timer_starts_on_task_activation()
def test_elapsed_uses_absolute_timestamps()
def test_pause_preserves_accumulated_time()
def test_resume_creates_new_session()
def test_total_duration_sums_all_sessions()
def test_timer_survives_clock_drift()

# Break Engine
def test_start_break_pauses_active_task()
def test_end_break_resumes_task()
def test_break_session_records_duration()
def test_can_change_break_type()

# Journal Engine
def test_journal_includes_completed_tasks()
def test_journal_includes_carry_forward()
def test_journal_handles_empty_day()
def test_journal_markdown_is_valid()
def test_journal_path_is_relative()

# State Manager
def test_valid_transitions_only()
def test_invalid_transition_raises_error()
def test_needs_review_flag_on_incomplete_close()

# Recovery
def test_recovery_closes_orphaned_sessions()
def test_recovery_detects_stale_lock()
def test_recovery_preserves_incomplete_planning()
```

---

## 13. Implementation Phases

### Phase 1: Foundation (Week 1)
**Goal:** Project scaffolding, data layer, basic app shell

- [ ] 1.1 Initialize project with `uv init`
- [ ] 1.2 Set up `pyproject.toml` with all dependencies
- [ ] 1.3 Create package structure (`src/leadership_os/`)
- [ ] 1.4 Implement `core/enums.py` — all status/priority/app state enums
- [ ] 1.5 Implement `core/models.py` — all data classes with validation
- [ ] 1.6 Implement `core/database.py` — SQLite schema creation and CRUD
- [ ] 1.7 Implement `config/config_manager.py` — TOML config read/write/defaults
- [ ] 1.8 Implement `core/state_manager.py` — JSON state persistence
- [ ] 1.9 Implement `core/event_bus.py` — observer pattern
- [ ] 1.10 Implement `utils/time_utils.py`, `path_utils.py`, `validators.py`
- [ ] 1.11 Write unit tests for all core modules
- [ ] 1.12 Create `main.py` entry point (empty app)
- [ ] 1.13 **Validation:** `uv run pytest tests/unit/ -v` passes
- [ ] 1.14 **Review:** Code review of data layer

### Phase 2: Application Core (Week 2)
**Goal:** Business logic engines

- [ ] 2.1 Implement `core/task_engine.py` — full task lifecycle
- [ ] 2.2 Implement `core/timer_engine.py` — work session tracking
- [ ] 2.3 Implement `core/break_engine.py` — break management
- [ ] 2.4 Implement `core/recovery.py` — startup recovery logic
- [ ] 2.5 Write unit tests for all engines
- [ ] 2.6 Write integration tests for task → timer → session flow
- [ ] 2.7 **Validation:** `uv run pytest tests/unit/ tests/integration/ -v`
- [ ] 2.8 **Review:** Business logic review

### Phase 3: UI Foundation (Week 3)
**Goal:** KivyMD app shell, theme, layout structure

- [ ] 3.1 Implement `ui/theme.py` — custom color palette
- [ ] 3.2 Create `ui/kv/main.kv` — main layout (sidebar, workspace, execution panel, status bar)
- [ ] 3.3 Implement `ui/widgets/sidebar.py` — navigation sidebar
- [ ] 3.4 Implement `ui/widgets/execution_panel.py` — right panel
- [ ] 3.5 Implement `ui/widgets/status_bar.py` — bottom bar
- [ ] 3.6 Implement `ui/widgets/task_card.py` — task display
- [ ] 3.7 Implement `ui/widgets/timer_display.py` — large timer
- [ ] 3.8 Implement `ui/widgets/progress_bar.py` — daily progress
- [ ] 3.9 Implement `ui/widgets/task_form.py` — task creation form
- [ ] 3.10 Wire up app.py with KivyMD App class
- [ ] 3.11 **Validation:** App launches, layout renders correctly
- [ ] 3.12 **Review:** UI architecture review

### Phase 4: Morning Planning (Week 4)
**Goal:** Complete planning workflow

- [ ] 4.1 Implement `ui/screens/planning_screen.py`
- [ ] 4.2 Create `ui/kv/planning_screen.kv`
- [ ] 4.3 Implement task list with keyboard reorder (Ctrl+Up/Down)
- [ ] 4.4 Implement carry-forward dialog from previous days
- [ ] 4.5 Implement task creation form with validation
- [ ] 4.6 Implement priority selection (Critical/High/Medium/Low)
- [ ] 4.7 Implement deadline picker (relative + absolute)
- [ ] 4.8 Implement "Begin Work" transition to working state
- [ ] 4.9 Integrate with TaskEngine
- [ ] 4.10 Write integration tests for planning flow
- [ ] 4.11 **Validation:** Full planning workflow works
- [ ] 4.12 **Review:** Planning UX review

### Phase 5: Focused Work (Week 5)
**Goal:** Working state, timer, task switching

- [ ] 5.1 Implement `ui/screens/working_screen.py`
- [ ] 5.2 Create `ui/kv/working_screen.kv`
- [ ] 5.3 Implement task highlighting (current vs. next)
- [ ] 5.4 Wire timer display to TimerEngine
- [ ] 5.5 Implement task switching (keyboard + click)
- [ ] 5.6 Implement task completion flow
- [ ] 5.7 Implement idle state (no active task)
- [ ] 5.8 Implement keyboard shortcuts for working state
- [ ] 5.9 Integrate with EventBus for real-time updates
- [ ] 5.10 Write integration tests for work session flow
- [ ] 5.11 **Validation:** Full work session lifecycle works
- [ ] 5.12 **Review:** Timer accuracy review

### Phase 6: Break Management (Week 5)
**Goal:** Break start/end, timer pause/resume

- [ ] 6.1 Implement `ui/screens/break_screen.py`
- [ ] 6.2 Create `ui/kv/break_screen.kv`
- [ ] 6.3 Implement break type selection dialog
- [ ] 6.4 Implement break timer display
- [ ] 6.5 Implement resume/end break flow
- [ ] 6.6 Integrate with BreakEngine
- [ ] 6.7 Test pause → resume → complete flow
- [ ] 6.8 **Validation:** Break management works correctly
- [ ] 6.9 **Review:** Break UX review

### Phase 7: End-of-Day Review (Week 6)
**Goal:** Review workflow, journal generation

- [ ] 7.1 Implement `ui/screens/review_screen.py`
- [ ] 7.2 Create `ui/kv/review_screen.kv`
- [ ] 7.3 Implement 3 reflection question forms
- [ ] 7.4 Implement carry-forward task review
- [ ] 7.5 Implement daily summary display
- [ ] 7.6 Implement `core/journal_engine.py` — Markdown generation
- [ ] 7.7 Create journal template
- [ ] 7.8 Implement journal file writing (Obsidian path)
- [ ] 7.9 Implement day archival
- [ ] 7.10 Write integration tests for journal generation
- [ ] 7.11 **Validation:** Full end-of-day workflow works
- [ ] 7.12 **Review:** Journal format review

### Phase 8: System Tray & Overlay (Week 7)
**Goal:** System tray, floating overlay window

- [ ] 8.1 Implement `tray/tray_manager.py` — cross-platform abstraction via pystray
- [ ] 8.2 Implement tray icon with menu (current task, timer, quick actions)
- [ ] 8.3 Implement `ui/widgets/overlay_widget.py` — floating window content
- [ ] 8.4 Create `ui/kv/overlay_widget.kv`
- [ ] 8.5 Implement always-on-top window (platform-specific hints)
- [ ] 8.6 Implement overlay drag-to-reposition
- [ ] 8.7 Implement tray → app communication
- [ ] 8.8 Test on Linux, macOS, Windows
- [ ] 8.9 **Validation:** Tray and overlay work on all platforms
- [ ] 8.10 **Review:** Tray integration review

### Phase 9: Search & History (Week 8)
**Goal:** Day history browser, basic search

- [ ] 9.1 Implement `ui/screens/history_screen.py`
- [ ] 9.2 Create `ui/kv/history_screen.kv`
- [ ] 9.3 Implement day list with summary preview
- [ ] 9.4 Implement day detail view (tasks, sessions, journal)
- [ ] 9.5 Implement basic text search across tasks and journals
- [ ] 9.6 Implement date range filtering
- [ ] 9.7 Implement journal preview in history view
- [ ] 9.8 Write tests for search functionality
- [ ] 9.9 **Validation:** History browsing and search work
- [ ] 9.10 **Review:** Search accuracy review

### Phase 9: Settings & Configuration (Week 8)
**Goal:** Settings screen, all configuration options

- [ ] 9.11 Implement `ui/screens/settings_screen.py`
- [ ] 9.12 Create `ui/kv/settings_screen.kv`
- [ ] 9.13 Implement work schedule settings
- [ ] 9.14 Implement UI settings (theme toggle, overlay)
- [ ] 9.15 Implement journal path settings
- [ ] 9.16 Implement notification settings (placeholder)
- [ ] 9.17 Implement keyboard shortcut customization
- [ ] 9.18 Implement startup behavior settings
- [ ] 9.19 Implement config export/import/reset
- [ ] 9.20 Validate all config values before saving
- [ ] 9.21 **Validation:** Settings persist and take effect
- [ ] 9.22 **Review:** Settings UX review

### Phase 10: Polish & Edge Cases (Week 9)
**Goal:** Visual polish, error handling, edge cases

- [ ] 10.1 Implement all error dialogs (user-friendly messages)
- [ ] 10.2 Implement empty states (no tasks, no history, etc.)
- [ ] 10.3 Implement loading states
- [ ] 10.4 Implement animations (state transitions, notifications)
- [ ] 10.5 Test keyboard-only workflow end-to-end
- [ ] 10.6 Test with large datasets (10 years of journals)
- [ ] 10.7 Test crash recovery scenarios
- [ ] 10.8 Test sleep/wake behavior
- [ ] 10.9 Test on all three platforms
- [ ] 10.10 Fix visual inconsistencies
- [ ] 10.11 **Validation:** Full workflow works flawlessly
- [ ] 10.12 **Review:** Final UX review

### Phase 11: Testing & Release (Week 10)
**Goal:** Comprehensive testing, packaging, documentation

- [ ] 11.1 Run full test suite with coverage
- [ ] 11.2 Achieve >80% coverage on core modules
- [ ] 11.3 Run ruff linter — zero warnings
- [ ] 11.4 Run pyright type checker — zero errors
- [ ] 11.5 Performance testing (startup time, search latency)
- [ ] 11.6 Write user documentation
- [ ] 11.7 Write developer documentation
- [ ] 11.8 Create build scripts using `briefcase` (cross-platform packaging)
- [ ] 11.9 Create release package (`.deb` for Linux, `.dmg` for macOS, `.exe` for Windows)
- [ ] 11.10 **Final Validation:** Complete daily workflow test
- [ ] 11.11 **Final Review:** Code freeze review
- [ ] 11.12 **Release:** v1.0.0

---

## 14. Coding Standards

### General Rules

1. **Readability over cleverness** — clear code, not short code
2. **Small functions** — one responsibility per function
3. **Early returns** — avoid deep nesting
4. **No duplication** — extract common logic into shared modules
5. **Type hints everywhere** — `pyright` strict mode

### Naming

```python
# Functions: snake_case, verb first
def create_task(...)
def get_active_session(...)
def calculate_elapsed(...)

# Classes: PascalCase
class TaskEngine
class TimerDisplay
class DatabaseManager

# Constants: UPPER_SNAKE_CASE
MAX_TASK_TITLE_LENGTH = 200
DEFAULT_PRIORITY = "medium"
APP_STATE_KEY = "app_state"

# Enums: descriptive values
class TaskStatus:
    PENDING = "pending"
    ACTIVE = "active"
    COMPLETED = "completed"
```

### Error Handling

```python
# Never silently ignore errors
# Always use Result pattern or raise specific exceptions
def create_task(self, title: str) -> Task:
    if not title.strip():
        raise ValidationError("Task title cannot be empty")
    # ...

# Use context managers for resources
with DatabaseManager() as db:
    task = db.get_task(task_id)
```

### Logging

```python
import logging

logger = logging.getLogger("leadership_os")

# Log meaningful events
logger.info("Task '%s' completed in %d seconds", task.title, duration)
logger.warning("Database recovery needed for session %s", session_id)
logger.error("Failed to generate journal: %s", error)
```

### File Headers

```python
"""Task Engine — manages the lifecycle of tasks.

Responsibilities:
- Create, update, delete tasks
- Validate state transitions
- Maintain task ordering
- Handle carry-forward logic
"""
```

---

## Appendix A: MVP Feature Scope

Per user decision, the minimum viable product includes:

| Feature | Included | Priority |
|---------|----------|----------|
| Task creation | ✅ | P0 |
| Focus timer | ✅ | P0 |
| System tray | ✅ | P0 |
| Journal generation | ✅ | P0 |
| Data persistence | ✅ | P0 |
| Configuration | ✅ | P0 |
| Recovery | ✅ | P0 |
| End-of-day review | ✅ | P0 |
| Keyboard shortcuts | ✅ | P0 |
| Break management | ✅ | P0 |
| Search & history | ❌ | P1 (Phase 9) |
| Command palette | ❌ | P1 (future) |
| Notification engine | ❌ | P1 (config placeholders only) |

---

## Appendix B: Platform-Specific Considerations

| Feature | Linux | macOS | Windows |
|---------|-------|-------|---------|
| System tray | pystray (AppIndicator) | pystray (NSStatusBar) | pystray (Win32) |
| Always-on-top | GTK window type hint | NSWindow level | HWND_TOPMOST |
| File paths | `~/.local/share/leadership-os/` | `~/Library/Application Support/leadership-os/` | `%APPDATA%\leadership-os\` |
| Obsidian vault | `~/Documents/Obsidian/` | `~/Documents/Obsidian/` | `C:\Users\<user>\Documents\Obsidian\` |
| Process lock | `fcntl.flock()` | `fcntl.flock()` | `msvcrt.locking()` |

---

## Appendix C: Database Migration Strategy

When the schema changes between versions:

1. Read current version from `schema_version` table
2. Apply migration scripts sequentially (v1 → v2 → v3...)
3. Migration scripts live in `src/leadership_os/core/migrations/`
4. Each migration is idempotent (safe to run multiple times)
5. Backup database before applying migrations
6. Example migration naming: `migrate_v1_to_v2.py`

---

*This specification is a living document. It will be updated as implementation progresses and decisions are refined.*
