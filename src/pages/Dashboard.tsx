import { useCallback, useState } from "react";
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

export function Dashboard() {
  const {
    tasks,
    activeTaskId,
    elapsedSeconds,
    handleStartTask,
    handlePauseTask,
    handleCompleteTask,
    handleSkipTask,
    handleExtendTime,
    handleEndDay,
  } = useSession();

  const [completedOpen, setCompletedOpen] = useState(false);

  const activeTask = tasks.find((t) => t.id === activeTaskId) || null;
  const pendingTasks = tasks.filter((t) => t.status === "pending" && t.id !== activeTaskId);
  const completedTasks = tasks.filter((t) => t.status === "completed");
  const totalEstimated = tasks.reduce((s, t) => s + t.estimated_duration_minutes, 0);
  const totalActual = tasks.reduce((s, t) => s + (t.actual_duration_minutes || 0), 0);
  const activeTaskCount = tasks.filter((t) => t.status !== "cancelled" && t.status !== "skipped").length;
  const progress = activeTaskCount > 0 ? Math.round((completedTasks.length / activeTaskCount) * 100) : 0;
  const estimatedRemaining = tasks.filter((t) => t.status === "pending" || t.id === activeTaskId)
    .reduce((s, t) => s + t.estimated_duration_minutes, 0);

  const handleEndDayClick = useCallback(() => { handleEndDay(); }, [handleEndDay]);

  return (
    <div className="h-full flex flex-col max-w-[960px] mx-auto w-full">
      {/* Header */}
      <div className="flex-none px-6 pt-6 pb-5 flex items-center justify-between">
        <div>
          <h1 className="text-[var(--text-h1)] font-semibold">Dashboard</h1>
          <p className="text-sm text-[var(--color-text-secondary)] mt-1">
            {completedTasks.length}/{activeTaskCount} tasks · {progress}% complete · {formatMinutes(estimatedRemaining)} left
          </p>
        </div>
        <button onClick={handleEndDayClick} className="btn-ghost text-sm btn-press">
          End day
        </button>
      </div>

      {/* Stats row */}
      <div className="flex-none px-6 pb-4 grid grid-cols-3 gap-3">
        <div className="stat-card">
          <div className="stat-value">{completedTasks.length}<span className="text-sm font-normal text-[var(--color-text-tertiary)]">/{activeTaskCount}</span></div>
          <div className="stat-label">Completed</div>
        </div>
        <div className="stat-card">
          <div className="stat-value">{formatMinutes(totalEstimated)}</div>
          <div className="stat-label">Estimated</div>
        </div>
        <div className="stat-card">
          <div className="stat-value">
            {totalEstimated > 0 ? Math.round((totalActual / totalEstimated) * 100) : 0}
            <span className="text-sm font-normal text-[var(--color-text-tertiary)]">%</span>
          </div>
          <div className="stat-label">Accuracy</div>
        </div>
      </div>

      {/* Progress bar */}
      <div className="flex-none mx-6 h-1 rounded-full bg-[var(--color-border)] overflow-hidden mb-5">
        <div className="h-full rounded-full bg-[var(--color-primary)] transition-all duration-700 ease-out" style={{ width: `${progress}%` }} />
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto px-6 pb-6 space-y-4">
        {/* Current Task */}
        {activeTask && activeTask.status === "active" && (
          <div className="card p-5 animate-fade-in">
            <div className="flex items-center gap-2 mb-1">
              <span className="w-1.5 h-1.5 rounded-full bg-[var(--color-primary)] animate-pulse-subtle" />
              <span className="text-xs font-semibold text-[var(--color-primary)] tracking-wide">Current task</span>
            </div>
            <p className="text-sm font-semibold mb-4">{activeTask.title}</p>
            <div className="flex items-baseline gap-3 mb-4">
              <span className="font-mono text-[42px] font-semibold tracking-tight leading-none tabular-nums text-[var(--color-text)]">
                {formatTime(elapsedSeconds)}
              </span>
              <span className="text-xs text-[var(--color-text-tertiary)] pb-1">
                of {formatMinutes(activeTask.estimated_duration_minutes)}
              </span>
            </div>
            <div className="flex flex-wrap gap-1.5">
              <button onClick={() => handlePauseTask(activeTask.id)} className="btn-secondary text-xs px-3 py-1.5 btn-press">Pause</button>
              <button onClick={() => handleCompleteTask(activeTask)} className="btn-primary text-xs px-3 py-1.5 btn-press">✓ Done</button>
              <button onClick={() => handleSkipTask(activeTask)} className="btn-ghost text-xs px-2 py-1.5 btn-press">Skip</button>
              <button onClick={() => handleExtendTime(activeTask, 15)} className="btn-ghost text-xs px-2 py-1.5 btn-press">+15m</button>
              <button onClick={() => handleExtendTime(activeTask, 30)} className="btn-ghost text-xs px-2 py-1.5 btn-press">+30m</button>
            </div>
          </div>
        )}

        {/* Pending Tasks */}
        {pendingTasks.length > 0 && (
          <div>
            <div className="section-header">
              <span>Pending</span>
              <span className="font-normal text-[var(--color-text-tertiary)]">({pendingTasks.length})</span>
            </div>
            <div className="space-y-0.5">
              {pendingTasks.map((task) => (
                <div key={task.id} className="task-row card-hover group">
                  <button
                    onClick={() => handleStartTask(task)}
                    className="w-[30px] h-[30px] rounded-lg bg-[var(--color-primary)] text-white flex items-center justify-center hover:bg-[var(--color-primary-hover)] transition-colors flex-none shadow-sm btn-press"
                    title="Start"
                  >
                    <svg width="9" height="11" viewBox="0 0 9 11" fill="currentColor"><path d="M1.5 1v9l6.5-4.5z"/></svg>
                  </button>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium truncate">{task.title}</p>
                    <p className="text-xs text-[var(--color-text-tertiary)] mt-0.5">
                      {formatMinutes(task.estimated_duration_minutes)}
                      {task.carry_forward_count > 0 && <span className="ml-2 text-[var(--color-warning)]">×{task.carry_forward_count}</span>}
                    </p>
                  </div>
                  <button onClick={() => handleSkipTask(task)} className="btn-ghost text-xs opacity-0 group-hover:opacity-100 transition-opacity btn-press">Skip</button>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Completed Tasks */}
        {completedTasks.length > 0 && (
          <div>
            <button
              onClick={() => setCompletedOpen(!completedOpen)}
              className="flex items-center gap-2 text-xs font-semibold text-[var(--color-text-tertiary)] tracking-wide mb-2 hover:text-[var(--color-text-secondary)] transition-colors btn-press"
            >
              <svg width="8" height="8" viewBox="0 0 8 8" fill="currentColor" className={`transition-transform duration-150 ${completedOpen ? "" : "-rotate-90"}`}>
                <path d="M4 6L0 0h8z"/>
              </svg>
              Completed ({completedTasks.length})
            </button>
            {completedOpen && (
              <div className="space-y-0.5 animate-fade-in">
                {completedTasks.map((task) => (
                  <div key={task.id} className="task-row opacity-40">
                    <div className="w-[18px] h-[18px] rounded-md bg-[var(--color-success)] flex items-center justify-center flex-none">
                      <svg width="9" height="9" viewBox="0 0 9 9" fill="none" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                        <path d="M2 4.5L3.5 6L7 2.5" className="checkmark-path"/>
                      </svg>
                    </div>
                    <span className="text-sm line-through flex-1 truncate text-[var(--color-text-tertiary)]">{task.title}</span>
                    {task.actual_duration_minutes !== null && (
                      <span className="text-xs text-[var(--color-text-tertiary)]">{formatMinutes(task.actual_duration_minutes)}</span>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Empty state */}
        {activeTaskCount === 0 && completedTasks.length === 0 && (
          <div className="text-center py-16 animate-fade-in">
            <div className="w-10 h-10 rounded-lg bg-[var(--color-primary)]/5 flex items-center justify-center mx-auto mb-4">
              <svg width="18" height="18" viewBox="0 0 18 18" fill="none" stroke="var(--color-primary)" strokeWidth="1.5" strokeLinecap="round"><path d="M9 1v16M1 9h16"/></svg>
            </div>
            <p className="text-sm font-medium text-[var(--color-text-secondary)]">No tasks yet</p>
            <p className="text-xs text-[var(--color-text-tertiary)] mt-1">Press N to add a task, or open the sidebar.</p>
          </div>
        )}
      </div>
    </div>
  );
}
