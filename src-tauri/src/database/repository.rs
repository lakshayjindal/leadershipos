use rusqlite::{params, Connection, Result};
use crate::models::session::Session;
use crate::models::task::Task;
use crate::models::time_entry::TimeEntry;
use crate::models::reflection::Reflection;
use crate::models::settings::Settings;
use uuid::Uuid;
use chrono::Local;

pub fn create_session(conn: &Connection, date: &str) -> Result<Session> {
    let id = Uuid::new_v4().to_string();
    let now = Local::now().format("%Y-%m-%d %H:%M:%S").to_string();
    conn.execute(
        "INSERT INTO sessions (id, date, status, created_at, updated_at) VALUES (?1, ?2, 'planning', ?3, ?4)",
        params![id, date, now, now],
    )?;
    Ok(Session {
        id,
        date: date.to_string(),
        status: "planning".to_string(),
        created_at: now.clone(),
        updated_at: now,
    })
}

pub fn get_today_session(conn: &Connection) -> Result<Option<Session>> {
    let today = Local::now().format("%Y-%m-%d").to_string();
    let mut stmt = conn.prepare(
        "SELECT id, date, status, created_at, updated_at FROM sessions WHERE date = ?1 ORDER BY created_at DESC LIMIT 1"
    )?;
    let mut rows = stmt.query(params![today])?;
    if let Some(row) = rows.next()? {
        Ok(Some(Session {
            id: row.get(0)?,
            date: row.get(1)?,
            status: row.get(2)?,
            created_at: row.get(3)?,
            updated_at: row.get(4)?,
        }))
    } else {
        Ok(None)
    }
}

pub fn get_session_by_id(conn: &Connection, session_id: &str) -> Result<Option<Session>> {
    let mut stmt = conn.prepare(
        "SELECT id, date, status, created_at, updated_at FROM sessions WHERE id = ?1"
    )?;
    let mut rows = stmt.query(params![session_id])?;
    if let Some(row) = rows.next()? {
        Ok(Some(Session {
            id: row.get(0)?,
            date: row.get(1)?,
            status: row.get(2)?,
            created_at: row.get(3)?,
            updated_at: row.get(4)?,
        }))
    } else {
        Ok(None)
    }
}

pub fn update_session_status(conn: &Connection, session_id: &str, status: &str) -> Result<()> {
    let now = Local::now().format("%Y-%m-%d %H:%M:%S").to_string();
    conn.execute(
        "UPDATE sessions SET status = ?1, updated_at = ?2 WHERE id = ?3",
        params![status, now, session_id],
    )?;
    Ok(())
}

pub fn create_task(
    conn: &Connection,
    session_id: &str,
    title: &str,
    description: &str,
    priority: &str,
    estimated_duration_minutes: i32,
    carry_forward_count: i32,
) -> Result<Task> {
    let id = Uuid::new_v4().to_string();
    let now = Local::now().format("%Y-%m-%d %H:%M:%S").to_string();

    // Get next sort order
    let max_order: i32 = conn
        .query_row(
            "SELECT COALESCE(MAX(sort_order), -1) FROM tasks WHERE session_id = ?1",
            params![session_id],
            |row| row.get(0),
        )?;

    conn.execute(
        "INSERT INTO tasks (id, session_id, title, description, priority, estimated_duration_minutes, status, carry_forward_count, sort_order, created_at, updated_at)
         VALUES (?1, ?2, ?3, ?4, ?5, ?6, 'pending', ?7, ?8, ?9, ?10)",
        params![id, session_id, title, description, priority, estimated_duration_minutes, carry_forward_count, max_order + 1, now, now],
    )?;
    Ok(Task {
        id,
        session_id: session_id.to_string(),
        title: title.to_string(),
        description: description.to_string(),
        priority: priority.to_string(),
        estimated_duration_minutes,
        actual_duration_minutes: None,
        status: "pending".to_string(),
        carry_forward_count,
        sort_order: max_order + 1,
        created_at: now.clone(),
        updated_at: now,
    })
}

pub fn get_tasks_by_session(conn: &Connection, session_id: &str) -> Result<Vec<Task>> {
    let mut stmt = conn.prepare(
        "SELECT id, session_id, title, description, priority, estimated_duration_minutes, actual_duration_minutes, status, carry_forward_count, sort_order, created_at, updated_at
         FROM tasks WHERE session_id = ?1 ORDER BY sort_order ASC"
    )?;
    let rows = stmt.query_map(params![session_id], |row| {
        Ok(Task {
            id: row.get(0)?,
            session_id: row.get(1)?,
            title: row.get(2)?,
            description: row.get(3)?,
            priority: row.get(4)?,
            estimated_duration_minutes: row.get(5)?,
            actual_duration_minutes: row.get(6)?,
            status: row.get(7)?,
            carry_forward_count: row.get(8)?,
            sort_order: row.get(9)?,
            created_at: row.get(10)?,
            updated_at: row.get(11)?,
        })
    })?;
    let mut tasks = Vec::new();
    for task in rows {
        tasks.push(task?);
    }
    Ok(tasks)
}

pub fn update_task(conn: &Connection, task: &Task) -> Result<()> {
    let now = Local::now().format("%Y-%m-%d %H:%M:%S").to_string();
    conn.execute(
        "UPDATE tasks SET title = ?1, description = ?2, priority = ?3, estimated_duration_minutes = ?4, actual_duration_minutes = ?5, status = ?6, sort_order = ?7, updated_at = ?8 WHERE id = ?9",
        params![task.title, task.description, task.priority, task.estimated_duration_minutes, task.actual_duration_minutes, task.status, task.sort_order, now, task.id],
    )?;
    Ok(())
}

pub fn update_task_status(conn: &Connection, task_id: &str, status: &str) -> Result<()> {
    let now = Local::now().format("%Y-%m-%d %H:%M:%S").to_string();
    conn.execute(
        "UPDATE tasks SET status = ?1, updated_at = ?2 WHERE id = ?3",
        params![status, now, task_id],
    )?;
    Ok(())
}

pub fn update_task_actual_duration(conn: &Connection, task_id: &str, minutes: i32) -> Result<()> {
    let now = Local::now().format("%Y-%m-%d %H:%M:%S").to_string();
    conn.execute(
        "UPDATE tasks SET actual_duration_minutes = ?1, updated_at = ?2 WHERE id = ?3",
        params![minutes, now, task_id],
    )?;
    Ok(())
}

pub fn delete_task(conn: &Connection, task_id: &str) -> Result<()> {
    conn.execute("DELETE FROM tasks WHERE id = ?1", params![task_id])?;
    Ok(())
}

pub fn reorder_tasks(conn: &Connection, task_ids: &[String]) -> Result<()> {
    for (i, task_id) in task_ids.iter().enumerate() {
        conn.execute(
            "UPDATE tasks SET sort_order = ?1 WHERE id = ?2",
            params![i as i32, task_id],
        )?;
    }
    Ok(())
}

pub fn get_incomplete_tasks_before_date(conn: &Connection, date: &str) -> Result<Vec<Task>> {
    let mut stmt = conn.prepare(
        "SELECT t.id, t.session_id, t.title, t.description, t.priority, t.estimated_duration_minutes, t.actual_duration_minutes, t.status, t.carry_forward_count, t.sort_order, t.created_at, t.updated_at
         FROM tasks t
         JOIN sessions s ON t.session_id = s.id
         WHERE s.date < ?1 AND t.status IN ('pending', 'active', 'paused')
         ORDER BY s.date DESC, t.sort_order ASC"
    )?;
    let rows = stmt.query_map(params![date], |row| {
        Ok(Task {
            id: row.get(0)?,
            session_id: row.get(1)?,
            title: row.get(2)?,
            description: row.get(3)?,
            priority: row.get(4)?,
            estimated_duration_minutes: row.get(5)?,
            actual_duration_minutes: row.get(6)?,
            status: row.get(7)?,
            carry_forward_count: row.get(8)?,
            sort_order: row.get(9)?,
            created_at: row.get(10)?,
            updated_at: row.get(11)?,
        })
    })?;
    let mut tasks = Vec::new();
    for task in rows {
        tasks.push(task?);
    }
    Ok(tasks)
}

pub fn start_time_entry(conn: &Connection, task_id: &str) -> Result<TimeEntry> {
    let id = Uuid::new_v4().to_string();
    let now = Local::now().format("%Y-%m-%d %H:%M:%S").to_string();
    conn.execute(
        "INSERT INTO time_entries (id, task_id, start_time, created_at) VALUES (?1, ?2, ?3, ?4)",
        params![id, task_id, now.clone(), now.clone()],
    )?;
    Ok(TimeEntry {
        id,
        task_id: task_id.to_string(),
        start_time: now.clone(),
        end_time: None,
        duration_minutes: None,
        created_at: now,
    })
}

pub fn stop_time_entry(conn: &Connection, entry_id: &str) -> Result<TimeEntry> {
    let now = Local::now().format("%Y-%m-%d %H:%M:%S").to_string();
    // Calculate duration from start_time to now
    let mut stmt = conn.prepare(
        "SELECT start_time FROM time_entries WHERE id = ?1"
    )?;
    let start_time: String = stmt.query_row(params![entry_id], |row| row.get(0))?;

    let start = chrono::NaiveDateTime::parse_from_str(&start_time, "%Y-%m-%d %H:%M:%S").unwrap();
    let end = chrono::NaiveDateTime::parse_from_str(&now, "%Y-%m-%d %H:%M:%S").unwrap();
    let duration = (end - start).num_minutes() as i32;

    conn.execute(
        "UPDATE time_entries SET end_time = ?1, duration_minutes = ?2 WHERE id = ?3",
        params![now.clone(), duration, entry_id],
    )?;
    Ok(TimeEntry {
            id: entry_id.to_string(),
            task_id: String::new(),
            start_time: start_time.clone(),
            end_time: Some(now.clone()),
            duration_minutes: Some(duration),
            created_at: start_time.clone(),
        })
}

pub fn get_active_time_entry(conn: &Connection, task_id: &str) -> Result<Option<TimeEntry>> {
    let mut stmt = conn.prepare(
        "SELECT id, task_id, start_time, end_time, duration_minutes, created_at
         FROM time_entries WHERE task_id = ?1 AND end_time IS NULL ORDER BY start_time DESC LIMIT 1"
    )?;
    let mut rows = stmt.query(params![task_id])?;
    if let Some(row) = rows.next()? {
        Ok(Some(TimeEntry {
            id: row.get(0)?,
            task_id: row.get(1)?,
            start_time: row.get(2)?,
            end_time: row.get(3)?,
            duration_minutes: row.get(4)?,
            created_at: row.get(5)?,
        }))
    } else {
        Ok(None)
    }
}

pub fn get_task_time_entries(conn: &Connection, task_id: &str) -> Result<Vec<TimeEntry>> {
    let mut stmt = conn.prepare(
        "SELECT id, task_id, start_time, end_time, duration_minutes, created_at
         FROM time_entries WHERE task_id = ?1 ORDER BY start_time ASC"
    )?;
    let rows = stmt.query_map(params![task_id], |row| {
        Ok(TimeEntry {
            id: row.get(0)?,
            task_id: row.get(1)?,
            start_time: row.get(2)?,
            end_time: row.get(3)?,
            duration_minutes: row.get(4)?,
            created_at: row.get(5)?,
        })
    })?;
    let mut entries = Vec::new();
    for entry in rows {
        entries.push(entry?);
    }
    Ok(entries)
}

pub fn upsert_reflection(
    conn: &Connection,
    session_id: &str,
    went_well: &str,
    went_wrong: &str,
    improve: &str,
) -> Result<Reflection> {
    let now = Local::now().format("%Y-%m-%d %H:%M:%S").to_string();

    let existing: Option<String> = conn
        .query_row(
            "SELECT id FROM reflections WHERE session_id = ?1",
            params![session_id],
            |row| row.get(0),
        )
        .ok();

    if let Some(reflection_id) = existing {
        conn.execute(
            "UPDATE reflections SET went_well = ?1, went_wrong = ?2, improve = ?3, updated_at = ?4 WHERE id = ?5",
            params![went_well, went_wrong, improve, now, reflection_id],
        )?;
        Ok(Reflection {
            id: reflection_id,
            session_id: session_id.to_string(),
            went_well: went_well.to_string(),
            went_wrong: went_wrong.to_string(),
            improve: improve.to_string(),
            created_at: String::new(),
            updated_at: now,
        })
    } else {
        let id = Uuid::new_v4().to_string();
        conn.execute(
            "INSERT INTO reflections (id, session_id, went_well, went_wrong, improve, created_at, updated_at) VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7)",
            params![id, session_id, went_well, went_wrong, improve, now, now],
        )?;
        Ok(Reflection {
            id,
            session_id: session_id.to_string(),
            went_well: went_well.to_string(),
            went_wrong: went_wrong.to_string(),
            improve: improve.to_string(),
            created_at: now.clone(),
            updated_at: now,
        })
    }
}

pub fn get_reflection_by_session(conn: &Connection, session_id: &str) -> Result<Option<Reflection>> {
    let mut stmt = conn.prepare(
        "SELECT id, session_id, went_well, went_wrong, improve, created_at, updated_at
         FROM reflections WHERE session_id = ?1"
    )?;
    let mut rows = stmt.query(params![session_id])?;
    if let Some(row) = rows.next()? {
        Ok(Some(Reflection {
            id: row.get(0)?,
            session_id: row.get(1)?,
            went_well: row.get(2)?,
            went_wrong: row.get(3)?,
            improve: row.get(4)?,
            created_at: row.get(5)?,
            updated_at: row.get(6)?,
        }))
    } else {
        Ok(None)
    }
}

pub fn get_settings(conn: &Connection) -> Result<Settings> {
    let mut stmt = conn.prepare(
        "SELECT id, obsidian_vault_path, reminder_interval_minutes, default_task_duration_minutes, working_hours_start, working_hours_end, theme, created_at, updated_at
         FROM settings LIMIT 1"
    )?;
    let result = stmt.query_row([], |row| {
        Ok(Settings {
            id: row.get(0)?,
            obsidian_vault_path: row.get(1)?,
            reminder_interval_minutes: row.get(2)?,
            default_task_duration_minutes: row.get(3)?,
            working_hours_start: row.get(4)?,
            working_hours_end: row.get(5)?,
            theme: row.get(6)?,
            created_at: row.get(7)?,
            updated_at: row.get(8)?,
        })
    });

    match result {
        Ok(settings) => Ok(settings),
        Err(rusqlite::Error::QueryReturnedNoRows) => {
            let id = Uuid::new_v4().to_string();
            let now = Local::now().format("%Y-%m-%d %H:%M:%S").to_string();
            conn.execute(
                "INSERT INTO settings (id, obsidian_vault_path, reminder_interval_minutes, default_task_duration_minutes, working_hours_start, working_hours_end, theme, created_at, updated_at)
                 VALUES (?1, '~/Documents/obsidian/days', 5, 30, '09:00', '17:00', 'system', ?2, ?3)",
                params![id, now, now],
            )?;
            Ok(Settings {
                id,
                obsidian_vault_path: "~/Documents/obsidian/days".to_string(),
                reminder_interval_minutes: 5,
                default_task_duration_minutes: 30,
                working_hours_start: "09:00".to_string(),
                working_hours_end: "17:00".to_string(),
                theme: "system".to_string(),
                created_at: now.clone(),
                updated_at: now,
            })
        }
        Err(e) => Err(e),
    }
}

pub fn update_settings(conn: &Connection, settings: &Settings) -> Result<()> {
    let now = Local::now().format("%Y-%m-%d %H:%M:%S").to_string();
    conn.execute(
        "UPDATE settings SET obsidian_vault_path = ?1, reminder_interval_minutes = ?2, default_task_duration_minutes = ?3, working_hours_start = ?4, working_hours_end = ?5, theme = ?6, updated_at = ?7 WHERE id = ?8",
        params![settings.obsidian_vault_path, settings.reminder_interval_minutes, settings.default_task_duration_minutes, settings.working_hours_start, settings.working_hours_end, settings.theme, now, settings.id],
    )?;
    Ok(())
}
