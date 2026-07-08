use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Settings {
    pub id: String,
    pub obsidian_vault_path: String,
    pub reminder_interval_minutes: i32,
    pub default_task_duration_minutes: i32,
    pub working_hours_start: String,
    pub working_hours_end: String,
    pub theme: String, // "system", "light", "dark"
    pub created_at: String,
    pub updated_at: String,
}
