import {
  createContext,
  useContext,
  useState,
  useEffect,
  useCallback,
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
  loadSession: () => Promise<void>;
  handleStartSession: () => Promise<void>;
  handleStartDay: () => Promise<void>;
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
          // Find active task
          const active = existingTasks.find((t) => t.status === "active");
          if (active) {
            setActiveTaskId(active.id);
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
  }, []);

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
        loadSession,
        handleStartSession,
        handleStartDay,
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
