use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Session {
    pub id: String,
    pub date: String,
    pub status: String, // "planning", "active", "completed"
    pub created_at: String,
    pub updated_at: String,
}
