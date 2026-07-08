mod commands;
mod database;
mod markdown;
mod models;
mod notifications;
mod scheduler;

use database::Database;
use std::path::PathBuf;

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    let app_data_dir = dirs::data_dir()
        .unwrap_or_else(|| PathBuf::from("."))
        .join("leadership-os");

    std::fs::create_dir_all(&app_data_dir).expect("Failed to create app data directory");

    let db_path = app_data_dir.join("leadership-os.db");
    let db = Database::new(db_path.to_str().unwrap())
        .expect("Failed to initialize database");

    tauri::Builder::default()
        .plugin(tauri_plugin_opener::init())
        .plugin(tauri_plugin_notification::init())
        .manage(db)
        .invoke_handler(tauri::generate_handler![
            // Session
            commands::start_session,
            commands::get_today_session,
            commands::get_session_by_id,
            commands::start_day,
            commands::end_day,
            // Tasks
            commands::create_task,
            commands::get_tasks_by_session,
            commands::update_task,
            commands::update_task_status,
            commands::delete_task,
            commands::reorder_tasks,
            commands::get_incomplete_tasks_before_date,
            // Time entries
            commands::start_task_timer,
            commands::stop_task_timer,
            commands::pause_task_timer,
            commands::get_active_time_entry,
            // Reflection
            commands::save_reflection,
            commands::get_reflection,
            // Markdown
            commands::generate_daily_note,
            // Settings
            commands::get_settings,
            commands::update_settings,
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
