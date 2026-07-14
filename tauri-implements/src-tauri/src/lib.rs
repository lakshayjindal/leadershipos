mod commands;
mod db;
mod event_bus;
mod journal_engine;
mod models;

use db::Database;
use tauri::Manager;

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    // Initialize logging
    tracing_subscriber::fmt()
        .with_target(false)
        .with_level(true)
        .with_file(true)
        .with_line_number(true)
        .init();

    tracing::info!("Leadership OS starting...");

    tauri::Builder::default()
        .plugin(tauri_plugin_notification::init())
        .plugin(tauri_plugin_shell::init())
        .plugin(tauri_plugin_dialog::init())
        .plugin(tauri_plugin_fs::init())
        .setup(|app| {
            let app_data_dir = app.path().app_data_dir().expect("Failed to get app data dir");
            tracing::info!("App data dir: {:?}", app_data_dir);

            match Database::new(app_data_dir) {
                Ok(database) => {
                    tracing::info!("Database initialized successfully");
                    app.manage(database);
                },
                Err(e) => {
                    tracing::error!("Failed to initialize database: {:?}", e);
                    return Err(Box::new(e).into());
                }
            }

            Ok(())
        })
        .invoke_handler(tauri::generate_handler![
            // Day commands
            commands::get_today,
            commands::get_today_status,
            // Task commands
            commands::create_task,
            commands::get_tasks,
            commands::update_task,
            commands::set_task_status,
            commands::reorder_tasks,
            // Timer commands
            commands::start_task,
            commands::pause_task,
            commands::complete_task,
            commands::get_active_session,
            // Break commands
            commands::start_break,
            commands::end_break,
            commands::get_active_break,
            // Reflection commands
            commands::save_reflection,
            commands::get_reflection,
            // Journal commands
            commands::generate_journal,
            // Search commands
            commands::search,
            // Carry forward commands
            commands::get_carry_forward_tasks,
            commands::carry_forward_task,
            commands::auto_carry_forward_all,
            // Shutdown command
            commands::shutdown_day,
            // Config commands
            commands::get_config,
            commands::save_config,
            // History commands
            commands::get_previous_days,
            // State commands
            commands::get_app_state_cmd,
            commands::set_app_state_cmd,
        ])
        .run(tauri::generate_context!())
        .expect("error while running Leadership OS");
}
