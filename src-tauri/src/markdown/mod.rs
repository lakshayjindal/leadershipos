use crate::models::reflection::Reflection;
use crate::models::task::Task;
use chrono::NaiveDate;
use std::fs;
use std::path::PathBuf;

pub fn generate_daily_note(
    date: &NaiveDate,
    completed_tasks: &[Task],
    carried_forward_tasks: &[Task],
    cancelled_tasks: &[Task],
    all_tasks: &[Task],
    reflection: &Reflection,
) -> String {
    let date_str = date.format("%Y-%m-%d").to_string();
    let mut md = String::new();

    md.push_str(&format!("# {}\n\n", date_str));

    // Summary
    md.push_str("## Summary\n\n");
    md.push_str(&format!(
        "- **Tasks Completed:** {}\n",
        completed_tasks.len()
    ));
    md.push_str(&format!(
        "- **Tasks Carried Forward:** {}\n",
        carried_forward_tasks.len()
    ));
    md.push_str(&format!(
        "- **Tasks Cancelled:** {}\n\n",
        cancelled_tasks.len()
    ));

    // Tasks completed
    md.push_str("## Tasks Completed\n\n");
    if completed_tasks.is_empty() {
        md.push_str("_No tasks completed._\n\n");
    } else {
        for task in completed_tasks {
            md.push_str(&format!("- [x] **{}**", task.title));
            if let Some(actual) = task.actual_duration_minutes {
                md.push_str(&format!(" ({}m)", actual));
            }
            md.push('\n');
        }
        md.push('\n');
    }

    // Tasks carried forward
    md.push_str("## Tasks Carried Forward\n\n");
    if carried_forward_tasks.is_empty() {
        md.push_str("_No tasks carried forward._\n\n");
    } else {
        for task in carried_forward_tasks {
            md.push_str(&format!(
                "- [ ] **{}** (carried forward {}x)\n",
                task.title, task.carry_forward_count
            ));
        }
        md.push('\n');
    }

    // Cancelled tasks
    if !cancelled_tasks.is_empty() {
        md.push_str("## Tasks Cancelled\n\n");
        for task in cancelled_tasks {
            md.push_str(&format!("- ~~{}~~\n", task.title));
        }
        md.push('\n');
    }

    // Priority matrix
    md.push_str("## Priority Matrix\n\n");

    let urgent_important: Vec<&Task> = all_tasks
        .iter()
        .filter(|t| t.priority == "urgent-important")
        .collect();
    let important: Vec<&Task> = all_tasks
        .iter()
        .filter(|t| t.priority == "important")
        .collect();
    let urgent: Vec<&Task> = all_tasks
        .iter()
        .filter(|t| t.priority == "urgent")
        .collect();

    if !urgent_important.is_empty() {
        md.push_str("### Urgent & Important\n\n");
        for task in &urgent_important {
            let status = if task.status == "completed" { "[x]" } else { "[ ]" };
            md.push_str(&format!("- {} {}\n", status, task.title));
        }
        md.push('\n');
    }

    if !important.is_empty() {
        md.push_str("### Important\n\n");
        for task in &important {
            let status = if task.status == "completed" { "[x]" } else { "[ ]" };
            md.push_str(&format!("- {} {}\n", status, task.title));
        }
        md.push('\n');
    }

    if !urgent.is_empty() {
        md.push_str("### Urgent\n\n");
        for task in &urgent {
            let status = if task.status == "completed" { "[x]" } else { "[ ]" };
            md.push_str(&format!("- {} {}\n", status, task.title));
        }
        md.push('\n');
    }

    // Estimated vs actual time
    md.push_str("## Estimated vs Actual Time\n\n");
    md.push_str("| Task | Priority | Estimated | Actual |\n");
    md.push_str("|------|----------|-----------|--------|\n");

    for task in all_tasks {
        let priority_label = match task.priority.as_str() {
            "urgent-important" => "Urgent & Important",
            "important" => "Important",
            "urgent" => "Urgent",
            _ => &task.priority,
        };
        let actual = task
            .actual_duration_minutes
            .map(|m| format!("{}m", m))
            .unwrap_or_else(|| "-".to_string());
        md.push_str(&format!(
            "| {} | {} | {}m | {} |\n",
            task.title, priority_label, task.estimated_duration_minutes, actual
        ));
    }
    md.push('\n');

    // Reflection
    md.push_str("## Reflection\n\n");

    md.push_str("### What Went Well\n\n");
    if reflection.went_well.is_empty() {
        md.push_str("_No reflection recorded._\n\n");
    } else {
        md.push_str(&format!("{}\n\n", reflection.went_well));
    }

    md.push_str("### What Went Wrong\n\n");
    if reflection.went_wrong.is_empty() {
        md.push_str("_No reflection recorded._\n\n");
    } else {
        md.push_str(&format!("{}\n\n", reflection.went_wrong));
    }

    md.push_str("### What Could Be Improved\n\n");
    if reflection.improve.is_empty() {
        md.push_str("_No reflection recorded._\n\n");
    } else {
        md.push_str(&format!("{}\n\n", reflection.improve));
    }

    md.push_str("---\n\n");
    md.push_str("_Generated automatically by Leadership OS._\n");

    md
}

pub fn write_daily_note(vault_path: &str, date: &NaiveDate, content: &str) -> Result<String, String> {
    let expanded_path = shellexpand::tilde(vault_path).to_string();
    let dir = PathBuf::from(&expanded_path);

    // Create directory if it doesn't exist
    fs::create_dir_all(&dir).map_err(|e| format!("Failed to create directory: {}", e))?;

    let file_name = format!("{}.md", date.format("%Y-%m-%d"));
    let file_path = dir.join(&file_name);

    fs::write(&file_path, content)
        .map_err(|e| format!("Failed to write file: {}", e))?;

    Ok(file_path.to_string_lossy().to_string())
}
