use crate::db::Database;
use crate::models::*;
use std::path::PathBuf;

pub struct JournalEngine;

impl JournalEngine {
    pub fn generate_journal(db: &Database, day_id: &str, vault_path: Option<&str>, journal_dir: &str) -> Result<String, String> {
        let day = db.get_or_create_today().map_err(|e| e.to_string())?;
        let tasks = db.get_tasks_by_day(day_id).map_err(|e| e.to_string())?;
        let summary = db.generate_daily_summary(day_id).map_err(|e| e.to_string())?;
        let reflection = db.get_reflection(day_id).map_err(|e| e.to_string())?;

        let date = chrono::NaiveDate::parse_from_str(&day.date, "%Y-%m-%d").unwrap_or_else(|_| chrono::Local::now().date_naive());
        let day_name = date.format("%A").to_string();
        let formatted_date = date.format("%B %d, %Y").to_string();

        let start_time = day.start_time.as_deref().unwrap_or("--:--");
        let end_time = day.end_time.as_deref().unwrap_or("--:--");

        let completed: Vec<&Task> = tasks.iter().filter(|t| t.status == TaskStatus::Completed).collect();
        let carried: Vec<&Task> = tasks.iter().filter(|t| t.status == TaskStatus::CarriedForward || t.status == TaskStatus::Pending).collect();
        let planned: Vec<&Task> = tasks.iter().filter(|t| t.status != TaskStatus::Archived && t.status != TaskStatus::Deleted).collect();

        let focus_hours = summary.total_focus_seconds / 3600;
        let focus_minutes = (summary.total_focus_seconds % 3600) / 60;
        let break_hours = summary.total_break_seconds / 3600;
        let break_minutes = (summary.total_break_seconds % 3600) / 60;

        let mut journal = String::new();
        journal.push_str(&format!("# {}, {}\n\n", day_name, formatted_date));
        journal.push_str(&format!("**Started:** {}  \n", start_time));
        journal.push_str(&format!("**Finished:** {}  \n\n", end_time));
        journal.push_str("---\n\n");

        journal.push_str("## Summary\n\n");
        journal.push_str(&format!("- **Planned Tasks:** {}\n", summary.total_planned));
        journal.push_str(&format!("- **Completed:** {}\n", summary.completed));
        journal.push_str(&format!("- **Carried Forward:** {}\n", summary.carried_forward));
        journal.push_str(&format!("- **Focus Time:** {}h {}m\n", focus_hours, focus_minutes));
        journal.push_str(&format!("- **Break Time:** {}h {}m\n\n", break_hours, break_minutes));
        journal.push_str("---\n\n");

        journal.push_str("## Planned Tasks\n\n");
        for task in &planned {
            let checked = if task.status == TaskStatus::Completed { "x" } else { " " };
            journal.push_str(&format!("- [{}] {}  \n", checked, task.title));
            if task.priority != Priority::Medium {
                journal.push_str(&format!("  _Priority: {}_  \n", task.priority.as_str()));
            }
        }
        journal.push_str("\n---\n\n");

        journal.push_str("## Completed Work\n\n");
        for task in &completed {
            journal.push_str(&format!("- [x] **{}**", task.title));
            if let Some(ref completed_at) = task.completed_at {
                journal.push_str(&format!(" ({})", &completed_at[11..16]));
            }
            journal.push_str("  \n");
            if let Some(ref notes) = task.notes {
                if !notes.is_empty() {
                    journal.push_str(&format!("  _{}_  \n", notes));
                }
            }
        }
        journal.push_str("\n---\n\n");

        journal.push_str("## Timeline\n\n");
        // Collect all events for timeline
        let mut events: Vec<(String, String)> = Vec::new();
        for task in &tasks {
            if let Some(ref activated) = task.activated_at {
                events.push((activated.clone(), format!("Started **{}**", task.title)));
            }
            if let Some(ref completed_at) = task.completed_at {
                events.push((completed_at.clone(), format!("Completed **{}**", task.title)));
            }
        }
        // Add break events
        // (Would need to load break sessions here too)
        events.sort_by(|a, b| a.0.cmp(&b.0));

        for (timestamp, description) in &events {
            let time = &timestamp[11..16];
            journal.push_str(&format!("{} — {}\n", time, description));
        }
        journal.push_str("\n---\n\n");

        journal.push_str("## Work Statistics\n\n");
        journal.push_str(&format!("| Metric | Value |\n"));
        journal.push_str(&format!("|--------|-------|\n"));
        journal.push_str(&format!("| Total Focus Time | {}h {}m |\n", focus_hours, focus_minutes));
        journal.push_str(&format!("| Total Break Time | {}h {}m |\n", break_hours, break_minutes));
        journal.push_str(&format!("| Tasks Planned | {} |\n", summary.total_planned));
        journal.push_str(&format!("| Tasks Completed | {} |\n", summary.completed));
        journal.push_str(&format!("| Work Sessions | {} |\n", summary.session_count));
        journal.push_str(&format!("| Longest Session | {}m |\n", summary.longest_session_seconds / 60));
        journal.push_str(&format!("| Completion Rate | {:.0}% |\n\n", summary.completion_percentage));
        journal.push_str("---\n\n");

        journal.push_str("## Reflection\n\n");
        if let Some(ref refl) = reflection {
            if let Some(ref acc) = refl.accomplishments {
                if !acc.is_empty() {
                    journal.push_str("### What did I accomplish?\n\n");
                    journal.push_str(acc);
                    journal.push_str("\n\n");
                }
            }
            if let Some(ref chal) = refl.challenges {
                if !chal.is_empty() {
                    journal.push_str("### What slowed me down?\n\n");
                    journal.push_str(chal);
                    journal.push_str("\n\n");
                }
            }
            if let Some(ref tomorrow) = refl.tomorrow_first_task {
                if !tomorrow.is_empty() {
                    journal.push_str("### First task tomorrow\n\n");
                    journal.push_str(tomorrow);
                    journal.push_str("\n\n");
                }
            }
        }

        if !carried.is_empty() {
            journal.push_str("---\n\n## Carry Forward\n\n");
            for task in &carried {
                journal.push_str(&format!("- [ ] **{}**  \n", task.title));
            }
        }

        // Write to file
        let base_path = vault_path.map(PathBuf::from).unwrap_or_else(|| {
            dirs::document_dir()
                .map(|p| p.join("Obsidian"))
                .unwrap_or_else(|| PathBuf::from("~/Documents/Obsidian"))
        });
        let journal_path = base_path.join(journal_dir);
        std::fs::create_dir_all(&journal_path).ok();
        let filename = format!("{}.md", day.date);
        let filepath = journal_path.join(&filename);
        std::fs::write(&filepath, &journal).ok();

        Ok(journal)
    }
}
