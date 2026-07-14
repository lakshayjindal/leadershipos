use serde::{Deserialize, Serialize};

// ─── Enums ──────────────────────────────────────────────────────────

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
#[serde(rename_all = "snake_case")]
pub enum TaskStatus {
    Pending,
    Active,
    Paused,
    Completed,
    Archived,
    Deleted,
    CarriedForward,
}

impl TaskStatus {
    #[allow(dead_code)]
    pub fn as_str(&self) -> &'static str {
        match self {
            TaskStatus::Pending => "pending",
            TaskStatus::Active => "active",
            TaskStatus::Paused => "paused",
            TaskStatus::Completed => "completed",
            TaskStatus::Archived => "archived",
            TaskStatus::Deleted => "deleted",
            TaskStatus::CarriedForward => "carried_forward",
        }
    }

    pub fn from_str(s: &str) -> Self {
        match s {
            "pending" => TaskStatus::Pending,
            "active" => TaskStatus::Active,
            "paused" => TaskStatus::Paused,
            "completed" => TaskStatus::Completed,
            "archived" => TaskStatus::Archived,
            "deleted" => TaskStatus::Deleted,
            "carried_forward" => TaskStatus::CarriedForward,
            _ => TaskStatus::Pending,
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
#[serde(rename_all = "snake_case")]
pub enum Priority {
    Critical,
    High,
    Medium,
    Low,
}

impl Priority {
    pub fn as_str(&self) -> &'static str {
        match self {
            Priority::Critical => "critical",
            Priority::High => "high",
            Priority::Medium => "medium",
            Priority::Low => "low",
        }
    }

    pub fn from_str(s: &str) -> Self {
        match s {
            "critical" => Priority::Critical,
            "high" => Priority::High,
            "medium" => Priority::Medium,
            "low" => Priority::Low,
            _ => Priority::Medium,
        }
    }

    #[allow(dead_code)]
    pub fn rank(&self) -> u8 {
        match self {
            Priority::Critical => 4,
            Priority::High => 3,
            Priority::Medium => 2,
            Priority::Low => 1,
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
#[allow(dead_code)]
pub enum BreakType {
    Lunch,
    Dinner,
    Tea,
    Meeting,
    Personal,
    Custom(String),
}

#[allow(dead_code)]
impl BreakType {
    pub fn as_str(&self) -> &'static str {
        match self {
            BreakType::Lunch => "lunch",
            BreakType::Dinner => "dinner",
            BreakType::Tea => "tea",
            BreakType::Meeting => "meeting",
            BreakType::Personal => "personal",
            BreakType::Custom(_) => "custom",
        }
    }

    pub fn from_str(s: &str) -> Self {
        match s {
            "lunch" => BreakType::Lunch,
            "dinner" => BreakType::Dinner,
            "tea" => BreakType::Tea,
            "meeting" => BreakType::Meeting,
            "personal" => BreakType::Personal,
            _ => BreakType::Custom(s.to_string()),
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
#[allow(dead_code)]
pub enum AppState {
    Startup,
    Planning,
    Working,
    Break,
    Idle,
    Review,
    Shutdown,
}

#[allow(dead_code)]
impl AppState {
    pub fn as_str(&self) -> &'static str {
        match self {
            AppState::Startup => "startup",
            AppState::Planning => "planning",
            AppState::Working => "working",
            AppState::Break => "break",
            AppState::Idle => "idle",
            AppState::Review => "review",
            AppState::Shutdown => "shutdown",
        }
    }

    pub fn from_str(s: &str) -> Self {
        match s {
            "startup" => AppState::Startup,
            "planning" => AppState::Planning,
            "working" => AppState::Working,
            "break" => AppState::Break,
            "idle" => AppState::Idle,
            "review" => AppState::Review,
            "shutdown" => AppState::Shutdown,
            _ => AppState::Idle,
        }
    }
}

// ─── Core Entities ─────────────────────────────────────────────────

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Task {
    pub id: String,
    pub day_id: String,
    pub title: String,
    pub description: Option<String>,
    pub priority: Priority,
    pub status: TaskStatus,
    pub deadline: Option<String>,
    pub estimated_duration_minutes: Option<i32>,
    pub actual_duration_seconds: i64,
    pub display_order: i32,
    pub notes: Option<String>,
    pub created_at: String,
    pub activated_at: Option<String>,
    pub completed_at: Option<String>,
    pub carry_forward_count: i32,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct WorkSession {
    pub id: String,
    pub task_id: String,
    pub start_time: String,
    pub end_time: Option<String>,
    pub duration_seconds: i64,
    pub paused_duration_seconds: i64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct BreakSession {
    pub id: String,
    pub day_id: String,
    pub break_type: String,
    pub start_time: String,
    pub end_time: Option<String>,
    pub duration_seconds: i64,
    pub notes: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Day {
    pub id: String,
    pub date: String,
    pub start_time: Option<String>,
    pub end_time: Option<String>,
    pub status: String,
    pub created_at: String,
    pub updated_at: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Reflection {
    pub id: String,
    pub day_id: String,
    pub accomplishments: Option<String>,
    pub challenges: Option<String>,
    pub tomorrow_first_task: Option<String>,
    pub additional_notes: Option<String>,
    pub completed_at: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DailySummary {
    pub id: String,
    pub day_id: String,
    pub total_planned: i32,
    pub completed: i32,
    pub carried_forward: i32,
    pub archived: i32,
    pub deleted_count: i32,
    pub total_focus_seconds: i64,
    pub total_break_seconds: i64,
    pub completion_percentage: f64,
    pub longest_session_seconds: i64,
    pub session_count: i32,
    pub generated_markdown_path: Option<String>,
    pub archived_at: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AppConfiguration {
    pub working_hours_start: String,
    pub working_hours_end: String,
    pub lunch_time: Option<String>,
    pub dinner_time: Option<String>,
    pub overlay_position: String,
    pub overlay_opacity: f64,
    pub theme: String,
    pub markdown_vault_path: Option<String>,
    pub journal_directory: String,
    pub notification_enabled: bool,
    pub startup_behavior: String,
    pub launch_at_startup: bool,
    pub deadline_reminder_minutes: i32,
    pub break_reminder_enabled: bool,
    pub short_break_duration: i32,
    pub long_break_duration: i32,
    pub sessions_before_long_break: i32,
}

impl Default for AppConfiguration {
    fn default() -> Self {
        Self {
            working_hours_start: "09:00".to_string(),
            working_hours_end: "18:00".to_string(),
            lunch_time: Some("13:00".to_string()),
            dinner_time: Some("19:30".to_string()),
            overlay_position: "bottom-right".to_string(),
            overlay_opacity: 0.85,
            theme: "dark".to_string(),
            markdown_vault_path: None,
            journal_directory: "Daily Notes".to_string(),
            notification_enabled: true,
            startup_behavior: "restore".to_string(),
            launch_at_startup: false,
            deadline_reminder_minutes: 30,
            break_reminder_enabled: true,
            short_break_duration: 5,
            long_break_duration: 15,
            sessions_before_long_break: 4,
        }
    }
}

// ─── Command Types ──────────────────────────────────────────────────

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CreateTaskRequest {
    pub title: String,
    pub description: Option<String>,
    pub priority: String,
    pub deadline: Option<String>,
    pub estimated_duration_minutes: Option<i32>,
    pub notes: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct UpdateTaskRequest {
    pub id: String,
    pub title: Option<String>,
    pub description: Option<String>,
    pub priority: Option<String>,
    pub deadline: Option<String>,
    pub estimated_duration_minutes: Option<i32>,
    pub notes: Option<String>,
    pub display_order: Option<i32>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TodayStatus {
    pub state: String,
    pub active_task: Option<Task>,
    pub current_session: Option<WorkSession>,
    pub day: Option<Day>,
    pub daily_summary: Option<DailySummary>,
    pub pending_tasks: i32,
    pub completed_tasks: i32,
}
