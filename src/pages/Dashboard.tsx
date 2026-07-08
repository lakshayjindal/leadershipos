import { useState, useEffect, useRef, useCallback } from "react";
import { useSession } from "../contexts/SessionContext";
import type { Task } from "../types";
import * as api from "../services/tauri";

export function Dashboard() {
  const {
    tasks,
    setTasks,
    setView,
    activeTaskId,
    setActiveTaskId,
    elapsedSeconds,
    setElapsedSeconds,
    settings,
  } = useSession();

  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const elapsedRef = useRef(0);
  const [notificationTask, setNotificationTask] = useState<Task | null>(null);
  const [showNotification, setShowNotification] = useState(false);
  const repeatTimerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const notificationTaskRef = useRef<Task | null>(null);
  const activeTaskIdRef = useRef<string | null>(null);

  useEffect(() => {
    notificationTaskRef.current = notificationTask;
  }, [notificationTask]);
  useEffect(() => {
    activeTaskIdRef.current = activeTaskId;
  }, [activeTaskId]);

  const activeTask = tasks.find((t) => t.id === activeTaskId) || null;
  const pendingTasks = tasks.filter(
    (t) => t.status === "pending" && t.id !== activeTaskId,
  );
  const completedTasks = tasks.filter((t) => t.status === "completed");
  const totalEstimated = tasks.reduce(
    (s, t) => s + t.estimated_duration_minutes, 0,
  );
  const totalActual = tasks.reduce(
    (s, t) => s + (t.actual_duration_minutes || 0), 0,
  );
  const activeTaskCount = tasks.filter(
    (t) => t.status !== "cancelled" && t.status !== "skipped",
  ).length;
  const progress =
    activeTaskCount > 0
      ? Math.round((completedTasks.length / activeTaskCount) * 100)
      : 0;

  const estimatedRemaining = tasks
    .filter((t) => t.status === "pending" || t.id === activeTaskId)
    .reduce((s, t) => s + t.estimated_duration_minutes, 0);

  const reminderIntervalMs = settings?.reminder_interval_minutes
    ? settings.reminder_interval_minutes * 60 * 1000
    : 5 * 60 * 1000;

  const sendDesktopNotification = useCallback(
    async (taskTitle: string, estimatedMinutes: number) => {
      try {
        const { sendNotification, isPermissionGranted, requestPermission } =
          await import("@tauri-apps/plugin-notification");
        let granted = await isPermissionGranted();
        if (!granted) {
          const permission = await requestPermission();
          granted = permission === "granted";
        }
        if (granted) {
          sendNotification({
            title: "Time is up!",
            body: `${taskTitle} (estimated ${estimatedMinutes} min) — please make a decision.`,
          });
        }
      } catch {
        // Notification plugin may not be available in all environments
      }
    },
    [],
  );

  const clearRepeatTimer = useCallback(() => {
    if (repeatTimerRef.current) {
      clearInterval(repeatTimerRef.current);
      repeatTimerRef.current = null;
    }
  }, []);

  const startRepeatTimer = useCallback(() => {
    clearRepeatTimer();
    repeatTimerRef.current = setInterval(() => {
      const currentTask = notificationTaskRef.current;
      if (
        currentTask &&
        currentTask.id === activeTaskIdRef.current &&
        activeTaskIdRef.current !== null
      ) {
        setShowNotification(true);
        sendDesktopNotification(
          currentTask.title,
          currentTask.estimated_duration_minutes,
        );
      } else {
        clearRepeatTimer();
      }
    }, reminderIntervalMs);
  }, [clearRepeatTimer, sendDesktopNotification, reminderIntervalMs]);

  useEffect(() => {
    if (activeTaskId && activeTask?.status === "active") {
      elapsedRef.current = 0;
      timerRef.current = setInterval(() => {
        elapsedRef.current += 1;
        setElapsedSeconds(elapsedRef.current);
      }, 1000);
      return () => {
        if (timerRef.current) clearInterval(timerRef.current);
      };
    } else {
      if (timerRef.current) clearInterval(timerRef.current);
      timerRef.current = null;
    }
  }, [activeTaskId, activeTask?.status, setElapsedSeconds]);

  useEffect(() => {
    if (!activeTask) return;
    const estimatedSeconds = activeTask.estimated_duration_minutes * 60;
    if (
      elapsedSeconds >= estimatedSeconds &&
      elapsedSeconds > 0 &&
      !showNotification
    ) {
      setNotificationTask(activeTask);
      setShowNotification(true);
      startRepeatTimer();
      sendDesktopNotification(
        activeTask.title,
        activeTask.estimated_duration_minutes,
      );
    }
  }, [elapsedSeconds, activeTask, startRepeatTimer, sendDesktopNotification]);

  useEffect(() => {
    return () => {
      clearRepeatTimer();
    };
  }, [clearRepeatTimer]);

  const formatTime = (seconds: number) => {
    const m = Math.floor(seconds / 60);
    const s = seconds % 60;
    return `${m.toString().padStart(2, "0")}:${s.toString().padStart(2, "0")}`;
  };

  const formatMinutes = (minutes: number) => {
    if (minutes < 60) return `${minutes}m`;
    const h = Math.floor(minutes / 60);
    const m = minutes % 60;
    return `${h}h ${m}m`;
  };

  const resolveNotification = useCallback(() => {
    clearRepeatTimer();
    setShowNotification(false);
    setNotificationTask(null);
  }, [clearRepeatTimer]);

  const handleStartTask = useCallback(
    async (task: Task) => {
      try {
        clearRepeatTimer();
        if (activeTaskId && activeTask) {
          await api.pauseTaskTimer(activeTaskId);
        }
        await api.startTaskTimer(task.id);
        setActiveTaskId(task.id);
        setElapsedSeconds(0);

        // Notify user that a new task has started
        try {
          const { sendNotification, isPermissionGranted, requestPermission } =
            await import("@tauri-apps/plugin-notification");
          let granted = await isPermissionGranted();
          if (!granted) {
            const permission = await requestPermission();
            granted = permission === "granted";
          }
          if (granted) {
            sendNotification({
              title: "Task started",
              body: `Working on: ${task.title} (${task.estimated_duration_minutes} min)`,
            });
          }
        } catch {}
      } catch (err) {
        console.error("Failed to start task:", err);
      }
    },
    [activeTaskId, activeTask, setActiveTaskId, setElapsedSeconds, clearRepeatTimer],
  );

  const handlePauseTask = useCallback(
    async (taskId: string) => {
      try {
        clearRepeatTimer();
        await api.pauseTaskTimer(taskId);
        setActiveTaskId(null);
        setElapsedSeconds(0);
      } catch (err) {
        console.error("Failed to pause task:", err);
      }
    },
    [setActiveTaskId, setElapsedSeconds, clearRepeatTimer],
  );

  const handleCompleteTask = useCallback(
    async (task: Task) => {
      try {
        clearRepeatTimer();
        if (activeTaskId === task.id) {
          await api.stopTaskTimer(task.id);
          setActiveTaskId(null);
          setElapsedSeconds(0);
        }
        await api.updateTaskStatus(task.id, "completed");
        setTasks(
          tasks.map((t) =>
            t.id === task.id ? { ...t, status: "completed" as const } : t,
          ),
        );
      } catch (err) {
        console.error("Failed to complete task:", err);
      }
    },
    [activeTaskId, tasks, setTasks, setActiveTaskId, setElapsedSeconds, clearRepeatTimer],
  );

  const handleSkipTask = useCallback(
    async (task: Task) => {
      try {
        clearRepeatTimer();
        if (activeTaskId === task.id) {
          await api.stopTaskTimer(task.id);
          setActiveTaskId(null);
          setElapsedSeconds(0);
        }
        await api.updateTaskStatus(task.id, "skipped");
        setTasks(
          tasks.map((t) =>
            t.id === task.id ? { ...t, status: "skipped" as const } : t,
          ),
        );
      } catch (err) {
        console.error("Failed to skip task:", err);
      }
    },
    [activeTaskId, tasks, setTasks, setActiveTaskId, setElapsedSeconds, clearRepeatTimer],
  );

  const handleExtendTime = useCallback(
    async (task: Task, extraMinutes: number) => {
      try {
        resolveNotification();
        const updated = {
          ...task,
          estimated_duration_minutes:
            task.estimated_duration_minutes + extraMinutes,
        };
        await api.updateTask(updated);
        if (extraMinutes > 0) {
          setTasks(
            tasks.map((t) =>
              t.id === task.id
                ? {
                    ...t,
                    estimated_duration_minutes:
                      t.estimated_duration_minutes + extraMinutes,
                  }
                : t,
            ),
          );
        }
        setElapsedSeconds(0);
      } catch (err) {
        console.error("Failed to extend time:", err);
      }
    },
    [tasks, setTasks, setElapsedSeconds, resolveNotification],
  );

  const handleStillWorking = useCallback(async () => {
    setShowNotification(false);
    setElapsedSeconds(0);
    elapsedRef.current = 0;
  }, [setElapsedSeconds]);

  const handleEndDay = async () => {
    clearRepeatTimer();
    if (activeTaskId && activeTask) {
      await handlePauseTask(activeTaskId);
    }
    setView("reflection");
  };

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="flex-none px-8 pt-8 pb-4 flex items-center justify-between">
        <div>
          <h1 className="text-[var(--text-h1)] font-semibold">Dashboard</h1>
          <div className="flex items-center gap-4 mt-1.5 text-sm text-[var(--color-text-secondary)]">
            <span>
              {completedTasks.length}/
              {tasks.filter((t) => t.status !== "cancelled").length} tasks
            </span>
            <span>{progress}% complete</span>
            <span>{formatMinutes(estimatedRemaining)} remaining</span>
          </div>
        </div>
        <button onClick={handleEndDay} className="btn-ghost text-sm">
          End day
        </button>
      </div>

      {/* Progress bar */}
      <div className="flex-none mx-8 h-1 rounded-full bg-[var(--color-border)] overflow-hidden">
        <div
          className="h-full rounded-full bg-[var(--color-primary)] transition-all duration-500 ease-out"
          style={{ width: `${progress}%` }}
        />
      </div>

      <div className="flex-1 overflow-y-auto px-8 py-5 space-y-5">
        {/* Current Task */}
        {activeTask && activeTask.status === "active" && (
          <div className="rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] p-6 shadow-sm">
            <p className="text-xs font-medium text-[var(--color-primary)] uppercase tracking-wider mb-1">
              Current task
            </p>
            <h2 className="text-base font-semibold mb-4">{activeTask.title}</h2>
            <div className="flex items-end gap-4 mb-5">
              <div className="font-mono text-[40px] font-semibold tracking-tight leading-none text-[var(--color-text)]">
                {formatTime(elapsedSeconds)}
              </div>
              <div className="pb-1 text-sm text-[var(--color-text-tertiary)]">
                Estimated {formatMinutes(activeTask.estimated_duration_minutes)}
              </div>
            </div>
            <div className="flex flex-wrap gap-2">
              <button
                onClick={() => handlePauseTask(activeTask.id)}
                className="btn-secondary text-sm px-4 py-2"
              >
                Pause
              </button>
              <button
                onClick={() => handleCompleteTask(activeTask)}
                className="btn-primary text-sm px-4 py-2"
              >
                Complete
              </button>
              <button
                onClick={() => handleSkipTask(activeTask)}
                className="btn-ghost text-sm"
              >
                Skip
              </button>
              <button
                onClick={() => handleExtendTime(activeTask, 15)}
                className="btn-ghost text-sm"
              >
                +15m
              </button>
              <button
                onClick={() => handleExtendTime(activeTask, 30)}
                className="btn-ghost text-sm"
              >
                +30m
              </button>
            </div>
          </div>
        )}

        {/* Pending Tasks */}
        {pendingTasks.length > 0 && (
          <section>
            <h3 className="text-xs font-medium text-[var(--color-text-tertiary)] uppercase tracking-wider mb-3">
              Pending
            </h3>
            <div className="space-y-2">
              {pendingTasks.map((task) => (
                <div
                  key={task.id}
                  className="rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] p-4 shadow-sm flex items-center gap-4"
                >
                  <button
                    onClick={() => handleStartTask(task)}
                    className="w-9 h-9 rounded-lg bg-[var(--color-primary)] text-white flex items-center justify-center hover:bg-[var(--color-primary-hover)] transition-colors flex-none shadow-sm cursor-pointer"
                    title="Start task"
                  >
                    <svg width="12" height="14" viewBox="0 0 12 14" fill="currentColor">
                      <path d="M1.5 1.5v11L10.5 7z" />
                    </svg>
                  </button>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium truncate">
                      {task.title}
                    </p>
                    <p className="text-xs text-[var(--color-text-tertiary)] mt-0.5">
                      {formatMinutes(task.estimated_duration_minutes)}
                    </p>
                  </div>
                  <button
                    onClick={() => handleSkipTask(task)}
                    className="btn-ghost text-xs"
                  >
                    Skip
                  </button>
                </div>
              ))}
            </div>
          </section>
        )}

        {/* Completed Tasks */}
        {completedTasks.length > 0 && (
          <section>
            <h3 className="text-xs font-medium text-[var(--color-text-tertiary)] uppercase tracking-wider mb-3">
              Completed
            </h3>
            <div className="space-y-2">
              {completedTasks.map((task) => (
                <div
                  key={task.id}
                  className="rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] p-4 flex items-center gap-4 opacity-60"
                >
                  <div className="w-9 h-9 rounded-lg bg-[var(--color-success-subtle)] flex items-center justify-center flex-none">
                    <svg width="14" height="14" viewBox="0 0 14 14" fill="none" stroke="var(--color-success)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <path d="M3 7L6 10L11 4" />
                    </svg>
                  </div>
                  <p className="text-sm line-through flex-1 text-[var(--color-text-tertiary)]">
                    {task.title}
                  </p>
                  {task.actual_duration_minutes !== null && (
                    <span className="text-xs text-[var(--color-text-tertiary)]">
                      {formatMinutes(task.actual_duration_minutes)}
                    </span>
                  )}
                </div>
              ))}
            </div>
          </section>
        )}

        {/* Empty state */}
        {tasks.filter(
          (t) =>
            t.status !== "completed" &&
            t.status !== "cancelled" &&
            t.status !== "skipped",
        ).length === 0 &&
          completedTasks.length === 0 && (
            <div className="text-center py-16">
              <p className="text-sm text-[var(--color-text-secondary)]">
                No tasks for today.
              </p>
              <p className="text-xs text-[var(--color-text-tertiary)] mt-1">
                Start a new session to plan your day.
              </p>
            </div>
          )}
      </div>

      {/* Bottom stats */}
      <div className="flex-none px-8 py-4 border-t border-[var(--color-border)] flex items-center justify-between text-xs text-[var(--color-text-tertiary)]">
        <span>Actual: {formatMinutes(totalActual)}</span>
        <span>Estimated: {formatMinutes(totalEstimated)}</span>
        <span>
          Accuracy:{" "}
          {totalEstimated > 0
            ? Math.round((totalActual / totalEstimated) * 100)
            : 0}
          %
        </span>
      </div>

      {/* Notification Modal */}
      {showNotification && notificationTask && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/30 backdrop-blur-sm"
          onClick={() => {}} // prevent accidental dismiss
        >
          <div className="rounded-2xl bg-[var(--color-surface)] border border-[var(--color-border)] p-8 max-w-sm w-full mx-6 shadow-xl">
            <div className="flex items-center gap-3 mb-1">
              <div className="w-10 h-10 rounded-xl bg-[var(--color-warning-subtle)] flex items-center justify-center">
                <svg width="20" height="20" viewBox="0 0 20 20" fill="none" stroke="var(--color-warning)" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M10 2L2 18h16L10 2z" />
                  <path d="M10 8v4" />
                  <path d="M10 14v1" />
                </svg>
              </div>
              <p className="text-base font-semibold">Time's up</p>
            </div>
            <p className="text-sm text-[var(--color-text-secondary)] mt-2 mb-4">
              Time is up for{" "}
              <span className="font-medium text-[var(--color-text)]">
                {notificationTask.title}
              </span>
            </p>
            {settings && (
              <p className="text-xs text-[var(--color-text-tertiary)] mb-6">
                Reminding every {settings.reminder_interval_minutes}{" "}
                minute{settings.reminder_interval_minutes !== 1 ? "s" : ""}
              </p>
            )}
            <div className="space-y-2">
              <button
                onClick={() => {
                  handleCompleteTask(notificationTask);
                  setShowNotification(false);
                }}
                className="btn-primary w-full text-sm"
              >
                Finish
              </button>
              <div className="grid grid-cols-2 gap-2">
                <button
                  onClick={() => handleExtendTime(notificationTask, 15)}
                  className="btn-secondary text-sm"
                >
                  +15 minutes
                </button>
                <button
                  onClick={() => handleExtendTime(notificationTask, 30)}
                  className="btn-secondary text-sm"
                >
                  +30 minutes
                </button>
              </div>
              <button onClick={handleStillWorking} className="btn-ghost w-full text-sm">
                Still working
              </button>
              <button
                onClick={() => {
                  handleSkipTask(notificationTask);
                  setShowNotification(false);
                }}
                className="btn-ghost w-full text-sm text-[var(--color-danger)] hover:bg-[var(--color-danger-subtle)]"
              >
                Switch task
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
