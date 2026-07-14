export type TaskStatus = 'pending' | 'active' | 'paused' | 'completed' | 'archived' | 'deleted' | 'carried_forward';
export type Priority = 'critical' | 'high' | 'medium' | 'low';
export type AppState = 'startup' | 'planning' | 'working' | 'break' | 'idle' | 'review' | 'shutdown';
export type BreakType = 'lunch' | 'dinner' | 'tea' | 'meeting' | 'personal' | 'custom';

export interface Task {
  id: string;
  day_id: string;
  title: string;
  description?: string | null;
  priority: Priority;
  status: TaskStatus;
  deadline?: string | null;
  estimated_duration_minutes?: number | null;
  actual_duration_seconds: number;
  display_order: number;
  notes?: string | null;
  created_at: string;
  activated_at?: string | null;
  completed_at?: string | null;
  carry_forward_count: number;
}

export interface WorkSession {
  id: string;
  task_id: string;
  start_time: string;
  end_time?: string | null;
  duration_seconds: number;
  paused_duration_seconds: number;
}

export interface BreakSession {
  id: string;
  day_id: string;
  break_type: string;
  start_time: string;
  end_time?: string | null;
  duration_seconds: number;
  notes?: string | null;
}

export interface Day {
  id: string;
  date: string;
  start_time?: string | null;
  end_time?: string | null;
  status: string;
  created_at: string;
  updated_at: string;
}

export interface Reflection {
  id: string;
  day_id: string;
  accomplishments?: string | null;
  challenges?: string | null;
  tomorrow_first_task?: string | null;
  additional_notes?: string | null;
  completed_at?: string | null;
}

export interface DailySummary {
  id: string;
  day_id: string;
  total_planned: number;
  completed: number;
  carried_forward: number;
  archived: number;
  deleted_count: number;
  total_focus_seconds: number;
  total_break_seconds: number;
  completion_percentage: number;
  longest_session_seconds: number;
  session_count: number;
  generated_markdown_path?: string | null;
  archived_at?: string | null;
}

export interface AppConfiguration {
  working_hours_start: string;
  working_hours_end: string;
  lunch_time?: string | null;
  dinner_time?: string | null;
  overlay_position: string;
  overlay_opacity: number;
  theme: string;
  markdown_vault_path?: string | null;
  journal_directory: string;
  notification_enabled: boolean;
  startup_behavior: string;
  launch_at_startup: boolean;
  deadline_reminder_minutes: number;
  break_reminder_enabled: boolean;
  short_break_duration: number;
  long_break_duration: number;
  sessions_before_long_break: number;
}

export interface TodayStatus {
  state: AppState;
  active_task: Task | null;
  current_session: WorkSession | null;
  day: Day | null;
  daily_summary: DailySummary | null;
  pending_tasks: number;
  completed_tasks: number;
}

export interface CreateTaskRequest {
  title: string;
  description?: string | null;
  priority: string;
  deadline?: string | null;
  estimated_duration_minutes?: number | null;
  notes?: string | null;
}

export interface UpdateTaskRequest {
  id: string;
  title?: string | null;
  description?: string | null;
  priority?: string | null;
  deadline?: string | null;
  estimated_duration_minutes?: number | null;
  notes?: string | null;
  display_order?: number | null;
}
