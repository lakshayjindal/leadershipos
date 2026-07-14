import { invoke } from '@tauri-apps/api/core';
import type {
  Task, WorkSession, BreakSession, Day, Reflection,
  DailySummary, AppConfiguration, TodayStatus, CreateTaskRequest, UpdateTaskRequest
} from './types';

// ─── Day API ──────────────────────────────────────────────────────

export async function getToday(): Promise<Day> {
  return invoke<Day>('get_today');
}

export async function getTodayStatus(): Promise<TodayStatus> {
  return invoke<TodayStatus>('get_today_status');
}

// ─── Task API ─────────────────────────────────────────────────────

export async function createTask(dayId: string, req: CreateTaskRequest): Promise<Task> {
  return invoke<Task>('create_task', { dayId, req });
}

export async function getTasks(dayId: string): Promise<Task[]> {
  return invoke<Task[]>('get_tasks', { dayId });
}

export async function updateTask(req: UpdateTaskRequest): Promise<void> {
  return invoke<void>('update_task', { req });
}

export async function setTaskStatus(taskId: string, status: string): Promise<void> {
  return invoke<void>('set_task_status', { taskId, status });
}

export async function reorderTasks(taskIds: string[]): Promise<void> {
  return invoke<void>('reorder_tasks', { taskIds });
}

// ─── Timer API ────────────────────────────────────────────────────

export async function startTask(taskId: string): Promise<WorkSession> {
  return invoke<WorkSession>('start_task', { taskId });
}

export async function pauseTask(taskId: string): Promise<void> {
  return invoke<void>('pause_task', { taskId });
}

export async function completeTask(taskId: string): Promise<void> {
  return invoke<void>('complete_task', { taskId });
}

export async function getActiveSession(taskId: string): Promise<WorkSession | null> {
  return invoke<WorkSession | null>('get_active_session', { taskId });
}

// ─── Break API ────────────────────────────────────────────────────

export async function startBreak(dayId: string, breakType: string): Promise<BreakSession> {
  return invoke<BreakSession>('start_break', { dayId, breakType });
}

export async function endBreak(breakId: string): Promise<BreakSession> {
  return invoke<BreakSession>('end_break', { breakId });
}

export async function getActiveBreak(dayId: string): Promise<BreakSession | null> {
  return invoke<BreakSession | null>('get_active_break', { dayId });
}

// ─── Reflection API ──────────────────────────────────────────────

export async function saveReflection(
  dayId: string, accomplishments: string, challenges: string, tomorrowTask: string
): Promise<Reflection> {
  return invoke<Reflection>('save_reflection', { dayId, accomplishments, challenges, tomorrowTask });
}

export async function getReflection(dayId: string): Promise<Reflection | null> {
  return invoke<Reflection | null>('get_reflection', { dayId });
}

// ─── Journal API ──────────────────────────────────────────────────

export async function generateJournal(dayId: string): Promise<string> {
  return invoke<string>('generate_journal', { dayId });
}

// ─── Search API ───────────────────────────────────────────────────

export async function search(query: string): Promise<Task[]> {
  return invoke<Task[]>('search', { query });
}

// ─── Carry Forward API ───────────────────────────────────────────

export async function getCarryForwardTasks(): Promise<Task[]> {
  return invoke<Task[]>('get_carry_forward_tasks');
}

export async function carryForwardTask(taskId: string, todayId: string): Promise<Task> {
  return invoke<Task>('carry_forward_task', { taskId, todayId });
}

export async function autoCarryForwardAll(): Promise<Task[]> {
  return invoke<Task[]>('auto_carry_forward_all');
}

// ─── Shutdown API ────────────────────────────────────────────────

export async function shutdownDay(dayId: string, generateJournal: boolean): Promise<string | null> {
  return invoke<string | null>('shutdown_day', { dayId, generateJournal });
}

// ─── Config API ───────────────────────────────────────────────────

export async function getConfig(): Promise<AppConfiguration> {
  return invoke<AppConfiguration>('get_config');
}

export async function saveConfig(config: AppConfiguration): Promise<void> {
  return invoke<void>('save_config', { config });
}

// ─── App State API ────────────────────────────────────────────────

export async function getAppState(): Promise<[string, string | null, string | null]> {
  return invoke<[string, string | null, string | null]>('get_app_state_cmd');
}

export async function setAppState(state: string, activeTaskId?: string | null, currentDayId?: string | null): Promise<void> {
  return invoke<void>('set_app_state_cmd', { state, activeTaskId, currentDayId });
}

// ─── History API ───────────────────────────────────────────────────

export async function getPreviousDays(limit?: number): Promise<[Day, DailySummary | null][]> {
  return invoke<[Day, DailySummary | null][]>('get_previous_days', { limit });
}

// ─── Overlay API ──────────────────────────────────────────────────

export async function toggleOverlay(): Promise<boolean> {
  return invoke<boolean>('toggle_overlay');
}

// ─── Formatting Utilities ────────────────────────────────────────

export function formatDuration(seconds: number): string {
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  const s = seconds % 60;
  if (h > 0) return `${h}h ${m}m`;
  if (m > 0) return `${m}m ${s}s`;
  return `${s}s`;
}

export function formatDurationShort(seconds: number): string {
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  const s = seconds % 60;
  if (h > 0) return `${h}:${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
  return `${m}:${s.toString().padStart(2, '0')}`;
}

export function formatDate(dateStr: string): string {
  const date = new Date(dateStr);
  return date.toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric', year: 'numeric' });
}

export function formatTime(dateStr: string): string {
  if (!dateStr) return '--:--';
  return dateStr.substring(11, 16);
}

export function nowISO(): string {
  return new Date().toISOString().replace('T', ' ').substring(0, 19);
}

export function getPriorityColor(priority: string): string {
  switch (priority) {
    case 'critical': return 'var(--color-critical)';
    case 'high': return 'var(--color-high)';
    case 'medium': return 'var(--color-medium)';
    case 'low': return 'var(--color-low)';
    default: return 'var(--color-medium)';
  }
}

export function getStatusIcon(status: string): string {
  switch (status) {
    case 'pending': return '○';
    case 'active': return '◉';
    case 'completed': return '✓';
    case 'archived': return '▤';
    case 'carried_forward': return '→';
    default: return '○';
  }
}

export function classNames(...classes: (string | boolean | undefined | null)[]): string {
  return classes.filter(Boolean).join(' ');
}
