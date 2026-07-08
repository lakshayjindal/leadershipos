use rusqlite::{Connection, Result};
use std::sync::Mutex;

pub mod repository;

pub struct Database {
    pub conn: Mutex<Connection>,
}

impl Database {
    pub fn new(db_path: &str) -> Result<Self> {
        let conn = Connection::open(db_path)?;
        let db = Database {
            conn: Mutex::new(conn),
        };
        db.run_migrations()?;
        Ok(db)
    }

    fn run_migrations(&self) -> Result<()> {
        let conn = self.conn.lock().unwrap();

        conn.execute_batch(
            "
            CREATE TABLE IF NOT EXISTS sessions (
                id TEXT PRIMARY KEY,
                date TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'planning',
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                updated_at TEXT NOT NULL DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS tasks (
                id TEXT PRIMARY KEY,
                session_id TEXT NOT NULL,
                title TEXT NOT NULL,
                description TEXT NOT NULL DEFAULT '',
                priority TEXT NOT NULL,
                estimated_duration_minutes INTEGER NOT NULL,
                actual_duration_minutes INTEGER,
                status TEXT NOT NULL DEFAULT 'pending',
                carry_forward_count INTEGER NOT NULL DEFAULT 0,
                sort_order INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                updated_at TEXT NOT NULL DEFAULT (datetime('now')),
                FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS time_entries (
                id TEXT PRIMARY KEY,
                task_id TEXT NOT NULL,
                start_time TEXT NOT NULL,
                end_time TEXT,
                duration_minutes INTEGER,
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS reflections (
                id TEXT PRIMARY KEY,
                session_id TEXT NOT NULL,
                went_well TEXT NOT NULL DEFAULT '',
                went_wrong TEXT NOT NULL DEFAULT '',
                improve TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                updated_at TEXT NOT NULL DEFAULT (datetime('now')),
                FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS settings (
                id TEXT PRIMARY KEY,
                obsidian_vault_path TEXT NOT NULL DEFAULT '~/Documents/obsidian/days',
                reminder_interval_minutes INTEGER NOT NULL DEFAULT 5,
                default_task_duration_minutes INTEGER NOT NULL DEFAULT 30,
                working_hours_start TEXT NOT NULL DEFAULT '09:00',
                working_hours_end TEXT NOT NULL DEFAULT '17:00',
                theme TEXT NOT NULL DEFAULT 'system',
                desktop_notifications INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                updated_at TEXT NOT NULL DEFAULT (datetime('now'))
            );

            CREATE INDEX IF NOT EXISTS idx_tasks_session ON tasks(session_id);
            CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);
            CREATE INDEX IF NOT EXISTS idx_time_entries_task ON time_entries(task_id);
            CREATE INDEX IF NOT EXISTS idx_reflections_session ON reflections(session_id);
            CREATE INDEX IF NOT EXISTS idx_sessions_date ON sessions(date);
            ",
        )?;

        // Migration: add desktop_notifications column if it doesn't exist
        // SQLite will error if column already exists, so we catch that gracefully
        let _ = conn.execute(
            "ALTER TABLE settings ADD COLUMN desktop_notifications INTEGER NOT NULL DEFAULT 1",
            [],
        );

        Ok(())
    }
}
