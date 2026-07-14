use tauri::State;
use crate::db::Database;
use crate::journal_engine::JournalEngine;
use crate::models::*;

// ─── Day Commands ──────────────────────────────────────────────────

#[tauri::command]
pub fn get_today(db: State<Database>) -> Result<Day, String> {
    db.get_or_create_today().map_err(|e| e.to_string())
}

#[tauri::command]
pub fn get_today_status(db: State<Database>) -> Result<TodayStatus, String> {
    let day = db.get_or_create_today().map_err(|e| e.to_string())?;
    let tasks = db.get_tasks_by_day(&day.id).map_err(|e| e.to_string())?;
    let (state, active_task_id, _) = db.get_app_state().map_err(|e| e.to_string())?;

    let active_task = active_task_id.as_ref().and_then(|id| {
        tasks.iter().find(|t| t.id == *id).cloned()
    });

    let current_session = active_task_id.as_ref().and_then(|id| {
        db.get_active_session(id).ok().flatten()
    });

    let summary = db.get_daily_summary(&day.id).ok().flatten();

    let pending_tasks = tasks.iter().filter(|t| t.status == TaskStatus::Pending).count() as i32;
    let completed_tasks = tasks.iter().filter(|t| t.status == TaskStatus::Completed).count() as i32;

    Ok(TodayStatus {
        state,
        active_task,
        current_session,
        day: Some(day),
        daily_summary: summary,
        pending_tasks,
        completed_tasks,
    })
}

// ─── Task Commands ─────────────────────────────────────────────────

#[tauri::command]
pub fn create_task(db: State<Database>, day_id: String, req: CreateTaskRequest) -> Result<Task, String> {
    db.create_task(&day_id, &req).map_err(|e| e.to_string())
}

#[tauri::command]
pub fn get_tasks(db: State<Database>, day_id: String) -> Result<Vec<Task>, String> {
    db.get_tasks_by_day(&day_id).map_err(|e| e.to_string())
}

#[tauri::command]
pub fn update_task(db: State<Database>, req: UpdateTaskRequest) -> Result<(), String> {
    db.update_task(&req).map_err(|e| e.to_string())
}

#[tauri::command]
pub fn set_task_status(db: State<Database>, task_id: String, status: String) -> Result<(), String> {
    db.set_task_status(&task_id, &status).map_err(|e| e.to_string())
}

#[tauri::command]
pub fn reorder_tasks(db: State<Database>, task_ids: Vec<String>) -> Result<(), String> {
    db.reorder_tasks(&task_ids).map_err(|e| e.to_string())
}

// ─── Timer Commands ────────────────────────────────────────────────

#[tauri::command]
pub fn start_task(db: State<Database>, task_id: String) -> Result<WorkSession, String> {
    let (_, current_active, _) = db.get_app_state().map_err(|e| e.to_string())?;
    if let Some(active_id) = current_active {
        if active_id != task_id {
            end_work_for_task_internal(&db, &active_id)?;
        }
    }

    db.set_task_status(&task_id, "active").map_err(|e| e.to_string())?;
    db.set_app_state("working", Some(&task_id), None).map_err(|e| e.to_string())?;
    db.start_work_session(&task_id).map_err(|e| e.to_string())
}

fn end_work_for_task_internal(db: &Database, task_id: &str) -> Result<(), String> {
    if let Ok(Some(session)) = db.get_active_session(task_id) {
        db.end_work_session(&session.id).map_err(|e| e.to_string())?;
    }
    db.set_task_status(task_id, "paused").map_err(|e| e.to_string())
}

#[tauri::command]
pub fn pause_task(db: State<Database>, task_id: String) -> Result<(), String> {
    if let Ok(Some(session)) = db.get_active_session(&task_id) {
        db.end_work_session(&session.id).map_err(|e| e.to_string())?;
    }
    db.set_task_status(&task_id, "paused").map_err(|e| e.to_string())?;
    db.set_app_state("idle", Some(&task_id), None).map_err(|e| e.to_string())?;
    Ok(())
}

#[tauri::command]
pub fn complete_task(db: State<Database>, task_id: String) -> Result<(), String> {
    if let Ok(Some(session)) = db.get_active_session(&task_id) {
        db.end_work_session(&session.id).map_err(|e| e.to_string())?;
    }
    db.set_task_status(&task_id, "completed").map_err(|e| e.to_string())?;
    db.set_app_state("working", None, None).map_err(|e| e.to_string())?;
    Ok(())
}

#[tauri::command]
pub fn get_active_session(db: State<Database>, task_id: String) -> Result<Option<WorkSession>, String> {
    db.get_active_session(&task_id).map_err(|e| e.to_string())
}

// ─── Break Commands ────────────────────────────────────────────────

#[tauri::command]
pub fn start_break(db: State<Database>, day_id: String, break_type: String) -> Result<BreakSession, String> {
    let (_, active_task_id, _) = db.get_app_state().map_err(|e| e.to_string())?;
    if let Some(task_id) = active_task_id {
        if let Ok(Some(session)) = db.get_active_session(&task_id) {
            db.end_work_session(&session.id).map_err(|e| e.to_string())?;
        }
    }
    db.set_app_state("break", None, None).map_err(|e| e.to_string())?;
    db.start_break(&day_id, &break_type).map_err(|e| e.to_string())
}

#[tauri::command]
pub fn end_break(db: State<Database>, break_id: String) -> Result<BreakSession, String> {
    let result = db.end_break(&break_id).map_err(|e| e.to_string())?;
    db.set_app_state("working", None, None).map_err(|e| e.to_string())?;
    Ok(result)
}

#[tauri::command]
pub fn get_active_break(db: State<Database>, day_id: String) -> Result<Option<BreakSession>, String> {
    db.get_active_break(&day_id).map_err(|e| e.to_string())
}

// ─── Reflection Commands ──────────────────────────────────────────

#[tauri::command]
pub fn save_reflection(db: State<Database>, day_id: String, accomplishments: String, challenges: String, tomorrow_task: String) -> Result<Reflection, String> {
    db.save_reflection(&day_id, &accomplishments, &challenges, &tomorrow_task).map_err(|e| e.to_string())
}

#[tauri::command]
pub fn get_reflection(db: State<Database>, day_id: String) -> Result<Option<Reflection>, String> {
    db.get_reflection(&day_id).map_err(|e| e.to_string())
}

// ─── Journal Commands ──────────────────────────────────────────────

#[tauri::command]
pub fn generate_journal(db: State<Database>, day_id: String) -> Result<String, String> {
    let config = db.get_config().map_err(|e| e.to_string())?;
    JournalEngine::generate_journal(
        &db,
        &day_id,
        config.markdown_vault_path.as_deref(),
        &config.journal_directory,
    )
}

// ─── Search Commands ──────────────────────────────────────────────

#[tauri::command]
pub fn search(db: State<Database>, query: String) -> Result<Vec<Task>, String> {
    db.search_tasks(&query, 50).map_err(|e| e.to_string())
}

// ─── Carry Forward Commands ───────────────────────────────────────

#[tauri::command]
pub fn get_carry_forward_tasks(db: State<Database>) -> Result<Vec<Task>, String> {
    db.get_carry_forward_tasks().map_err(|e| e.to_string())
}

#[tauri::command]
pub fn carry_forward_task(db: State<Database>, task_id: String, today_id: String) -> Result<Task, String> {
    db.carry_forward_task(&task_id, &today_id).map_err(|e| e.to_string())
}

#[tauri::command]
pub fn auto_carry_forward_all(db: State<Database>) -> Result<Vec<Task>, String> {
    let day = db.get_or_create_today().map_err(|e| e.to_string())?;
    db.auto_carry_forward_all(&day.id).map_err(|e| e.to_string())
}

// ─── Shutdown Command ──────────────────────────────────────────────

#[tauri::command]
pub fn shutdown_day(db: State<Database>, day_id: String, generate_journal: bool) -> Result<Option<String>, String> {
    if generate_journal {
        let config = db.get_config().map_err(|e| e.to_string())?;
        let journal = crate::journal_engine::JournalEngine::generate_journal(
            &db,
            &day_id,
            config.markdown_vault_path.as_deref(),
            &config.journal_directory,
        ).ok();
        db.shutdown_day(&day_id).map_err(|e| e.to_string())?;
        Ok(journal)
    } else {
        db.shutdown_day(&day_id).map_err(|e| e.to_string())?;
        Ok(None)
    }
}

// ─── History Commands ─────────────────────────────────────────────

#[tauri::command]
pub fn get_previous_days(db: State<Database>, limit: Option<i32>) -> Result<Vec<(Day, Option<DailySummary>)>, String> {
    db.get_previous_days(limit.unwrap_or(30)).map_err(|e| e.to_string())
}

// ─── Configuration Commands ───────────────────────────────────────

#[tauri::command]
pub fn get_config(db: State<Database>) -> Result<AppConfiguration, String> {
    db.get_config().map_err(|e| e.to_string())
}

#[tauri::command]
pub fn save_config(db: State<Database>, config: AppConfiguration) -> Result<(), String> {
    db.save_config(&config).map_err(|e| e.to_string())
}

// ─── App State Commands ───────────────────────────────────────────

#[tauri::command]
pub fn get_app_state_cmd(db: State<Database>) -> Result<(String, Option<String>, Option<String>), String> {
    db.get_app_state().map_err(|e| e.to_string())
}

#[tauri::command]
pub fn set_app_state_cmd(db: State<Database>, state: String, active_task_id: Option<String>, current_day_id: Option<String>) -> Result<(), String> {
    db.set_app_state(&state, active_task_id.as_deref(), current_day_id.as_deref()).map_err(|e| e.to_string())
}


