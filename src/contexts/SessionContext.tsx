import {
  createContext,
  useContext,
  useState,
  useEffect,
  useCallback,
  useRef,
  type ReactNode,
} from "react";
import type { Session, Task, Settings } from "../types";
import * as api from "../services/tauri";

export type AppView =
  | "loading"
  | "welcome"
  | "planning"
  | "commitment"
  | "dashboard"
  | "reflection"
  | "settings";

interface SessionContextType {
  view: AppView;
  session: Session | null;
  tasks: Task[];
  settings: Settings | null;
  activeTaskId: string | null;
  elapsedSeconds: number;
  showTimeUp: boolean;
  timeUpTask: Task | null;
  dismissTimeUp: () => void;
  extendTime: (extraMinutes: number) => Promise<void>;
  handleExtendTime: (task: Task, extraMinutes: number) => Promise<void>;
  stillWorking: () => void;
  loadSession: () => Promise<void>;
  handleStartSession: () => Promise<void>;
  handleStartDay: () => Promise<void>;
  handleStartTask: (task: Task) => Promise<void>;
  handlePauseTask: (taskId: string) => Promise<void>;
  handleCompleteTask: (task: Task) => Promise<void>;
  handleSkipTask: (task: Task) => Promise<void>;
  handleEndDay: () => Promise<void>;
  setTasks: (tasks: Task[]) => void;
  setView: (view: AppView) => void;
  setActiveTaskId: (id: string | null) => void;
  setElapsedSeconds: (s: number) => void;
  loadSettings: () => Promise<void>;
}

const SessionContext = createContext<SessionContextType | null>(null);

export function SessionProvider({ children }: { children: ReactNode }) {
  const [view, setView] = useState<AppView>("loading");
  const [session, setSession] = useState<Session | null>(null);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [settings, setSettings] = useState<Settings | null>(null);
  const [activeTaskId, setActiveTaskId] = useState<string | null>(null);
  const [elapsedSeconds, setElapsedSeconds] = useState(0);
  const [showTimeUp, setShowTimeUp] = useState(false);
  const [timeUpTask, setTimeUpTask] = useState<Task | null>(null);
  const timeUpTriggeredRef = useRef(false);

  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const notificationTimerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  // ─── Timer effect (runs on all pages) ───────────────────────────────
  useEffect(() => {
    if (activeTaskId) {
      timerRef.current = setInterval(() => {
        setElapsedSeconds((prev) => prev + 1);
      }, 1000);
      return () => {
        if (timerRef.current) clearInterval(timerRef.current);
      };
    }
    return;
  }, [activeTaskId]);

  // ─── Time-up detection ──────────────────────────────────────────────
  useEffect(() => {
    if (!activeTaskId) {
      setShowTimeUp(false);
      setTimeUpTask(null);
      timeUpTriggeredRef.current = false;
      return;
    }
    const activeTask = tasks.find((t) => t.id === activeTaskId);
    if (!activeTask) return;

    const estimatedSeconds = activeTask.estimated_duration_minutes * 60;
    if (elapsedSeconds >= estimatedSeconds && elapsedSeconds > 0 && !timeUpTriggeredRef.current) {
      timeUpTriggeredRef.current = true;
      setTimeUpTask(activeTask);
      setShowTimeUp(true);
      sendDesktopNotification(
        "Time is up!",
        `${activeTask.title} (estimated ${activeTask.estimated_duration_minutes} min) — please make a decision.`,
      );

      // Start repeat notification timer (only once)
      const intervalMs = settings?.reminder_interval_minutes
        ? settings.reminder_interval_minutes * 60 * 1000
        : 5 * 60 * 1000;
      notificationTimerRef.current = setInterval(() => {
        setShowTimeUp(true);
        const t = tasks.find((tt) => tt.id === activeTaskId);
        if (t && t.status === "active") {
          sendDesktopNotification(
            "Time is up!",
            `${t.title} (estimated ${t.estimated_duration_minutes} min) — please make a decision.`,
          );
        }
      }, intervalMs);
    }

    return () => {
      // No cleanup of notificationTimerRef here — it's managed by dismissTimeUp
    };
  }, [elapsedSeconds, activeTaskId, tasks, settings]);

  const dismissTimeUp = useCallback(() => {
    if (notificationTimerRef.current) {
      clearInterval(notificationTimerRef.current);
      notificationTimerRef.current = null;
    }
    setShowTimeUp(false);
    setTimeUpTask(null);
  }, []);

  const stillWorking = useCallback(() => {
    setShowTimeUp(false);
    setElapsedSeconds(0);
  }, [setElapsedSeconds]);

  const extendTime = useCallback(
    async (extraMinutes: number) => {
      const task = timeUpTask;
      if (!task) return;
      dismissTimeUp();
      try {
        const updated = {
          ...task,
          estimated_duration_minutes: task.estimated_duration_minutes + extraMinutes,
        };
        await api.updateTask(updated);
        setTasks(
          tasks.map((t) =>
            t.id === task.id ? updated : t,
          ),
        );
        setElapsedSeconds(0);
      } catch (err) {
        console.error("Failed to extend time:", err);
      }
    },
    [timeUpTask, tasks, setTasks, setElapsedSeconds, dismissTimeUp],
  );

  const handleExtendTime = useCallback(
    async (task: Task, extraMinutes: number) => {
      try {
        dismissTimeUp();
        const updated = {
          ...task,
          estimated_duration_minutes: task.estimated_duration_minutes + extraMinutes,
        };
        await api.updateTask(updated);
        setTasks(
          tasks.map((t) =>
            t.id === task.id ? updated : t,
          ),
        );
        setElapsedSeconds(0);
      } catch (err) {
        console.error("Failed to extend time:", err);
      }
    },
    [tasks, setTasks, setElapsedSeconds, dismissTimeUp],
  );

  // ─── Notification helper ──────────────────────────────────────────────
  const sendDesktopNotification = async (
    title: string,
    body: string,
  ) => {
    // Respect the user's preference
    if (settings && settings.desktop_notifications === false) return;

    try {
      const { sendNotification, isPermissionGranted, requestPermission } =
        await import("@tauri-apps/plugin-notification");
      let granted = await isPermissionGranted();
      if (!granted) {
        const permission = await requestPermission();
        granted = permission === "granted";
      }
      if (granted) {
        sendNotification({ title, body });
      }
    } catch {
      // Notification plugin not available
    }
  };

  // ─── Timer restore on app restart ─────────────────────────────────────
  const restoreElapsedTime = useCallback(
    async (taskId: string) => {
      try {
        const entry = await api.getActiveTimeEntry(taskId);
        if (entry && entry.start_time) {
          const start = new Date(entry.start_time.replace(" ", "T") + "Z").getTime();
          const now = Date.now();
          const elapsed = Math.floor((now - start) / 1000);
          if (elapsed > 0) setElapsedSeconds(elapsed);
        }
      } catch {
        // Couldn't restore — start from 0
      }
    },
    [setElapsedSeconds],
  );

  // ─── Session loading with timer restore ──────────────────────────────
  const loadSession = useCallback(async () => {
    try {
      const existingSession = await api.getTodaySession();
      if (existingSession) {
        setSession(existingSession);
        const existingTasks = await api.getTasksBySession(existingSession.id);
        setTasks(existingTasks);
        if (existingSession.status === "planning") {
          setView("planning");
        } else if (existingSession.status === "active") {
          const active = existingTasks.find((t) => t.status === "active");
          if (active) {
            setActiveTaskId(active.id);
            await restoreElapsedTime(active.id);
          }
          setView("dashboard");
        } else {
          setView("welcome");
        }
      } else {
        setSession(null);
        setTasks([]);
        setView("welcome");
      }
    } catch {
      setView("welcome");
    }
  }, [restoreElapsedTime]);

  const handleStartSession = useCallback(async () => {
    try {
      const newSession = await api.startSession();
      setSession(newSession);
      const sessionTasks = await api.getTasksBySession(newSession.id);
      setTasks(sessionTasks);
      setView("planning");
    } catch (err) {
      console.error("Failed to start session:", err);
    }
  }, []);

  const handleStartDay = useCallback(async () => {
    if (!session) return;
    try {
      await api.startDay(session.id);
      setSession({ ...session, status: "active" });
      setView("dashboard");
    } catch (err) {
      console.error("Failed to start day:", err);
    }
  }, [session]);

  // ─── Task actions ────────────────────────────────────────────────────
  const handleStartTask = useCallback(
    async (task: Task) => {
      try {
        dismissTimeUp();
        // Pause current task if any
        if (activeTaskId) {
          await api.pauseTaskTimer(activeTaskId);
        }
        await api.startTaskTimer(task.id);
        setActiveTaskId(task.id);
        setElapsedSeconds(0);

        // Update local tasks array — THIS FIXES THE TIMER BUG
        setTasks(
          tasks.map((t) =>
            t.id === task.id ? { ...t, status: "active" as const } : t,
          ),
        );

        sendDesktopNotification(
          "Task started",
          `Working on: ${task.title} (${task.estimated_duration_minutes} min)`,
        );
      } catch (err) {
        console.error("Failed to start task:", err);
      }
    },
    [activeTaskId, tasks, setTasks, setActiveTaskId, setElapsedSeconds, dismissTimeUp],
  );

  const handlePauseTask = useCallback(
    async (taskId: string) => {
      try {
        dismissTimeUp();
        await api.pauseTaskTimer(taskId);
        setActiveTaskId(null);
        setElapsedSeconds(0);
      } catch (err) {
        console.error("Failed to pause task:", err);
      }
    },
    [setActiveTaskId, setElapsedSeconds, dismissTimeUp],
  );

  const handleCompleteTask = useCallback(
    async (task: Task) => {
      try {
        dismissTimeUp();
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
    [activeTaskId, tasks, setTasks, setActiveTaskId, setElapsedSeconds, dismissTimeUp],
  );

  const handleSkipTask = useCallback(
    async (task: Task) => {
      try {
        dismissTimeUp();
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
    [activeTaskId, tasks, setTasks, setActiveTaskId, setElapsedSeconds, dismissTimeUp],
  );

  const handleEndDay = useCallback(async () => {
    dismissTimeUp();
    if (activeTaskId) {
      await api.pauseTaskTimer(activeTaskId);
      setActiveTaskId(null);
      setElapsedSeconds(0);
    }
    setView("reflection");
  }, [activeTaskId, setActiveTaskId, setElapsedSeconds, dismissTimeUp]);

  const loadSettings = useCallback(async () => {
    try {
      const s = await api.getSettings();
      setSettings(s);
    } catch {
      // Settings will be created automatically
    }
  }, []);

  useEffect(() => {
    loadSession();
    loadSettings();
  }, [loadSession, loadSettings]);

  return (
    <SessionContext.Provider
      value={{
        view,
        session,
        tasks,
        settings,
        activeTaskId,
        elapsedSeconds,
        showTimeUp,
        timeUpTask,
        dismissTimeUp,
        extendTime,
        handleExtendTime,
        stillWorking,
        loadSession,
        handleStartSession,
        handleStartDay,
        handleStartTask,
        handlePauseTask,
        handleCompleteTask,
        handleSkipTask,
        handleEndDay,
        setTasks,
        setView,
        setActiveTaskId,
        setElapsedSeconds,
        loadSettings,
      }}
    >
      {children}
    </SessionContext.Provider>
  );
}

export function useSession(): SessionContextType {
  const ctx = useContext(SessionContext);
  if (!ctx) throw new Error("useSession must be used within SessionProvider");
  return ctx;
}
