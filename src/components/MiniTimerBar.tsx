import { useSession } from "../contexts/SessionContext";

function formatTime(seconds: number) {
  const m = Math.floor(seconds / 60);
  const s = seconds % 60;
  return `${m.toString().padStart(2, "0")}:${s.toString().padStart(2, "0")}`;
}

function formatMinutes(minutes: number) {
  if (minutes < 60) return `${minutes}m`;
  const h = Math.floor(minutes / 60);
  const m = minutes % 60;
  return `${h}h ${m}m`;
}

export function MiniTimerBar() {
  const {
    tasks,
    activeTaskId,
    elapsedSeconds,
    handlePauseTask,
    handleCompleteTask,
  } = useSession();

  const activeTask = tasks.find((t) => t.id === activeTaskId);
  if (!activeTask || activeTask.status !== "active") return null;

  return (
    <div className="flex-none h-9 border-b border-[var(--color-border)] bg-[var(--color-surface)] animate-slide-in-right">
      <div className="h-full flex items-center justify-between px-4 max-w-[900px] mx-auto">
        <div className="flex items-center gap-2.5 min-w-0">
          <span className="w-1.5 h-1.5 rounded-full bg-[var(--color-primary)] animate-pulse-subtle flex-none" />
          <span className="text-xs font-medium truncate text-[var(--color-text-secondary)]">
            {activeTask.title}
          </span>
        </div>
        <div className="flex items-center gap-3 flex-none">
          <span className="font-mono text-xs font-semibold tabular-nums text-[var(--color-text)]">
            {formatTime(elapsedSeconds)}
          </span>
          <span className="text-[11px] text-[var(--color-text-tertiary)]">
            / {formatMinutes(activeTask.estimated_duration_minutes)}
          </span>
          <button
            onClick={() => handlePauseTask(activeTask.id)}
            className="text-[var(--color-text-tertiary)] hover:text-[var(--color-text)] transition-colors p-0.5"
            title="Pause"
          >
            <svg width="11" height="11" viewBox="0 0 11 11" fill="currentColor">
              <rect x="2" y="1.5" width="2.5" height="8" rx="0.8" />
              <rect x="6.5" y="1.5" width="2.5" height="8" rx="0.8" />
            </svg>
          </button>
          <button
            onClick={() => handleCompleteTask(activeTask)}
            className="text-xs font-medium text-[var(--color-success)] hover:text-[var(--color-success)]/80 transition-colors"
            title="Complete"
          >
            ✓
          </button>
        </div>
      </div>
    </div>
  );
}
