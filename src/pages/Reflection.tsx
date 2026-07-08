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
    (t) => t.status === "pending" || t.status === "active" || t.status === "paused",
  );

  const handleSubmit = async () => {
    setSaving(true);
    try {
      await api.saveReflection(session.id, wentWell, wentWrong, improve);
      for (const task of unfinishedTasks) {
        await api.updateTaskStatus(task.id, showCarryForward ? "pending" : "cancelled");
      }
      await api.endDay(session.id);
      try {
        const path = await api.generateDailyNote(session.id);
        setGeneratedPath(path);
      } catch {
        setGeneratedPath("(could not write file — check vault path in settings)");
      }
    } catch (err) {
      console.error("Failed to save reflection:", err);
    } finally {
      setSaving(false);
    }
  };

  const handleClose = () => setView("welcome");

  return (
    <div className="h-full flex flex-col max-w-[700px] mx-auto w-full">
      <div className="flex-none px-6 pt-6 pb-5">
        <h1 className="text-[var(--text-h1)] font-semibold">Reflect on your day</h1>
        <p className="text-sm text-[var(--color-text-secondary)] mt-1.5">
          Honest reflection is how leaders grow.
        </p>
      </div>

      <div className="flex-1 overflow-y-auto px-6 pb-4 space-y-6">
        {/* Unfinished tasks */}
        {unfinishedTasks.length > 0 && (
          <div className="card p-4 space-y-3">
            <p className="text-sm font-semibold">Unfinished tasks</p>
            <ul className="space-y-1.5">
              {unfinishedTasks.map((task) => (
                <li key={task.id} className="flex items-center gap-2 text-sm text-[var(--color-text-secondary)]">
                  <span className="w-1 h-1 rounded-full bg-[var(--color-warning)]" />
                  {task.title}
                </li>
              ))}
            </ul>
            <div className="flex gap-4 pt-1">
              <label className="flex items-center gap-2 text-sm cursor-pointer">
                <input type="radio" name="carry" checked={showCarryForward} onChange={() => setShowCarryForward(true)} className="w-3.5 h-3.5 accent-[var(--color-primary)]" />
                Carry forward
              </label>
              <label className="flex items-center gap-2 text-sm cursor-pointer">
                <input type="radio" name="carry" checked={!showCarryForward} onChange={() => setShowCarryForward(false)} className="w-3.5 h-3.5 accent-[var(--color-danger)]" />
                Mark cancelled
              </label>
            </div>
          </div>
        )}

        {/* Questions */}
        <div className="space-y-5">
          <div>
            <label htmlFor="ww">What went well?</label>
            <textarea id="ww" value={wentWell} onChange={(e) => setWentWell(e.target.value)} rows={3} placeholder="Celebrate your wins — what worked today?" />
          </div>
          <div>
            <label htmlFor="wwr">What went wrong?</label>
            <textarea id="wwr" value={wentWrong} onChange={(e) => setWentWrong(e.target.value)} rows={3} placeholder="What challenges did you face?" />
          </div>
          <div>
            <label htmlFor="imp">What could be improved?</label>
            <textarea id="imp" value={improve} onChange={(e) => setImprove(e.target.value)} rows={3} placeholder="What would you do differently next time?" />
          </div>
        </div>

        {/* Success */}
        {generatedPath && (
          <div className="card p-4 border-[var(--color-success)]/20 bg-[var(--color-success-subtle)]">
            <p className="text-sm font-medium text-[var(--color-success)]">Session completed</p>
            <p className="text-xs text-[var(--color-text-secondary)] mt-0.5">Daily note saved to: {generatedPath}</p>
          </div>
        )}

        {/* Confirm skip */}
        {confirmSkip && (
          <div className="card p-4 border-[var(--color-warning)]/20 bg-[var(--color-warning-subtle)]">
            <p className="text-sm mb-3">Reflection helps you grow. Are you sure?</p>
            <div className="flex gap-2">
              <button onClick={() => setConfirmSkip(false)} className="btn-secondary text-sm px-4 py-2">Continue</button>
              <button onClick={handleSubmit} className="btn-primary text-sm px-4 py-2">Submit anyway</button>
            </div>
          </div>
        )}
      </div>

      {/* Footer */}
      <div className="flex-none px-6 py-4 border-t border-[var(--color-border)] flex gap-2">
        {generatedPath ? (
          <button onClick={handleClose} className="btn-primary w-full btn-press">Close</button>
        ) : (
          <>
            <button onClick={() => setConfirmSkip(true)} disabled={saving} className="btn-secondary flex-1 btn-press">
              Skip
            </button>
            <button onClick={handleSubmit} disabled={saving} className="btn-primary flex-[2] btn-press">
              {saving ? "Saving…" : "Submit reflection"}
            </button>
          </>
        )}
      </div>
    </div>
  );
}
