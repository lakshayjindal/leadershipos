use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Task {
    pub id: String,
    pub session_id: String,
    pub title: String,
    pub description: String,
    pub priority: String, // "urgent-important", "important", "urgent"
    pub estimated_duration_minutes: i32,
    pub actual_duration_minutes: Option<i32>,
    pub status: String, // "pending", "active", "paused", "completed", "skipped", "cancelled"
    pub carry_forward_count: i32,
    pub sort_order: i32,
    pub created_at: String,
    pub updated_at: String,
}
