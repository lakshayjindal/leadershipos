use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Reflection {
    pub id: String,
    pub session_id: String,
    pub went_well: String,
    pub went_wrong: String,
    pub improve: String,
    pub created_at: String,
    pub updated_at: String,
}
