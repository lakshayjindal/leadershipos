import { useState, useEffect, useRef } from 'react';
import type { Task, BreakSession, WorkSession } from '../types';
import { useAppStore } from '../store';
import {
  startTask, pauseTask, completeTask,
  startBreak, endBreak, getActiveBreak, getToday,
  formatDurationShort, formatDuration, formatTime,
} from '../utils';
import { showOverlay, hideOverlay, updateOverlay } from '../overlay';
import { notifyTimerStarted, notifyTimerPaused, notifyTimerCompleted } from '../notifications';
import { useToast } from './Toast';

const breakTypes = [
  { id: 'tea', label: 'Tea', icon: '☕' },
  { id: 'lunch', label: 'Lunch', icon: '🍽' },
  { id: 'dinner', label: 'Dinner', icon: '🌙' },
  { id: 'personal', label: 'Personal', icon: '🧘' },
  { id: 'meeting', label: 'Meeting', icon: '📋' },
];

export default function ExecutionPanel() {
  const { todayStatus, currentState, setCurrentState, setTodayStatus } = useAppStore();
  const { addToast } = useToast();

  // Timer state
  const [elapsed, setElapsed] = useState(0);
  const [isRunning, setIsRunning] = useState(false);
  const [showBreakOptions, setShowBreakOptions] = useState(false);
  const [activeBreak, setActiveBreak] = useState<BreakSession | null>(null);
  const [breakElapsed, setBreakElapsed] = useState(0);
  const [clickThroughMode, setClickThroughMode] = useState(false);
  const [sessionCount, setSessionCount] = useState(todayStatus?.daily_summary?.session_count ?? 0);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const breakIntervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const overlayIntervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const activeTask = todayStatus?.active_task ?? null;
  const activeSession = todayStatus?.current_session ?? null;
  const dailySummary = todayStatus?.daily_summary ?? null;

  // Refs to track start time for overlay and timer accuracy
  const startTimeRef = useRef<number>(0);

  // Initialize from todayStatus
  useEffect(() => {
    if (activeSession && activeTask) {
      const startTime = parseDate(activeSession.start_time);
      startTimeRef.current = startTime;
      setIsRunning(true);
      startTimerInterval(startTime);
      startOverlayUpdates(activeTask.title, startTime, 'running');
      showOverlay();
    }
    checkActiveBreak();
    return () => {
      clearIntervals();
    };
  }, []);

  // Re-check break on state change
  useEffect(() => {
    if (currentState === 'break') {
      checkActiveBreak();
    }
  }, [currentState]);

  function clearIntervals() {
    if (intervalRef.current) clearInterval(intervalRef.current);
    if (breakIntervalRef.current) clearInterval(breakIntervalRef.current);
    if (overlayIntervalRef.current) clearInterval(overlayIntervalRef.current);
  }

  async function checkActiveBreak() {
    try {
      const day = await getToday();
      const brk = await getActiveBreak(day.id);
      if (brk) {
        setActiveBreak(brk);
        const start = new Date(brk.start_time.replace(' ', 'T')).getTime();
        setBreakElapsed(Math.floor((Date.now() - start) / 1000));
        if (breakIntervalRef.current) clearInterval(breakIntervalRef.current);
        breakIntervalRef.current = setInterval(() => {
          setBreakElapsed(prev => prev + 1);
        }, 1000);
      }
    } catch { /* ignore */ }
  }

  function parseDate(dateStr: string): number {
    return new Date(dateStr.replace(' ', 'T')).getTime();
  }

  function startTimerInterval(startTime: number) {
    if (intervalRef.current) clearInterval(intervalRef.current);
    const now = Date.now();
    setElapsed(Math.floor((now - startTime) / 1000));
    intervalRef.current = setInterval(() => {
      // Recalculate from startTime to avoid drift
      setElapsed(Math.floor((Date.now() - startTime) / 1000));
    }, 1000);
  }

  function startOverlayUpdates(taskTitle: string, startTime: number, status: string) {
    if (overlayIntervalRef.current) clearInterval(overlayIntervalRef.current);
    const count = todayStatus?.pending_tasks ?? 0;
    updateOverlay(
      taskTitle,
      Math.floor((Date.now() - startTime) / 1000),
      status,
      count > 0 ? `${count} pending` : undefined
    );
    // Continuously update overlay every 2 seconds
    overlayIntervalRef.current = setInterval(() => {
      updateOverlay(
        taskTitle,
        Math.floor((Date.now() - startTime) / 1000),
        status
      );
    }, 2000);
  }

  async function handleStartTask(taskId: string) {
    try {
      const session = await startTask(taskId);
      const startTime = parseDate(session.start_time);
      setIsRunning(true);
      setElapsed(0);
      startTimerInterval(startTime);
      setCurrentState('working');

      const task = todayStatus?.active_task ?? null;
      startOverlayUpdates(task?.title || 'Task', startTime, 'running');
      showOverlay();
      if (task) notifyTimerStarted(task.title);
      refreshStatus();
    } catch (e) {
      addToast('Failed to start task', 'error');
    }
  }

  async function handlePause() {
    if (!activeTask) return;
    try {
      await pauseTask(activeTask.id);
      setIsRunning(false);
      if (intervalRef.current) clearInterval(intervalRef.current);
      updateOverlay(activeTask.title, elapsed, 'paused');
      setTimeout(() => hideOverlay(), 2000);
      notifyTimerPaused(activeTask.title, formatDurationShort(elapsed));
      setCurrentState('idle');
      refreshStatus();
    } catch (e) {
      addToast('Failed to pause', 'error');
    }
  }

  async function handleComplete() {
    if (!activeTask) return;
    try {
      const title = activeTask.title;
      const totalElapsed = elapsed;
      await completeTask(activeTask.id);
      setIsRunning(false);
      setElapsed(0);
      clearIntervals();
      hideOverlay();
      notifyTimerCompleted(title, formatDurationShort(totalElapsed));
      addToast(`✓ "${title}" completed`, 'success');
      refreshStatus();
    } catch (e) {
      addToast('Failed to complete task', 'error');
    }
  }

  async function handleStartBreak(breakType: string) {
    try {
      if (isRunning && activeTask) {
        await pauseTask(activeTask.id);
        setIsRunning(false);
        if (intervalRef.current) clearInterval(intervalRef.current);
      }
      const day = await getToday();
      const session = await startBreak(day.id, breakType);
      setActiveBreak(session);
      setBreakElapsed(0);
      setShowBreakOptions(false);
      setCurrentState('break');

      const start = new Date(session.start_time.replace(' ', 'T')).getTime();
      if (breakIntervalRef.current) clearInterval(breakIntervalRef.current);
      breakIntervalRef.current = setInterval(() => {
        setBreakElapsed(Math.floor((Date.now() - start) / 1000));
      }, 1000);
      refreshStatus();
    } catch (e) {
      addToast('Failed to start break', 'error');
    }
  }

  async function handleEndBreak() {
    if (!activeBreak) return;
    try {
      await endBreak(activeBreak.id);
      setActiveBreak(null);
      setBreakElapsed(0);
      if (breakIntervalRef.current) clearInterval(breakIntervalRef.current);
      setCurrentState('working');
      addToast('Break ended. Ready to focus.', 'info');
      refreshStatus();
    } catch (e) {
      addToast('Failed to end break', 'error');
    }
  }

  // Re-import getTodayStatus from utils (top-level import would cause circular deps)
  async function refreshStatus() {
    try {
      const { getTodayStatus } = await import('../utils');
      const status = await getTodayStatus();
      setTodayStatus(status);
    } catch { /* ignore */ }
  }

  // ─── Determine what to render based on state ───────────────────

  function renderTimerSection() {
    if (currentState === 'review') return null; // Minimized during review

    if (currentState === 'break' && activeBreak) {
      return (
        <>
          <div className="execution-break-indicator">
            {breakTypes.find(b => b.id === activeBreak.break_type)?.icon || '☕'}
            {' '}
            {breakTypes.find(b => b.id === activeBreak.break_type)?.label || activeBreak.break_type}
          </div>
          <div className="execution-timer" style={{ color: 'var(--color-warning)' }}>
            {formatDurationShort(breakElapsed)}
          </div>
          <div className="execution-session-info">
            <span>Started: {formatTime(activeBreak.start_time)}</span>
          </div>
          <div className="execution-actions">
            <button className="btn btn-primary btn-lg w-full" onClick={handleEndBreak}>
              ▶ Resume Work
            </button>
          </div>
        </>
      );
    }

    if (!activeTask && currentState !== 'planning' && currentState !== 'idle' && currentState !== 'startup') {
      return (
        <>
          <div className="execution-timer" style={{ color: 'var(--color-text-muted)', fontSize: 24 }}>
            00:00
          </div>
          <div className="execution-idle-message">
            No active task.<br />
            Start one from Today's Plan.
          </div>
        </>
      );
    }

    if (activeTask) {
      return (
        <>
          <div className="execution-current-task">
            <div className="execution-task-title">{activeTask.title}</div>
            <span className={`badge badge-${activeTask.priority}`} style={{ fontSize: 10 }}>
              {activeTask.priority}
            </span>
          </div>

          <div className="execution-timer">
            {formatDurationShort(elapsed)}
          </div>

          {activeSession && (
            <div className="execution-session-info">
              <span>Started: {formatTime(activeSession.start_time)}</span>
              <span>Elapsed: {formatDuration(elapsed)}</span>
              {activeTask.estimated_duration_minutes && (
                <span>Est: {activeTask.estimated_duration_minutes}m</span>
              )}
            </div>
          )}

          {isRunning ? (
            <div className="execution-actions">
              <button className="btn btn-secondary btn-lg w-full" onClick={handlePause}>
                ⏸ Pause
              </button>
              <button className="btn btn-primary btn-lg w-full" onClick={handleComplete}>
                ✓ Complete
              </button>
              <button className="btn btn-ghost btn-sm w-full" onClick={() => setShowBreakOptions(true)}>
                ☕ Start Break
              </button>
            </div>
          ) : (
            <div className="execution-actions">
              <button className="btn btn-primary btn-lg w-full" onClick={() => handleStartTask(activeTask.id)}>
                ▶ Resume
              </button>
            </div>
          )}

          {/* Session counter */}
          {sessionCount > 0 && (
            <div className="execution-session-info" style={{ textAlign: 'center', padding: '4px 0' }}>
              <span>Session #{sessionCount}</span>
            </div>
          )}

          {/* Click-through mode toggle */}
          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 4 }}>
            <button
              className="btn btn-ghost"
              style={{
                fontSize: 11, padding: '2px 6px',
                color: clickThroughMode ? 'var(--color-primary)' : 'var(--color-text-muted)',
              }}
              onClick={() => setClickThroughMode(!clickThroughMode)}
              title={clickThroughMode ? 'Click-through enabled' : 'Click-through disabled'}
            >
              {clickThroughMode ? '◉ Click-Through' : '○ Click-Through'}
            </button>
          </div>

          {showBreakOptions && (
            <div className="execution-break-options">
              <div className="text-xs text-secondary" style={{ marginBottom: 4 }}>Choose break type:</div>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4 }}>
                {breakTypes.map(bt => (
                  <button
                    key={bt.id}
                    className="btn btn-ghost btn-sm"
                    onClick={() => handleStartBreak(bt.id)}
                  >
                    {bt.icon} {bt.label}
                  </button>
                ))}
                <button className="btn btn-ghost btn-sm" onClick={() => setShowBreakOptions(false)}>
                  ✕ Cancel
                </button>
              </div>
            </div>
          )}
        </>
      );
    }

    // Idle / planning state
    return (
      <>
        <div className="execution-timer" style={{ color: 'var(--color-text-muted)', fontSize: 24 }}>
          00:00
        </div>
        <div className="execution-idle-message">
          No active task.<br />
          Start one from Today's Plan.
        </div>
      </>
    );
  }

  function renderProgress() {
    if (!dailySummary) return null;
    const pct = dailySummary.completion_percentage;
    return (
      <div className="execution-progress">
        <div className="progress-bar">
          <div
            className={`progress-bar-fill ${pct >= 80 ? 'success' : pct >= 40 ? 'warning' : ''}`}
            style={{ width: `${Math.min(pct, 100)}%` }}
          />
        </div>
        <div className="execution-progress-text">
          {dailySummary.completed}/{dailySummary.total_planned} Tasks ({Math.round(pct)}%)
        </div>
      </div>
    );
  }

  return (
    <aside className="execution-panel">
      {renderTimerSection()}
      {renderProgress()}
    </aside>
  );
}
