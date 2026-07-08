import { invoke } from "@tauri-apps/api/core";
import type {
  Session,
  Task,
  TimeEntry,
  Reflection,
  Settings,
} from "../types";

// ─── Session ────────────────────────────────────────────────────────────────

export async function startSession(): Promise<Session> {
  return invoke<Session>("start_session");
}

export async function getTodaySession(): Promise<Session | null> {
  return invoke<Session | null>("get_today_session");
}

export async function getSessionById(
  sessionId: string,
): Promise<Session | null> {
  return invoke<Session | null>("get_session_by_id", { sessionId });
}

export async function startDay(sessionId: string): Promise<void> {
  return invoke<void>("start_day", { sessionId });
}

export async function endDay(sessionId: string): Promise<void> {
  return invoke<void>("end_day", { sessionId });
}

// ─── Tasks ──────────────────────────────────────────────────────────────────

export async function createTask(
  sessionId: string,
  title: string,
  description: string,
  priority: string,
  estimatedDurationMinutes: number,
): Promise<Task> {
  return invoke<Task>("create_task", {
    sessionId,
    title,
    description,
    priority,
    estimatedDurationMinutes,
  });
}

export async function getTasksBySession(
  sessionId: string,
): Promise<Task[]> {
  return invoke<Task[]>("get_tasks_by_session", { sessionId });
}

export async function updateTask(task: Task): Promise<void> {
  return invoke<void>("update_task", { task });
}

export async function updateTaskStatus(
  taskId: string,
  status: string,
): Promise<void> {
  return invoke<void>("update_task_status", { taskId, status });
}

export async function deleteTask(taskId: string): Promise<void> {
  return invoke<void>("delete_task", { taskId });
}

export async function reorderTasks(taskIds: string[]): Promise<void> {
  return invoke<void>("reorder_tasks", { taskIds });
}

export async function getIncompleteTasksBeforeDate(
  date: string,
): Promise<Task[]> {
  return invoke<Task[]>("get_incomplete_tasks_before_date", { date });
}

// ─── Time Entries ───────────────────────────────────────────────────────────

export async function startTaskTimer(taskId: string): Promise<TimeEntry> {
  return invoke<TimeEntry>("start_task_timer", { taskId });
}

export async function stopTaskTimer(taskId: string): Promise<number> {
  return invoke<number>("stop_task_timer", { taskId });
}

export async function pauseTaskTimer(taskId: string): Promise<number> {
  return invoke<number>("pause_task_timer", { taskId });
}

export async function getActiveTimeEntry(
  taskId: string,
): Promise<TimeEntry | null> {
  return invoke<TimeEntry | null>("get_active_time_entry", { taskId });
}

// ─── Reflection ─────────────────────────────────────────────────────────────

export async function saveReflection(
  sessionId: string,
  wentWell: string,
  wentWrong: string,
  improve: string,
): Promise<Reflection> {
  return invoke<Reflection>("save_reflection", {
    sessionId,
    wentWell,
    wentWrong,
    improve,
  });
}

export async function getReflection(
  sessionId: string,
): Promise<Reflection | null> {
  return invoke<Reflection | null>("get_reflection", { sessionId });
}

// ─── Markdown ───────────────────────────────────────────────────────────────

export async function generateDailyNote(
  sessionId: string,
): Promise<string> {
  return invoke<string>("generate_daily_note", { sessionId });
}

// ─── Settings ───────────────────────────────────────────────────────────────

export async function getSettings(): Promise<Settings> {
  return invoke<Settings>("get_settings");
}

export async function updateSettings(
  settings: Settings,
): Promise<void> {
  return invoke<void>("update_settings", { settings });
}
