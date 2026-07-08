import { useSession } from "../contexts/SessionContext";
import type { Priority } from "../types";

export function Commitment() {
  const { tasks, handleStartDay, setView } = useSession();

  const priorityTasks = (p: Priority) => tasks.filter((t) => t.priority === p && t.status !== "completed");

  const urgentImportant = priorityTasks("urgent-important");
  const important = priorityTasks("important");
  const urgent = priorityTasks("urgent");

  const totalEstimated = tasks.filter((t) => t.status !== "completed")
    .reduce((sum, t) => sum + t.estimated_duration_minutes, 0);
  const pendingCount = tasks.filter((t) => t.status !== "completed").length;

  return (
    <div className="h-full flex flex-col max-w-[700px] mx-auto w-full">
      {/* Header */}
      <div className="flex-none px-6 pt-6 pb-5">
        <h1 className="text-[var(--text-h1)] font-semibold">Commit to your day</h1>
        <p className="text-sm text-[var(--color-text-secondary)] mt-1.5">
          Review your plan. The timer starts when you begin.
        </p>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto px-6 pb-4 space-y-6">
        {/* Stats */}
        <div className="grid grid-cols-3 gap-3">
          <div className="stat-card text-center">
            <div className="stat-value">{pendingCount}</div>
            <div className="stat-label">Tasks</div>
          </div>
          <div className="stat-card text-center">
            <div className="stat-value">{totalEstimated}<span className="text-sm font-normal text-[var(--color-text-tertiary)] ml-0.5">m</span></div>
            <div className="stat-label">Estimated</div>
          </div>
          <div className="stat-card text-center">
            <div className="stat-value">{urgentImportant.length + important.length + urgent.length}</div>
            <div className="stat-label">Active</div>
          </div>
        </div>

        {/* Priority sections */}
        {urgentImportant.length > 0 && (
          <section>
            <div className="section-header">
              <span className="w-1.5 h-1.5 rounded-full bg-[var(--color-danger)]" />
              Urgent & Important
            </div>
            <div className="space-y-1.5">
              {urgentImportant.map((task) => (
                <div key={task.id} className="task-row card-hover">
                  <span className="text-sm font-medium truncate">{task.title}</span>
                  <span className="text-xs text-[var(--color-text-tertiary)] flex-none">{task.estimated_duration_minutes}m</span>
                </div>
              ))}
            </div>
          </section>
        )}

        {important.length > 0 && (
          <section>
            <div className="section-header">
              <span className="w-1.5 h-1.5 rounded-full bg-[var(--color-primary)]" />
              Important
            </div>
            <div className="space-y-1.5">
              {important.map((task) => (
                <div key={task.id} className="task-row card-hover">
                  <span className="text-sm font-medium truncate">{task.title}</span>
                  <span className="text-xs text-[var(--color-text-tertiary)] flex-none">{task.estimated_duration_minutes}m</span>
                </div>
              ))}
            </div>
          </section>
        )}

        {urgent.length > 0 && (
          <section>
            <div className="section-header">
              <span className="w-1.5 h-1.5 rounded-full bg-[var(--color-warning)]" />
              Urgent
            </div>
            <div className="space-y-1.5">
              {urgent.map((task) => (
                <div key={task.id} className="task-row card-hover">
                  <span className="text-sm font-medium truncate">{task.title}</span>
                  <span className="text-xs text-[var(--color-text-tertiary)] flex-none">{task.estimated_duration_minutes}m</span>
                </div>
              ))}
            </div>
          </section>
        )}
      </div>

      {/* Actions */}
      <div className="flex-none px-6 py-4 border-t border-[var(--color-border)] flex gap-2">
        <button onClick={() => setView("planning")} className="btn-secondary flex-1 btn-press">
          Back
        </button>
        <button onClick={handleStartDay} className="btn-primary flex-[2] btn-press">
          Start my day
        </button>
      </div>
    </div>
  );
}
