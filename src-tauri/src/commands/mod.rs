use crate::database::{Database, repository};
use crate::markdown;
use crate::models::reflection::Reflection;
use crate::models::session::Session;
use crate::models::settings::Settings;
use crate::models::task::Task;
use crate::models::time_entry::TimeEntry;
use chrono::Local;

// ─── Session Commands ───────────────────────────────────────────────────────

#[tauri::command]
pub fn start_session(db: tauri::State<Database>) -> Result<Session, String> {
    let conn = db.conn.lock().map_err(|e| e.to_string())?;
    let today = Local::now().format("%Y-%m-%d").to_string();

    // Check if session already exists for today
    if let Some(session) = repository::get_today_session(&conn).map_err(|e| e.to_string())? {
        return Ok(session);
    }

    // Check for incomplete tasks from previous days
    let incomplete_tasks =
        repository::get_incomplete_tasks_before_date(&conn, &today).map_err(|e| e.to_string())?;

    // Create new session
    let mut session =
        repository::create_session(&conn, &today).map_err(|e| e.to_string())?;

    // Carry forward incomplete tasks
    for task in &incomplete_tasks {
        repository::create_task(
            &conn,
            &session.id,
            &task.title,
            &task.description,
            &task.priority,
            task.estimated_duration_minutes,
            task.carry_forward_count + 1,
        )
        .map_err(|e| e.to_string())?;
    }

    session.status = "planning".to_string();
    Ok(session)
}

#[tauri::command]
pub fn get_today_session(db: tauri::State<Database>) -> Result<Option<Session>, String> {
    let conn = db.conn.lock().map_err(|e| e.to_string())?;
    repository::get_today_session(&conn).map_err(|e| e.to_string())
}

#[tauri::command]
pub fn get_session_by_id(
    db: tauri::State<Database>,
    session_id: String,
) -> Result<Option<Session>, String> {
    let conn = db.conn.lock().map_err(|e| e.to_string())?;
    repository::get_session_by_id(&conn, &session_id).map_err(|e| e.to_string())
}

#[tauri::command]
pub fn start_day(db: tauri::State<Database>, session_id: String) -> Result<(), String> {
    let conn = db.conn.lock().map_err(|e| e.to_string())?;
    repository::update_session_status(&conn, &session_id, "active").map_err(|e| e.to_string())?;
    Ok(())
}

#[tauri::command]
pub fn end_day(db: tauri::State<Database>, session_id: String) -> Result<(), String> {
    let conn = db.conn.lock().map_err(|e| e.to_string())?;
    repository::update_session_status(&conn, &session_id, "completed").map_err(|e| e.to_string())?;
    Ok(())
}

// ─── Task Commands ──────────────────────────────────────────────────────────

#[tauri::command]
pub fn create_task(
    db: tauri::State<Database>,
    session_id: String,
    title: String,
    description: String,
    priority: String,
    estimated_duration_minutes: i32,
) -> Result<Task, String> {
    let conn = db.conn.lock().map_err(|e| e.to_string())?;
    repository::create_task(&conn, &session_id, &title, &description, &priority, estimated_duration_minutes, 0)
        .map_err(|e| e.to_string())
}

#[tauri::command]
pub fn get_tasks_by_session(
    db: tauri::State<Database>,
    session_id: String,
) -> Result<Vec<Task>, String> {
    let conn = db.conn.lock().map_err(|e| e.to_string())?;
    repository::get_tasks_by_session(&conn, &session_id).map_err(|e| e.to_string())
}

#[tauri::command]
pub fn update_task(
    db: tauri::State<Database>,
    task: Task,
) -> Result<(), String> {
    let conn = db.conn.lock().map_err(|e| e.to_string())?;
    repository::update_task(&conn, &task).map_err(|e| e.to_string())
}

#[tauri::command]
pub fn update_task_status(
    db: tauri::State<Database>,
    task_id: String,
    status: String,
) -> Result<(), String> {
    let conn = db.conn.lock().map_err(|e| e.to_string())?;
    repository::update_task_status(&conn, &task_id, &status).map_err(|e| e.to_string())
}

#[tauri::command]
pub fn delete_task(db: tauri::State<Database>, task_id: String) -> Result<(), String> {
    let conn = db.conn.lock().map_err(|e| e.to_string())?;
    repository::delete_task(&conn, &task_id).map_err(|e| e.to_string())
}

#[tauri::command]
pub fn reorder_tasks(
    db: tauri::State<Database>,
    task_ids: Vec<String>,
) -> Result<(), String> {
    let conn = db.conn.lock().map_err(|e| e.to_string())?;
    repository::reorder_tasks(&conn, &task_ids).map_err(|e| e.to_string())
}

#[tauri::command]
pub fn get_incomplete_tasks_before_date(
    db: tauri::State<Database>,
    date: String,
) -> Result<Vec<Task>, String> {
    let conn = db.conn.lock().map_err(|e| e.to_string())?;
    repository::get_incomplete_tasks_before_date(&conn, &date).map_err(|e| e.to_string())
}

// ─── Time Entry Commands ────────────────────────────────────────────────────

#[tauri::command]
pub fn start_task_timer(
    db: tauri::State<Database>,
    task_id: String,
) -> Result<TimeEntry, String> {
    let conn = db.conn.lock().map_err(|e| e.to_string())?;

    // Stop any active timer for this task
    if let Some(active) = repository::get_active_time_entry(&conn, &task_id).map_err(|e| e.to_string())? {
        repository::stop_time_entry(&conn, &active.id).map_err(|e| e.to_string())?;
    }

    // Update task status to active
    repository::update_task_status(&conn, &task_id, "active").map_err(|e| e.to_string())?;

    // Start new time entry
    repository::start_time_entry(&conn, &task_id).map_err(|e| e.to_string())
}

#[tauri::command]
pub fn stop_task_timer(
    db: tauri::State<Database>,
    task_id: String,
) -> Result<i32, String> {
    let conn = db.conn.lock().map_err(|e| e.to_string())?;

    if let Some(active) = repository::get_active_time_entry(&conn, &task_id).map_err(|e| e.to_string())? {
        let entry = repository::stop_time_entry(&conn, &active.id).map_err(|e| e.to_string())?;
        let minutes = entry.duration_minutes.unwrap_or(0);

        // Update actual duration on task
        let total_minutes = get_total_actual_minutes(&conn, &task_id)?;
        repository::update_task_actual_duration(&conn, &task_id, total_minutes).map_err(|e| e.to_string())?;

        Ok(minutes)
    } else {
        Ok(0)
    }
}

#[tauri::command]
pub fn pause_task_timer(
    db: tauri::State<Database>,
    task_id: String,
) -> Result<i32, String> {
    let conn = db.conn.lock().map_err(|e| e.to_string())?;

    if let Some(active) = repository::get_active_time_entry(&conn, &task_id).map_err(|e| e.to_string())? {
        let entry = repository::stop_time_entry(&conn, &active.id).map_err(|e| e.to_string())?;
        let minutes = entry.duration_minutes.unwrap_or(0);

        // Update task status to paused
        repository::update_task_status(&conn, &task_id, "paused").map_err(|e| e.to_string())?;

        // Update actual duration
        let total_minutes = get_total_actual_minutes(&conn, &task_id)?;
        repository::update_task_actual_duration(&conn, &task_id, total_minutes).map_err(|e| e.to_string())?;

        Ok(minutes)
    } else {
        Ok(0)
    }
}

#[tauri::command]
pub fn get_active_time_entry(
    db: tauri::State<Database>,
    task_id: String,
) -> Result<Option<TimeEntry>, String> {
    let conn = db.conn.lock().map_err(|e| e.to_string())?;
    repository::get_active_time_entry(&conn, &task_id).map_err(|e| e.to_string())
}

fn get_total_actual_minutes(conn: &rusqlite::Connection, task_id: &str) -> Result<i32, String> {
    let entries = repository::get_task_time_entries(conn, task_id).map_err(|e| e.to_string())?;
    Ok(entries.iter().filter_map(|e| e.duration_minutes).sum())
}

// ─── Reflection Commands ────────────────────────────────────────────────────

#[tauri::command]
pub fn save_reflection(
    db: tauri::State<Database>,
    session_id: String,
    went_well: String,
    went_wrong: String,
    improve: String,
) -> Result<Reflection, String> {
    let conn = db.conn.lock().map_err(|e| e.to_string())?;
    repository::upsert_reflection(&conn, &session_id, &went_well, &went_wrong, &improve)
        .map_err(|e| e.to_string())
}

#[tauri::command]
pub fn get_reflection(
    db: tauri::State<Database>,
    session_id: String,
) -> Result<Option<Reflection>, String> {
    let conn = db.conn.lock().map_err(|e| e.to_string())?;
    repository::get_reflection_by_session(&conn, &session_id).map_err(|e| e.to_string())
}

// ─── Markdown Commands ──────────────────────────────────────────────────────

#[tauri::command]
pub fn generate_daily_note(
    db: tauri::State<Database>,
    session_id: String,
) -> Result<String, String> {
    let conn = db.conn.lock().map_err(|e| e.to_string())?;

    let session = repository::get_session_by_id(&conn, &session_id)
        .map_err(|e| e.to_string())?
        .ok_or_else(|| "Session not found".to_string())?;

    let all_tasks = repository::get_tasks_by_session(&conn, &session_id)
        .map_err(|e| e.to_string())?;

    let reflection = repository::get_reflection_by_session(&conn, &session_id)
        .map_err(|e| e.to_string())?
        .unwrap_or(Reflection {
            id: String::new(),
            session_id: session_id.clone(),
            went_well: String::new(),
            went_wrong: String::new(),
            improve: String::new(),
            created_at: String::new(),
            updated_at: String::new(),
        });

    let settings = repository::get_settings(&conn).map_err(|e| e.to_string())?;

    let date = chrono::NaiveDate::parse_from_str(&session.date, "%Y-%m-%d")
        .map_err(|e| format!("Invalid date: {}", e))?;

    let completed: Vec<&Task> = all_tasks.iter().filter(|t| t.status == "completed").collect();
    let carried: Vec<&Task> = all_tasks
        .iter()
        .filter(|t| t.status == "pending" || t.status == "active" || t.status == "paused")
        .collect();
    let cancelled: Vec<&Task> = all_tasks.iter().filter(|t| t.status == "cancelled").collect();

    let content = markdown::generate_daily_note(
        &date,
        &completed.iter().map(|t| (*t).clone()).collect::<Vec<_>>(),
        &carried.iter().map(|t| (*t).clone()).collect::<Vec<_>>(),
        &cancelled.iter().map(|t| (*t).clone()).collect::<Vec<_>>(),
        &all_tasks,
        &reflection,
    );

    let file_path = markdown::write_daily_note(&settings.obsidian_vault_path, &date, &content)?;

    Ok(file_path)
}

// ─── Settings Commands ──────────────────────────────────────────────────────

#[tauri::command]
pub fn get_settings(db: tauri::State<Database>) -> Result<Settings, String> {
    let conn = db.conn.lock().map_err(|e| e.to_string())?;
    repository::get_settings(&conn).map_err(|e| e.to_string())
}

#[tauri::command]
pub fn update_settings(
    db: tauri::State<Database>,
    settings: Settings,
) -> Result<(), String> {
    let conn = db.conn.lock().map_err(|e| e.to_string())?;
    repository::update_settings(&conn, &settings).map_err(|e| e.to_string())
}
