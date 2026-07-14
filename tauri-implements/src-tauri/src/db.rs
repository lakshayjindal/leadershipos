use rusqlite::{Connection, Result, params};
use std::path::PathBuf;
use std::sync::Mutex;

use crate::models::*;

pub struct Database {
    conn: Mutex<Connection>,
}

impl Database {
    pub fn new(app_data_dir: PathBuf) -> Result<Self> {
        std::fs::create_dir_all(&app_data_dir).ok();
        let db_path = app_data_dir.join("leadership-os.db");
        let conn = Connection::open(&db_path)?;
        conn.execute_batch("PRAGMA journal_mode=WAL; PRAGMA foreign_keys=ON;")?;
        let db = Database { conn: Mutex::new(conn) };
        db.initialize_schema()?;
        Ok(db)
    }

    fn initialize_schema(&self) -> Result<()> {
        let conn = self.conn.lock().unwrap();
        conn.execute_batch(
            "
            CREATE TABLE IF NOT EXISTS days (
                id TEXT PRIMARY KEY,
                date TEXT NOT NULL UNIQUE,
                start_time TEXT,
                end_time TEXT,
                status TEXT NOT NULL DEFAULT 'pending',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS tasks (
                id TEXT PRIMARY KEY,
                day_id TEXT NOT NULL,
                title TEXT NOT NULL,
                description TEXT,
                priority TEXT NOT NULL DEFAULT 'medium',
                status TEXT NOT NULL DEFAULT 'pending',
                deadline TEXT,
                estimated_duration_minutes INTEGER,
                actual_duration_seconds INTEGER NOT NULL DEFAULT 0,
                display_order INTEGER NOT NULL DEFAULT 0,
                notes TEXT,
                created_at TEXT NOT NULL,
                activated_at TEXT,
                completed_at TEXT,
                carry_forward_count INTEGER NOT NULL DEFAULT 0,
                FOREIGN KEY (day_id) REFERENCES days(id)
            );

            CREATE TABLE IF NOT EXISTS work_sessions (
                id TEXT PRIMARY KEY,
                task_id TEXT NOT NULL,
                start_time TEXT NOT NULL,
                end_time TEXT,
                duration_seconds INTEGER NOT NULL DEFAULT 0,
                paused_duration_seconds INTEGER NOT NULL DEFAULT 0,
                FOREIGN KEY (task_id) REFERENCES tasks(id)
            );

            CREATE TABLE IF NOT EXISTS break_sessions (
                id TEXT PRIMARY KEY,
                day_id TEXT NOT NULL,
                break_type TEXT NOT NULL,
                start_time TEXT NOT NULL,
                end_time TEXT,
                duration_seconds INTEGER NOT NULL DEFAULT 0,
                notes TEXT,
                FOREIGN KEY (day_id) REFERENCES days(id)
            );

            CREATE TABLE IF NOT EXISTS reflections (
                id TEXT PRIMARY KEY,
                day_id TEXT NOT NULL UNIQUE,
                accomplishments TEXT,
                challenges TEXT,
                tomorrow_first_task TEXT,
                additional_notes TEXT,
                completed_at TEXT,
                FOREIGN KEY (day_id) REFERENCES days(id)
            );

            CREATE TABLE IF NOT EXISTS daily_summaries (
                id TEXT PRIMARY KEY,
                day_id TEXT NOT NULL UNIQUE,
                total_planned INTEGER NOT NULL DEFAULT 0,
                completed INTEGER NOT NULL DEFAULT 0,
                carried_forward INTEGER NOT NULL DEFAULT 0,
                archived INTEGER NOT NULL DEFAULT 0,
                deleted_count INTEGER NOT NULL DEFAULT 0,
                total_focus_seconds INTEGER NOT NULL DEFAULT 0,
                total_break_seconds INTEGER NOT NULL DEFAULT 0,
                completion_percentage REAL NOT NULL DEFAULT 0.0,
                longest_session_seconds INTEGER NOT NULL DEFAULT 0,
                session_count INTEGER NOT NULL DEFAULT 0,
                generated_markdown_path TEXT,
                archived_at TEXT,
                FOREIGN KEY (day_id) REFERENCES days(id)
            );

            CREATE TABLE IF NOT EXISTS configurations (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS app_state (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                current_state TEXT NOT NULL DEFAULT 'idle',
                active_task_id TEXT,
                current_day_id TEXT,
                updated_at TEXT NOT NULL
            );

            INSERT OR IGNORE INTO app_state (id, current_state, updated_at)
            VALUES (1, 'idle', datetime('now'));

            -- ─── FTS5 Search Index ────────────────────────────────
            CREATE VIRTUAL TABLE IF NOT EXISTS tasks_fts USING fts5(
                title, description, notes,
                content='tasks',
                content_rowid='rowid',
                tokenize='porter unicode61'
            );

            -- Triggers to keep FTS index in sync
            CREATE TRIGGER IF NOT EXISTS tasks_ai AFTER INSERT ON tasks BEGIN
                INSERT INTO tasks_fts(rowid, title, description, notes)
                VALUES (new.rowid, new.title, new.description, new.notes);
            END;

            CREATE TRIGGER IF NOT EXISTS tasks_ad AFTER DELETE ON tasks BEGIN
                INSERT INTO tasks_fts(tasks_fts, rowid, title, description, notes)
                VALUES ('delete', old.rowid, old.title, old.description, old.notes);
            END;

            CREATE TRIGGER IF NOT EXISTS tasks_au AFTER UPDATE ON tasks BEGIN
                INSERT INTO tasks_fts(tasks_fts, rowid, title, description, notes)
                VALUES ('delete', old.rowid, old.title, old.description, old.notes);
                INSERT INTO tasks_fts(rowid, title, description, notes)
                VALUES (new.rowid, new.title, new.description, new.notes);
            END;
            "
        )?;

        // Rebuild FTS index if it's empty (for existing data)
        let count: i32 = conn
            .query_row("SELECT COALESCE(COUNT(*), 0) FROM tasks_fts", [], |row| row.get(0))
            .unwrap_or(0);
        if count == 0 {
            conn.execute("INSERT INTO tasks_fts(tasks_fts) VALUES('rebuild')", []).ok();
        }

        Ok(())
    }

    // ─── Day Operations ─────────────────────────────────────────────

    pub fn get_or_create_today(&self) -> Result<Day> {
        let conn = self.conn.lock().unwrap();
        let today = chrono::Local::now().format("%Y-%m-%d").to_string();

        let existing = conn.query_row(
            "SELECT id, date, start_time, end_time, status, created_at, updated_at FROM days WHERE date = ?1",
            params![today],
            |row| {
                Ok(Day {
                    id: row.get(0)?,
                    date: row.get(1)?,
                    start_time: row.get(2)?,
                    end_time: row.get(3)?,
                    status: row.get(4)?,
                    created_at: row.get(5)?,
                    updated_at: row.get(6)?,
                })
            },
        );

        match existing {
            Ok(day) => Ok(day),
            Err(_) => {
                let id = uuid::Uuid::new_v4().to_string();
                let now = chrono::Local::now().format("%Y-%m-%d %H:%M:%S").to_string();
                conn.execute(
                    "INSERT INTO days (id, date, status, created_at, updated_at) VALUES (?1, ?2, 'pending', ?3, ?4)",
                    params![id, today, now, now],
                )?;
                Ok(Day {
                    id,
                    date: today,
                    start_time: None,
                    end_time: None,
                    status: "pending".to_string(),
                    created_at: now.clone(),
                    updated_at: now,
                })
            }
        }
    }

    // ─── Task Operations ────────────────────────────────────────────

    pub fn create_task(&self, day_id: &str, req: &CreateTaskRequest) -> Result<Task> {
        tracing::debug!("Creating task: {}", req.title);
        let conn = self.conn.lock().unwrap();
        let id = uuid::Uuid::new_v4().to_string();
        let now = chrono::Local::now().format("%Y-%m-%d %H:%M:%S").to_string();

        let max_order: i32 = conn.query_row(
            "SELECT COALESCE(MAX(display_order), -1) + 1 FROM tasks WHERE day_id = ?1",
            params![day_id],
            |row| row.get(0),
        )?;

        conn.execute(
            "INSERT INTO tasks (id, day_id, title, description, priority, status, deadline, estimated_duration_minutes, display_order, notes, created_at)
             VALUES (?1, ?2, ?3, ?4, ?5, 'pending', ?6, ?7, ?8, ?9, ?10)",
            params![
                id,
                day_id,
                req.title,
                req.description,
                req.priority,
                req.deadline,
                req.estimated_duration_minutes,
                max_order,
                req.notes,
                now,
            ],
        )?;

        tracing::info!("Task created: {} (id: {})", req.title, id);
        Ok(Task {
            id,
            day_id: day_id.to_string(),
            title: req.title.clone(),
            description: req.description.clone(),
            priority: Priority::from_str(&req.priority),
            status: TaskStatus::Pending,
            deadline: req.deadline.clone(),
            estimated_duration_minutes: req.estimated_duration_minutes,
            actual_duration_seconds: 0,
            display_order: max_order,
            notes: req.notes.clone(),
            created_at: now,
            activated_at: None,
            completed_at: None,
            carry_forward_count: 0,
        })
    }

    pub fn get_tasks_by_day(&self, day_id: &str) -> Result<Vec<Task>> {
        let conn = self.conn.lock().unwrap();
        let mut stmt = conn.prepare(
            "SELECT id, day_id, title, description, priority, status, deadline, estimated_duration_minutes,
                    actual_duration_seconds, display_order, notes, created_at, activated_at, completed_at, carry_forward_count
             FROM tasks WHERE day_id = ?1 AND status != 'deleted'
             ORDER BY display_order ASC"
        )?;

        let tasks = stmt.query_map(params![day_id], |row| {
            Ok(Task {
                id: row.get(0)?,
                day_id: row.get(1)?,
                title: row.get(2)?,
                description: row.get(3)?,
                priority: Priority::from_str(&row.get::<_, String>(4)?),
                status: TaskStatus::from_str(&row.get::<_, String>(5)?),
                deadline: row.get(6)?,
                estimated_duration_minutes: row.get(7)?,
                actual_duration_seconds: row.get(8)?,
                display_order: row.get(9)?,
                notes: row.get(10)?,
                created_at: row.get(11)?,
                activated_at: row.get(12)?,
                completed_at: row.get(13)?,
                carry_forward_count: row.get(14)?,
            })
        })?.collect::<Result<Vec<_>>>()?;

        Ok(tasks)
    }

    pub fn update_task(&self, req: &UpdateTaskRequest) -> Result<()> {
        tracing::debug!("Updating task: {}", req.id);
        let conn = self.conn.lock().unwrap();

        if let Some(title) = &req.title {
            conn.execute("UPDATE tasks SET title = ?1 WHERE id = ?2",
                params![title, req.id])?;
        }
        if let Some(description) = &req.description {
            conn.execute("UPDATE tasks SET description = ?1 WHERE id = ?2",
                params![description, req.id])?;
        }
        if let Some(priority) = &req.priority {
            conn.execute("UPDATE tasks SET priority = ?1 WHERE id = ?2",
                params![priority, req.id])?;
        }
        if let Some(deadline) = &req.deadline {
            conn.execute("UPDATE tasks SET deadline = ?1 WHERE id = ?2",
                params![deadline, req.id])?;
        }
        if let Some(notes) = &req.notes {
            conn.execute("UPDATE tasks SET notes = ?1 WHERE id = ?2",
                params![notes, req.id])?;
        }
        if let Some(order) = req.display_order {
            conn.execute("UPDATE tasks SET display_order = ?1 WHERE id = ?2",
                params![order, req.id])?;
        }
        Ok(())
    }

    pub fn set_task_status(&self, task_id: &str, status: &str) -> Result<()> {
        tracing::debug!("Setting task {} status to {}", task_id, status);
        let conn = self.conn.lock().unwrap();

        // ─── State machine validation ────────────────────────────
        let current_status: String = conn.query_row(
            "SELECT status FROM tasks WHERE id = ?1",
            params![task_id],
            |row| row.get(0),
        )?;

        let valid = match (current_status.as_str(), status) {
            ("pending", "active") | ("pending", "archived") | ("pending", "deleted") => true,
            ("active", "paused") | ("active", "completed") | ("active", "archived") => true,
            ("paused", "active") | ("paused", "completed") | ("paused", "archived") => true,
            ("completed", "closed") => true,
            // Allow carried_forward to become active, pending, archived, or deleted
            ("carried_forward", "active") | ("carried_forward", "pending") |
            ("carried_forward", "archived") | ("carried_forward", "deleted") => true,
            // Allow reopening completed tasks
            ("completed", "pending") => true,
            _ => false,
        };

        if !valid {
            return Err(rusqlite::Error::InvalidParameterName(
                format!("Invalid state transition from '{}' to '{}'", current_status, status)
            ));
        }

        let now = chrono::Local::now().format("%Y-%m-%d %H:%M:%S").to_string();
        let mut query = "UPDATE tasks SET status = ?1".to_string();

        match status {
            "active" => { query.push_str(", activated_at = COALESCE(activated_at, ?2)"); }
            "completed" => { query.push_str(", completed_at = ?2"); }
            _ => {}
        }

        query.push_str(" WHERE id = ?3");
        conn.execute(&query, params![status, now, task_id])?;

        tracing::info!("Task {} status changed: {} → {}", task_id, current_status, status);
        Ok(())
    }

    pub fn reorder_tasks(&self, task_ids: &[String]) -> Result<()> {
        let conn = self.conn.lock().unwrap();
        for (i, task_id) in task_ids.iter().enumerate() {
            conn.execute("UPDATE tasks SET display_order = ?1 WHERE id = ?2",
                params![i as i32, task_id])?;
        }
        Ok(())
    }

    // ─── Work Session Operations ────────────────────────────────────

    pub fn start_work_session(&self, task_id: &str) -> Result<WorkSession> {
        let conn = self.conn.lock().unwrap();
        let id = uuid::Uuid::new_v4().to_string();
        let now = chrono::Local::now().format("%Y-%m-%d %H:%M:%S").to_string();

        conn.execute(
            "INSERT INTO work_sessions (id, task_id, start_time) VALUES (?1, ?2, ?3)",
            params![id, task_id, now],
        )?;

        Ok(WorkSession {
            id,
            task_id: task_id.to_string(),
            start_time: now,
            end_time: None,
            duration_seconds: 0,
            paused_duration_seconds: 0,
        })
    }

    pub fn end_work_session(&self, session_id: &str) -> Result<WorkSession> {
        let conn = self.conn.lock().unwrap();
        let now = chrono::Local::now().format("%Y-%m-%d %H:%M:%S").to_string();

        // Get start time
        let start_time: String = conn.query_row(
            "SELECT start_time FROM work_sessions WHERE id = ?1",
            params![session_id],
            |row| row.get(0),
        )?;

        // Calculate duration
        let start = chrono::NaiveDateTime::parse_from_str(&start_time, "%Y-%m-%d %H:%M:%S").unwrap_or_default();
        let end = chrono::NaiveDateTime::parse_from_str(&now, "%Y-%m-%d %H:%M:%S").unwrap_or_default();
        let duration = (end - start).num_seconds().max(0);

        conn.execute(
            "UPDATE work_sessions SET end_time = ?1, duration_seconds = ?2 WHERE id = ?3",
            params![now, duration, session_id],
        )?;

        // Update task actual duration
        conn.execute(
            "UPDATE tasks SET actual_duration_seconds = actual_duration_seconds + ?1 WHERE id = (
                SELECT task_id FROM work_sessions WHERE id = ?2
            )",
            params![duration, session_id],
        )?;

        Ok(WorkSession {
            id: session_id.to_string(),
            task_id: String::new(),
            start_time,
            end_time: Some(now),
            duration_seconds: duration,
            paused_duration_seconds: 0,
        })
    }

    pub fn get_active_session(&self, task_id: &str) -> Result<Option<WorkSession>> {
        let conn = self.conn.lock().unwrap();
        let result = conn.query_row(
            "SELECT id, task_id, start_time, end_time, duration_seconds, paused_duration_seconds
             FROM work_sessions WHERE task_id = ?1 AND end_time IS NULL
             ORDER BY start_time DESC LIMIT 1",
            params![task_id],
            |row| {
                Ok(WorkSession {
                    id: row.get(0)?,
                    task_id: row.get(1)?,
                    start_time: row.get(2)?,
                    end_time: row.get(3)?,
                    duration_seconds: row.get(4)?,
                    paused_duration_seconds: row.get(5)?,
                })
            },
        );
        match result {
            Ok(session) => Ok(Some(session)),
            Err(rusqlite::Error::QueryReturnedNoRows) => Ok(None),
            Err(e) => Err(e),
        }
    }

    // ─── Break Session Operations ───────────────────────────────────

    pub fn start_break(&self, day_id: &str, break_type: &str) -> Result<BreakSession> {
        let conn = self.conn.lock().unwrap();
        let id = uuid::Uuid::new_v4().to_string();
        let now = chrono::Local::now().format("%Y-%m-%d %H:%M:%S").to_string();

        conn.execute(
            "INSERT INTO break_sessions (id, day_id, break_type, start_time) VALUES (?1, ?2, ?3, ?4)",
            params![id, day_id, break_type, now],
        )?;

        Ok(BreakSession {
            id,
            day_id: day_id.to_string(),
            break_type: break_type.to_string(),
            start_time: now,
            end_time: None,
            duration_seconds: 0,
            notes: None,
        })
    }

    pub fn end_break(&self, break_id: &str) -> Result<BreakSession> {
        let conn = self.conn.lock().unwrap();
        let now = chrono::Local::now().format("%Y-%m-%d %H:%M:%S").to_string();

        let start_time: String = conn.query_row(
            "SELECT start_time FROM break_sessions WHERE id = ?1",
            params![break_id],
            |row| row.get(0),
        )?;

        let start = chrono::NaiveDateTime::parse_from_str(&start_time, "%Y-%m-%d %H:%M:%S").unwrap_or_default();
        let end = chrono::NaiveDateTime::parse_from_str(&now, "%Y-%m-%d %H:%M:%S").unwrap_or_default();
        let duration = (end - start).num_seconds().max(0);

        conn.execute(
            "UPDATE break_sessions SET end_time = ?1, duration_seconds = ?2 WHERE id = ?3",
            params![now, duration, break_id],
        )?;

        Ok(BreakSession {
            id: break_id.to_string(),
            day_id: String::new(),
            break_type: String::new(),
            start_time,
            end_time: Some(now),
            duration_seconds: duration,
            notes: None,
        })
    }

    pub fn get_active_break(&self, day_id: &str) -> Result<Option<BreakSession>> {
        let conn = self.conn.lock().unwrap();
        let result = conn.query_row(
            "SELECT id, day_id, break_type, start_time, end_time, duration_seconds, notes
             FROM break_sessions WHERE day_id = ?1 AND end_time IS NULL
             ORDER BY start_time DESC LIMIT 1",
            params![day_id],
            |row| {
                Ok(BreakSession {
                    id: row.get(0)?,
                    day_id: row.get(1)?,
                    break_type: row.get(2)?,
                    start_time: row.get(3)?,
                    end_time: row.get(4)?,
                    duration_seconds: row.get(5)?,
                    notes: row.get(6)?,
                })
            },
        );
        match result {
            Ok(bs) => Ok(Some(bs)),
            Err(rusqlite::Error::QueryReturnedNoRows) => Ok(None),
            Err(e) => Err(e),
        }
    }

    // ─── Reflection Operations ──────────────────────────────────────

    pub fn save_reflection(&self, day_id: &str, accomplishments: &str, challenges: &str, tomorrow_task: &str) -> Result<Reflection> {
        let conn = self.conn.lock().unwrap();
        let id = uuid::Uuid::new_v4().to_string();
        let now = chrono::Local::now().format("%Y-%m-%d %H:%M:%S").to_string();

        conn.execute(
            "INSERT OR REPLACE INTO reflections (id, day_id, accomplishments, challenges, tomorrow_first_task, completed_at)
             VALUES (?1, ?2, ?3, ?4, ?5, ?6)",
            params![id, day_id, accomplishments, challenges, tomorrow_task, now],
        )?;

        Ok(Reflection {
            id,
            day_id: day_id.to_string(),
            accomplishments: Some(accomplishments.to_string()),
            challenges: Some(challenges.to_string()),
            tomorrow_first_task: Some(tomorrow_task.to_string()),
            additional_notes: None,
            completed_at: Some(now),
        })
    }

    pub fn get_reflection(&self, day_id: &str) -> Result<Option<Reflection>> {
        let conn = self.conn.lock().unwrap();
        let result = conn.query_row(
            "SELECT id, day_id, accomplishments, challenges, tomorrow_first_task, additional_notes, completed_at
             FROM reflections WHERE day_id = ?1",
            params![day_id],
            |row| {
                Ok(Reflection {
                    id: row.get(0)?,
                    day_id: row.get(1)?,
                    accomplishments: row.get(2)?,
                    challenges: row.get(3)?,
                    tomorrow_first_task: row.get(4)?,
                    additional_notes: row.get(5)?,
                    completed_at: row.get(6)?,
                })
            },
        );
        match result {
            Ok(r) => Ok(Some(r)),
            Err(rusqlite::Error::QueryReturnedNoRows) => Ok(None),
            Err(e) => Err(e),
        }
    }

    // ─── Configuration Operations ───────────────────────────────────

    pub fn get_config(&self) -> Result<AppConfiguration> {
        let conn = self.conn.lock().unwrap();
        let mut stmt = conn.prepare("SELECT key, value FROM configurations")?;
        let configs: std::collections::HashMap<String, String> = stmt.query_map([], |row| {
            Ok((row.get::<_, String>(0)?, row.get::<_, String>(1)?))
        })?.filter_map(|r| r.ok()).collect();

        Ok(AppConfiguration {
            working_hours_start: configs.get("working_hours_start").cloned().unwrap_or_else(|| "09:00".to_string()),
            working_hours_end: configs.get("working_hours_end").cloned().unwrap_or_else(|| "18:00".to_string()),
            lunch_time: configs.get("lunch_time").cloned(),
            dinner_time: configs.get("dinner_time").cloned(),
            overlay_position: configs.get("overlay_position").cloned().unwrap_or_else(|| "bottom-right".to_string()),
            overlay_opacity: configs.get("overlay_opacity").and_then(|v| v.parse().ok()).unwrap_or(0.85),
            theme: configs.get("theme").cloned().unwrap_or_else(|| "dark".to_string()),
            markdown_vault_path: configs.get("markdown_vault_path").cloned(),
            journal_directory: configs.get("journal_directory").cloned().unwrap_or_else(|| "Daily Notes".to_string()),
            notification_enabled: configs.get("notification_enabled").and_then(|v| v.parse().ok()).unwrap_or(true),
            startup_behavior: configs.get("startup_behavior").cloned().unwrap_or_else(|| "restore".to_string()),
            launch_at_startup: configs.get("launch_at_startup").and_then(|v| v.parse().ok()).unwrap_or(false),
            deadline_reminder_minutes: configs.get("deadline_reminder_minutes").and_then(|v| v.parse().ok()).unwrap_or(30),
            break_reminder_enabled: configs.get("break_reminder_enabled").and_then(|v| v.parse().ok()).unwrap_or(true),
            short_break_duration: configs.get("short_break_duration").and_then(|v| v.parse().ok()).unwrap_or(5),
            long_break_duration: configs.get("long_break_duration").and_then(|v| v.parse().ok()).unwrap_or(15),
            sessions_before_long_break: configs.get("sessions_before_long_break").and_then(|v| v.parse().ok()).unwrap_or(4),
        })
    }

    pub fn save_config(&self, config: &AppConfiguration) -> Result<()> {
        let conn = self.conn.lock().unwrap();
        let pairs = vec![
            ("working_hours_start", config.working_hours_start.clone()),
            ("working_hours_end", config.working_hours_end.clone()),
            ("lunch_time", config.lunch_time.clone().unwrap_or_default()),
            ("dinner_time", config.dinner_time.clone().unwrap_or_default()),
            ("overlay_position", config.overlay_position.clone()),
            ("overlay_opacity", config.overlay_opacity.to_string()),
            ("theme", config.theme.clone()),
            ("markdown_vault_path", config.markdown_vault_path.clone().unwrap_or_default()),
            ("journal_directory", config.journal_directory.clone()),
            ("notification_enabled", config.notification_enabled.to_string()),
            ("startup_behavior", config.startup_behavior.clone()),
            ("launch_at_startup", config.launch_at_startup.to_string()),
            ("deadline_reminder_minutes", config.deadline_reminder_minutes.to_string()),
            ("break_reminder_enabled", config.break_reminder_enabled.to_string()),
            ("short_break_duration", config.short_break_duration.to_string()),
            ("long_break_duration", config.long_break_duration.to_string()),
            ("sessions_before_long_break", config.sessions_before_long_break.to_string()),
        ];

        for (key, value) in pairs {
            conn.execute(
                "INSERT OR REPLACE INTO configurations (key, value) VALUES (?1, ?2)",
                params![key, value],
            )?;
        }
        Ok(())
    }

    // ─── App State Operations ───────────────────────────────────────

    pub fn get_app_state(&self) -> Result<(String, Option<String>, Option<String>)> {
        let conn = self.conn.lock().unwrap();
        let result = conn.query_row(
            "SELECT current_state, active_task_id, current_day_id FROM app_state WHERE id = 1",
            [],
            |row| {
                Ok((row.get::<_, String>(0)?, row.get::<_, Option<String>>(1)?, row.get::<_, Option<String>>(2)?))
            },
        );
        match result {
            Ok(state) => Ok(state),
            Err(rusqlite::Error::QueryReturnedNoRows) => {
                Ok(("idle".to_string(), None, None))
            }
            Err(e) => Err(e),
        }
    }

    pub fn set_app_state(&self, state: &str, active_task_id: Option<&str>, current_day_id: Option<&str>) -> Result<()> {
        let conn = self.conn.lock().unwrap();
        let now = chrono::Local::now().format("%Y-%m-%d %H:%M:%S").to_string();
        conn.execute(
            "UPDATE app_state SET current_state = ?1, active_task_id = ?2, current_day_id = ?3, updated_at = ?4 WHERE id = 1",
            params![state, active_task_id, current_day_id, now],
        )?;
        Ok(())
    }

    // ─── Carry Forward Operations ───────────────────────────────────

    /// Get unfinished tasks from previous days (not today) that are pending, paused, or carried_forward
    pub fn get_carry_forward_tasks(&self) -> Result<Vec<Task>> {
        let conn = self.conn.lock().unwrap();
        let today = chrono::Local::now().format("%Y-%m-%d").to_string();
        let mut stmt = conn.prepare(
            "SELECT t.id, t.day_id, t.title, t.description, t.priority, t.status, t.deadline,
                    t.estimated_duration_minutes, t.actual_duration_seconds, t.display_order,
                    t.notes, t.created_at, t.activated_at, t.completed_at, t.carry_forward_count
             FROM tasks t
             JOIN days d ON t.day_id = d.id
             WHERE d.date < ?1
               AND t.status IN ('pending', 'paused', 'carried_forward')
               AND t.status != 'deleted'
             ORDER BY d.date DESC, t.display_order ASC"
        )?;

        let tasks = stmt.query_map(params![today], |row| {
            Ok(Task {
                id: row.get(0)?,
                day_id: row.get(1)?,
                title: row.get(2)?,
                description: row.get(3)?,
                priority: Priority::from_str(&row.get::<_, String>(4)?),
                status: TaskStatus::from_str(&row.get::<_, String>(5)?),
                deadline: row.get(6)?,
                estimated_duration_minutes: row.get(7)?,
                actual_duration_seconds: row.get(8)?,
                display_order: row.get(9)?,
                notes: row.get(10)?,
                created_at: row.get(11)?,
                activated_at: row.get(12)?,
                completed_at: row.get(13)?,
                carry_forward_count: row.get(14)?,
            })
        })?.collect::<Result<Vec<_>>>()?;

        Ok(tasks)
    }

    /// Copy a task to today's plan with status 'carried_forward' and incremented count
    pub fn carry_forward_task(&self, task_id: &str, today_id: &str) -> Result<Task> {
        tracing::debug!("Carrying forward task: {}", task_id);
        let conn = self.conn.lock().unwrap();

        // Get original task
        let original = conn.query_row(
            "SELECT id, day_id, title, description, priority, deadline, estimated_duration_minutes,
                    actual_duration_seconds, notes, carry_forward_count
             FROM tasks WHERE id = ?1",
            params![task_id],
            |row| {
                Ok((
                    row.get::<_, String>(0)?,
                    row.get::<_, String>(1)?,
                    row.get::<_, String>(2)?,
                    row.get::<_, Option<String>>(3)?,
                    row.get::<_, String>(4)?,
                    row.get::<_, Option<String>>(5)?,
                    row.get::<_, Option<i32>>(6)?,
                    row.get::<_, i64>(7)?,
                    row.get::<_, Option<String>>(8)?,
                    row.get::<_, i32>(9)?,
                ))
            },
        )?;

        let (old_id, _old_day_id, title, description, priority, deadline,
             estimated_duration, actual_duration, notes, carry_forward_count) = original;

        let new_id = uuid::Uuid::new_v4().to_string();
        let now = chrono::Local::now().format("%Y-%m-%d %H:%M:%S").to_string();

        let max_order: i32 = conn.query_row(
            "SELECT COALESCE(MAX(display_order), -1) + 1 FROM tasks WHERE day_id = ?1",
            params![today_id],
            |row| row.get(0),
        )?;

        conn.execute(
            "INSERT INTO tasks (id, day_id, title, description, priority, status, deadline,
             estimated_duration_minutes, actual_duration_seconds, display_order, notes, created_at, carry_forward_count)
             VALUES (?1, ?2, ?3, ?4, ?5, 'carried_forward', ?6, ?7, ?8, ?9, ?10, ?11, ?12)",
            params![
                new_id, today_id, title, description, priority,
                deadline, estimated_duration, actual_duration,
                max_order, notes, now, carry_forward_count + 1,
            ],
        )?;

        // Archive the old task so it's not carried forward again
        conn.execute(
            "UPDATE tasks SET status = 'archived' WHERE id = ?1",
            params![old_id],
        )?;

        tracing::info!("Task carried forward: {} → new id: {} (count: {})", title, new_id, carry_forward_count + 1);

        Ok(Task {
            id: new_id,
            day_id: today_id.to_string(),
            title,
            description,
            priority: Priority::from_str(&priority),
            status: TaskStatus::CarriedForward,
            deadline,
            estimated_duration_minutes: estimated_duration,
            actual_duration_seconds: 0, // Reset duration for the new day
            display_order: max_order,
            notes,
            created_at: now,
            activated_at: None,
            completed_at: None,
            carry_forward_count: carry_forward_count + 1,
        })
    }

    /// Auto-carry-forward all unfinished tasks from previous days to today
    pub fn auto_carry_forward_all(&self, today_id: &str) -> Result<Vec<Task>> {
        let unfinished = self.get_carry_forward_tasks()?;
        let mut carried = Vec::new();
        for task in unfinished {
            carried.push(self.carry_forward_task(&task.id, today_id)?);
        }
        Ok(carried)
    }

    // ─── Summary Operations ─────────────────────────────────────────

    pub fn generate_daily_summary(&self, day_id: &str) -> Result<DailySummary> {
        let conn = self.conn.lock().unwrap();

        let total: i32 = conn.query_row(
            "SELECT COUNT(*) FROM tasks WHERE day_id = ?1 AND status != 'deleted'",
            params![day_id], |row| row.get(0),
        )?;

        let completed: i32 = conn.query_row(
            "SELECT COUNT(*) FROM tasks WHERE day_id = ?1 AND status = 'completed'",
            params![day_id], |row| row.get(0),
        )?;

        let carried: i32 = conn.query_row(
            "SELECT COUNT(*) FROM tasks WHERE day_id = ?1 AND status = 'carried_forward'",
            params![day_id], |row| row.get(0),
        )?;

        let archived: i32 = conn.query_row(
            "SELECT COUNT(*) FROM tasks WHERE day_id = ?1 AND status = 'archived'",
            params![day_id], |row| row.get(0),
        )?;

        let focus_seconds: i64 = conn.query_row(
            "SELECT COALESCE(SUM(duration_seconds), 0) FROM work_sessions ws
             JOIN tasks t ON ws.task_id = t.id WHERE t.day_id = ?1",
            params![day_id], |row| row.get(0),
        )?;

        let break_seconds: i64 = conn.query_row(
            "SELECT COALESCE(SUM(duration_seconds), 0) FROM break_sessions WHERE day_id = ?1",
            params![day_id], |row| row.get(0),
        )?;

        let longest: i64 = conn.query_row(
            "SELECT COALESCE(MAX(duration_seconds), 0) FROM work_sessions ws
             JOIN tasks t ON ws.task_id = t.id WHERE t.day_id = ?1",
            params![day_id], |row| row.get(0),
        )?;

        let session_count: i32 = conn.query_row(
            "SELECT COUNT(*) FROM work_sessions ws
             JOIN tasks t ON ws.task_id = t.id WHERE t.day_id = ?1 AND ws.end_time IS NOT NULL",
            params![day_id], |row| row.get(0),
        )?;

        let pct = if total > 0 { (completed as f64 / total as f64) * 100.0 } else { 0.0 };

        let id = uuid::Uuid::new_v4().to_string();

        conn.execute(
            "INSERT OR REPLACE INTO daily_summaries (id, day_id, total_planned, completed, carried_forward, archived,
             deleted_count, total_focus_seconds, total_break_seconds, completion_percentage, longest_session_seconds, session_count)
             VALUES (?1, ?2, ?3, ?4, ?5, ?6, 0, ?7, ?8, ?9, ?10, ?11)",
            params![id, day_id, total, completed, carried, archived, focus_seconds, break_seconds, pct, longest, session_count],
        )?;

        Ok(DailySummary {
            id,
            day_id: day_id.to_string(),
            total_planned: total,
            completed,
            carried_forward: carried,
            archived,
            deleted_count: 0,
            total_focus_seconds: focus_seconds,
            total_break_seconds: break_seconds,
            completion_percentage: pct,
            longest_session_seconds: longest,
            session_count,
            generated_markdown_path: None,
            archived_at: None,
        })
    }

    pub fn get_daily_summary(&self, day_id: &str) -> Result<Option<DailySummary>> {
        let conn = self.conn.lock().unwrap();
        let result = conn.query_row(
            "SELECT id, day_id, total_planned, completed, carried_forward, archived, deleted_count,
                    total_focus_seconds, total_break_seconds, completion_percentage, longest_session_seconds,
                    session_count, generated_markdown_path, archived_at
             FROM daily_summaries WHERE day_id = ?1",
            params![day_id],
            |row| {
                Ok(DailySummary {
                    id: row.get(0)?,
                    day_id: row.get(1)?,
                    total_planned: row.get(2)?,
                    completed: row.get(3)?,
                    carried_forward: row.get(4)?,
                    archived: row.get(5)?,
                    deleted_count: row.get(6)?,
                    total_focus_seconds: row.get(7)?,
                    total_break_seconds: row.get(8)?,
                    completion_percentage: row.get(9)?,
                    longest_session_seconds: row.get(10)?,
                    session_count: row.get(11)?,
                    generated_markdown_path: row.get(12)?,
                    archived_at: row.get(13)?,
                })
            },
        );
        match result {
            Ok(s) => Ok(Some(s)),
            Err(rusqlite::Error::QueryReturnedNoRows) => Ok(None),
            Err(e) => Err(e),
        }
    }

    // ─── Search Operations ──────────────────────────────────────────

    pub fn search_tasks(&self, query: &str, limit: i32) -> Result<Vec<Task>> {
        let conn = self.conn.lock().unwrap();

        // Try FTS5 search first; fall back to LIKE if query is very short or FTS5 fails
        if query.len() >= 2 {
            // Sanitize FTS5 query: escape special characters and add prefix matching
            let fts_query = query
                .split_whitespace()
                .map(|word| format!("\"{}*\"", word.replace('"', "")))
                .collect::<Vec<_>>()
                .join(" AND ");

            // Try FTS5 with the original query as a fallback
            let fts_result = conn.prepare(
                "SELECT t.id, t.day_id, t.title, t.description, t.priority, t.status, t.deadline,
                        t.estimated_duration_minutes, t.actual_duration_seconds, t.display_order,
                        t.notes, t.created_at, t.activated_at, t.completed_at, t.carry_forward_count
                 FROM tasks t
                 INNER JOIN tasks_fts fts ON fts.rowid = t.rowid
                 WHERE tasks_fts MATCH ?1
                   AND t.status != 'deleted'
                 ORDER BY rank
                 LIMIT ?2"
            );

            if let Ok(mut stmt) = fts_result {
                let tasks_result = stmt.query_map(params![fts_query, limit], |row| {
                    Ok(Task {
                        id: row.get(0)?,
                        day_id: row.get(1)?,
                        title: row.get(2)?,
                        description: row.get(3)?,
                        priority: Priority::from_str(&row.get::<_, String>(4)?),
                        status: TaskStatus::from_str(&row.get::<_, String>(5)?),
                        deadline: row.get(6)?,
                        estimated_duration_minutes: row.get(7)?,
                        actual_duration_seconds: row.get(8)?,
                        display_order: row.get(9)?,
                        notes: row.get(10)?,
                        created_at: row.get(11)?,
                        activated_at: row.get(12)?,
                        completed_at: row.get(13)?,
                        carry_forward_count: row.get(14)?,
                    })
                });

                if let Ok(tasks) = tasks_result {
                    let results: Vec<Task> = tasks.filter_map(|r| r.ok()).collect();
                    if !results.is_empty() {
                        return Ok(results);
                    }
                }
            }
        }

        // Fallback: LIKE search for short queries or when FTS5 returns nothing
        let pattern = format!("%{}%", query);
        let mut stmt = conn.prepare(
            "SELECT id, day_id, title, description, priority, status, deadline, estimated_duration_minutes,
                    actual_duration_seconds, display_order, notes, created_at, activated_at, completed_at, carry_forward_count
             FROM tasks
             WHERE (title LIKE ?1 OR description LIKE ?1 OR notes LIKE ?1)
             AND status != 'deleted'
             ORDER BY
                CASE WHEN title LIKE ?2 THEN 0 ELSE 1 END,
                created_at DESC
             LIMIT ?3"
        )?;

        let tasks = stmt.query_map(params![pattern, query, limit], |row| {
            Ok(Task {
                id: row.get(0)?,
                day_id: row.get(1)?,
                title: row.get(2)?,
                description: row.get(3)?,
                priority: Priority::from_str(&row.get::<_, String>(4)?),
                status: TaskStatus::from_str(&row.get::<_, String>(5)?),
                deadline: row.get(6)?,
                estimated_duration_minutes: row.get(7)?,
                actual_duration_seconds: row.get(8)?,
                display_order: row.get(9)?,
                notes: row.get(10)?,
                created_at: row.get(11)?,
                activated_at: row.get(12)?,
                completed_at: row.get(13)?,
                carry_forward_count: row.get(14)?,
            })
        })?.collect::<Result<Vec<_>>>()?;

        Ok(tasks)
    }

    // ─── History Operations ─────────────────────────────────────────

    pub fn get_previous_days(&self, limit: i32) -> Result<Vec<(Day, Option<DailySummary>)>> {
        let conn = self.conn.lock().unwrap();
        let mut stmt = conn.prepare(
            "SELECT id, date, start_time, end_time, status, created_at, updated_at
             FROM days
             ORDER BY date DESC
             LIMIT ?1"
        )?;

        let days: Vec<Day> = stmt.query_map(params![limit], |row| {
            Ok(Day {
                id: row.get(0)?,
                date: row.get(1)?,
                start_time: row.get(2)?,
                end_time: row.get(3)?,
                status: row.get(4)?,
                created_at: row.get(5)?,
                updated_at: row.get(6)?,
            })
        })?.collect::<Result<Vec<_>>>()?;

        let mut result = Vec::new();
        for day in days {
            let summary = self.get_daily_summary(&day.id).ok().flatten();
            result.push((day, summary));
        }
        Ok(result)
    }

    // ─── Day Shutdown Operations ────────────────────────────────────

    pub fn shutdown_day(&self, day_id: &str) -> Result<()> {
        let conn = self.conn.lock().unwrap();
        let now = chrono::Local::now().format("%Y-%m-%d %H:%M:%S").to_string();

        // End any active work sessions
        conn.execute(
            "UPDATE work_sessions SET end_time = ?1, duration_seconds =
             CAST((julianday(?1) - julianday(start_time)) * 86400 AS INTEGER)
             WHERE end_time IS NULL",
            params![now],
        ).ok();

        // Generate daily summary
        drop(conn);

        // Set day end time and status
        let conn = self.conn.lock().unwrap();
        conn.execute(
            "UPDATE days SET end_time = ?1, status = 'completed', updated_at = ?1 WHERE id = ?2",
            params![now, day_id],
        )?;

        // Set app state to shutdown
        conn.execute(
            "UPDATE app_state SET current_state = 'shutdown', active_task_id = NULL, updated_at = ?1 WHERE id = 1",
            params![now],
        )?;

        tracing::info!("Day {} shutdown completed", day_id);
        Ok(())
    }
}
