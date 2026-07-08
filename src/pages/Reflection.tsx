import { useState } from "react";
import { useSession } from "../contexts/SessionContext";
import * as api from "../services/tauri";

export function ReflectionPage() {
  const { session, tasks, setView } = useSession();
  const [wentWell, setWentWell] = useState("");
  const [wentWrong, setWentWrong] = useState("");
  const [improve, setImprove] = useState("");
  const [saving, setSaving] = useState(false);
  const [confirmSkip, setConfirmSkip] = useState(false);
  const [generatedPath, setGeneratedPath] = useState<string | null>(null);
  const [showCarryForward, setShowCarryForward] = useState(true);

  if (!session) return null;

  const unfinishedTasks = tasks.filter(
    (t) =>
      t.status === "pending" ||
      t.status === "active" ||
      t.status === "paused",
  );

  const handleSubmit = async () => {
    setSaving(true);
    try {
      await api.saveReflection(session.id, wentWell, wentWrong, improve);

      for (const task of unfinishedTasks) {
        if (showCarryForward) {
          await api.updateTaskStatus(task.id, "pending");
        } else {
          await api.updateTaskStatus(task.id, "cancelled");
        }
      }

      await api.endDay(session.id);

      try {
        const path = await api.generateDailyNote(session.id);
        setGeneratedPath(path);
      } catch {
        setGeneratedPath(
          "(could not write file — check vault path in settings)",
        );
      }
    } catch (err) {
      console.error("Failed to save reflection:", err);
    } finally {
      setSaving(false);
    }
  };

  const handleClose = () => {
    setView("welcome");
  };

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="flex-none px-8 pt-8 pb-4">
        <h1 className="text-[var(--text-h1)] font-semibold">Reflect on your day</h1>
        <p className="text-[var(--color-text-secondary)] mt-1.5 text-[var(--text-body)]">
          Honest reflection is how leaders grow.
        </p>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto px-8 pb-4 space-y-8">
        {/* Unfinished tasks */}
        {unfinishedTasks.length > 0 && (
          <div className="rounded-xl bg-[var(--color-surface)] border border-[var(--color-border)] p-5 shadow-sm space-y-4">
            <h2 className="text-sm font-medium">Unfinished tasks</h2>
            <ul className="space-y-2">
              {unfinishedTasks.map((task) => (
                <li
                  key={task.id}
                  className="flex items-center gap-2.5 text-sm text-[var(--color-text-secondary)]"
                >
                  <span className="w-1.5 h-1.5 rounded-full bg-[var(--color-warning)]" />
                  {task.title}
                </li>
              ))}
            </ul>
            <div className="flex gap-6 pt-1">
              <label className="flex items-center gap-2.5 text-sm cursor-pointer">
                <input
                  type="radio"
                  name="carryAction"
                  checked={showCarryForward}
                  onChange={() => setShowCarryForward(true)}
                  className="w-4 h-4 accent-[var(--color-primary)]"
                />
                Carry forward
              </label>
              <label className="flex items-center gap-2.5 text-sm cursor-pointer">
                <input
                  type="radio"
                  name="carryAction"
                  checked={!showCarryForward}
                  onChange={() => setShowCarryForward(false)}
                  className="w-4 h-4 accent-[var(--color-danger)]"
                />
                Mark cancelled
              </label>
            </div>
          </div>
        )}

        {/* Reflection questions */}
        <div className="space-y-6">
          <div className="space-y-2">
            <label htmlFor="wentWell">What went well?</label>
            <textarea
              id="wentWell"
              value={wentWell}
              onChange={(e) => setWentWell(e.target.value)}
              rows={4}
              placeholder="Celebrate your wins — what worked today?"
            />
          </div>
          <div className="space-y-2">
            <label htmlFor="wentWrong">What went wrong?</label>
            <textarea
              id="wentWrong"
              value={wentWrong}
              onChange={(e) => setWentWrong(e.target.value)}
              rows={4}
              placeholder="What challenges did you face? Be honest."
            />
          </div>
          <div className="space-y-2">
            <label htmlFor="improve">What could be improved?</label>
            <textarea
              id="improve"
              value={improve}
              onChange={(e) => setImprove(e.target.value)}
              rows={4}
              placeholder="What would you do differently next time?"
            />
          </div>
        </div>

        {/* Success */}
        {generatedPath && (
          <div className="rounded-xl bg-[var(--color-success-subtle)] border border-[var(--color-success)]/20 p-5 space-y-1.5">
            <p className="text-sm font-medium text-[var(--color-success)]">
              Session completed
            </p>
            <p className="text-xs text-[var(--color-text-secondary)]">
              Daily note saved to: {generatedPath}
            </p>
          </div>
        )}

        {/* Confirm skip */}
        {confirmSkip && (
          <div className="rounded-xl bg-[var(--color-warning-subtle)] border border-[var(--color-warning)]/20 p-5 space-y-4">
            <p className="text-sm">
              Reflection helps you grow as a leader. Are you sure?
            </p>
            <div className="flex gap-2">
              <button
                onClick={() => setConfirmSkip(false)}
                className="btn-secondary text-sm px-4 py-2"
              >
                Continue reflecting
              </button>
              <button
                onClick={handleSubmit}
                className="btn-primary text-sm px-4 py-2"
              >
                Submit anyway
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Footer */}
      <div className="flex-none px-8 py-5 border-t border-[var(--color-border)] flex gap-3">
        {generatedPath ? (
          <button onClick={handleClose} className="btn-primary w-full">
            Close
          </button>
        ) : (
          <>
            <button
              onClick={() => setConfirmSkip(true)}
              disabled={saving}
              className="btn-secondary flex-1"
            >
              Skip reflection
            </button>
            <button
              onClick={handleSubmit}
              disabled={saving}
              className="btn-primary flex-1"
            >
              {saving ? "Saving…" : "Submit reflection"}
            </button>
          </>
        )}
      </div>
    </div>
  );
}
