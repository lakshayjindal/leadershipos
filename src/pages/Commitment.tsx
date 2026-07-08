import { useSession } from "../contexts/SessionContext";
import type { Priority } from "../types";

export function Commitment() {
  const { tasks, handleStartDay, setView } = useSession();

  const priorityTasks = (p: Priority) =>
    tasks.filter((t) => t.priority === p && t.status !== "completed");

  const urgentImportant = priorityTasks("urgent-important");
  const important = priorityTasks("important");
  const urgent = priorityTasks("urgent");

  const totalEstimated = tasks
    .filter((t) => t.status !== "completed")
    .reduce((sum, t) => sum + t.estimated_duration_minutes, 0);

  const pendingCount = tasks.filter((t) => t.status !== "completed").length;

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="flex-none px-8 pt-8 pb-4">
        <h1 className="text-[var(--text-h1)] font-semibold">Commit to your day</h1>
        <p className="text-[var(--color-text-secondary)] mt-1.5 text-[var(--text-body)]">
          Review your plan before starting — the timer begins when you do.
        </p>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto px-8 pb-4 space-y-8">
        {/* Summary stats — visual rhythm: large numbers */}
        <div className="grid grid-cols-3 gap-4">
          <div className="rounded-xl bg-[var(--color-surface)] border border-[var(--color-border)] p-5 text-center shadow-sm">
            <p className="text-[28px] font-semibold tracking-tight">{pendingCount}</p>
            <p className="text-xs text-[var(--color-text-tertiary)] mt-1.5 uppercase tracking-wider font-medium">
              Tasks
            </p>
          </div>
          <div className="rounded-xl bg-[var(--color-surface)] border border-[var(--color-border)] p-5 text-center shadow-sm">
            <p className="text-[28px] font-semibold tracking-tight">
              {totalEstimated}
              <span className="text-sm font-normal text-[var(--color-text-tertiary)] ml-0.5">m</span>
            </p>
            <p className="text-xs text-[var(--color-text-tertiary)] mt-1.5 uppercase tracking-wider font-medium">
              Estimated
            </p>
          </div>
          <div className="rounded-xl bg-[var(--color-surface)] border border-[var(--color-border)] p-5 text-center shadow-sm">
            <p className="text-[28px] font-semibold tracking-tight">
              {urgentImportant.length + important.length + urgent.length}
            </p>
            <p className="text-xs text-[var(--color-text-tertiary)] mt-1.5 uppercase tracking-wider font-medium">
              Active
            </p>
          </div>
        </div>

        {/* Priority sections — visual rhythm: medium */}
        {urgentImportant.length > 0 && (
          <section>
            <div className="flex items-center gap-2 mb-3">
              <span className="w-2 h-2 rounded-full bg-red-500" />
              <h3 className="text-sm font-medium text-[var(--color-text)]">
                Urgent & Important
              </h3>
            </div>
            <div className="space-y-2">
              {urgentImportant.map((task) => (
                <div
                  key={task.id}
                  className="rounded-xl bg-[var(--color-surface)] border border-[var(--color-border)] p-4 shadow-sm"
                >
                  <p className="text-sm font-medium">{task.title}</p>
                  <p className="text-xs text-[var(--color-text-tertiary)] mt-1">
                    {task.estimated_duration_minutes} min
                  </p>
                </div>
              ))}
            </div>
          </section>
        )}

        {important.length > 0 && (
          <section>
            <div className="flex items-center gap-2 mb-3">
              <span className="w-2 h-2 rounded-full bg-blue-500" />
              <h3 className="text-sm font-medium text-[var(--color-text)]">
                Important
              </h3>
            </div>
            <div className="space-y-2">
              {important.map((task) => (
                <div
                  key={task.id}
                  className="rounded-xl bg-[var(--color-surface)] border border-[var(--color-border)] p-4 shadow-sm"
                >
                  <p className="text-sm font-medium">{task.title}</p>
                  <p className="text-xs text-[var(--color-text-tertiary)] mt-1">
                    {task.estimated_duration_minutes} min
                  </p>
                </div>
              ))}
            </div>
          </section>
        )}

        {urgent.length > 0 && (
          <section>
            <div className="flex items-center gap-2 mb-3">
              <span className="w-2 h-2 rounded-full bg-amber-500" />
              <h3 className="text-sm font-medium text-[var(--color-text)]">
                Urgent
              </h3>
            </div>
            <div className="space-y-2">
              {urgent.map((task) => (
                <div
                  key={task.id}
                  className="rounded-xl bg-[var(--color-surface)] border border-[var(--color-border)] p-4 shadow-sm"
                >
                  <p className="text-sm font-medium">{task.title}</p>
                  <p className="text-xs text-[var(--color-text-tertiary)] mt-1">
                    {task.estimated_duration_minutes} min
                  </p>
                </div>
              ))}
            </div>
          </section>
        )}
      </div>

      {/* Footer */}
      <div className="flex-none px-8 py-5 border-t border-[var(--color-border)] flex gap-3">
        <button
          onClick={() => setView("planning")}
          className="btn-secondary flex-1"
        >
          Back
        </button>
        <button onClick={handleStartDay} className="btn-primary flex-1">
          Start my day
        </button>
      </div>
    </div>
  );
}
