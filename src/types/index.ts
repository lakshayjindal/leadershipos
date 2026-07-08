export type Priority = "urgent-important" | "important" | "urgent";

export type TaskStatus = "pending" | "active" | "paused" | "completed" | "skipped" | "cancelled";

export type SessionStatus = "planning" | "active" | "completed";

export interface Task {
  id: string;
  session_id: string;
  title: string;
  description: string;
  priority: Priority;
  estimated_duration_minutes: number;
  actual_duration_minutes: number | null;
  status: TaskStatus;
  carry_forward_count: number;
  sort_order: number;
  created_at: string;
  updated_at: string;
}

export interface CreateTaskInput {
  title: string;
  description?: string;
  priority: Priority;
  estimated_duration_minutes: number;
}

export interface UpdateTaskInput {
  title?: string;
  description?: string;
  priority?: Priority;
  estimated_duration_minutes?: number;
  status?: TaskStatus;
  sort_order?: number;
}

export interface TimeEntry {
  id: string;
  task_id: string;
  start_time: string;
  end_time: string | null;
  duration_minutes: number | null;
  created_at: string;
}

export interface Reflection {
  id: string;
  session_id: string;
  went_well: string;
  went_wrong: string;
  improve: string;
  created_at: string;
  updated_at: string;
}

export interface Session {
  id: string;
  date: string;
  status: SessionStatus;
  created_at: string;
  updated_at: string;
}

export interface SessionWithDetails extends Session {
  tasks: Task[];
  reflection: Reflection | null;
  total_estimated_minutes: number;
  total_actual_minutes: number | null;
  completed_tasks: number;
  total_tasks: number;
}

export interface Settings {
  obsidian_vault_path: string;
  reminder_interval_minutes: number;
  default_task_duration_minutes: number;
  working_hours_start: string;
  working_hours_end: string;
  theme: "system" | "light" | "dark";
}

export interface DashboardStats {
  current_task: Task | null;
  today_progress: number;
  completed_tasks: Task[];
  pending_tasks: Task[];
  estimated_remaining_minutes: number;
  elapsed_minutes: number;
  paused_minutes: number;
}
