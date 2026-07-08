import { useState, useRef, useEffect } from "react";
import type { Priority } from "../types";
import { useSession } from "../contexts/SessionContext";
import * as api from "../services/tauri";

const priorityOptions: { value: Priority; label: string }[] = [
  { value: "urgent-important", label: "Urgent & Important" },
  { value: "important", label: "Important" },
  { value: "urgent", label: "Urgent" },
];

interface QuickAddModalProps {
  open: boolean;
  onClose: () => void;
}

export function QuickAddModal({ open, onClose }: QuickAddModalProps) {
  const { session, tasks, setTasks, settings } = useSession();
  const [title, setTitle] = useState("");
  const [priority, setPriority] = useState<Priority>("important");
  const [estimate, setEstimate] = useState(30);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (open && inputRef.current) {
      setTimeout(() => inputRef.current?.focus(), 50);
    }
  }, [open]);

  useEffect(() => {
    if (!open) {
      setTitle("");
      setPriority("important");
      if (settings) setEstimate(settings.default_task_duration_minutes);
    }
  }, [open, settings]);

  const handleSubmit = async () => {
    if (!title.trim() || !session) return;
    try {
      const task = await api.createTask(
        session.id,
        title.trim(),
        "",
        priority,
        estimate,
      );
      setTasks([...tasks, task]);
      onClose();
    } catch (err) {
      console.error("Failed to create task:", err);
    }
  };

  if (!open) return null;

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal-panel p-5" onClick={(e) => e.stopPropagation()}>
        <p className="text-xs font-semibold text-[var(--color-text-secondary)] tracking-wide mb-4">
          Add a new task
        </p>
        <input
          ref={inputRef}
          type="text"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter") handleSubmit();
            if (e.key === "Escape") onClose();
          }}
          placeholder="What are you working on?"
          className="mb-3"
        />
        <div className="flex items-center gap-3 mb-4">
          <select
            value={priority}
            onChange={(e) => setPriority(e.target.value as Priority)}
            className="flex-1 text-sm"
          >
            {priorityOptions.map((o) => (
              <option key={o.value} value={o.value}>
                {o.label}
              </option>
            ))}
          </select>
          <div className="flex items-center gap-1.5 flex-none">
            <input
              type="number"
              value={estimate}
              onChange={(e) => setEstimate(Math.max(1, Number(e.target.value)))}
              className="w-16 text-center text-sm"
              min={1}
            />
            <span className="text-xs text-[var(--color-text-tertiary)]">min</span>
          </div>
        </div>
        <div className="flex gap-2">
          <button onClick={onClose} className="btn-ghost text-sm flex-1 py-2">
            Cancel
          </button>
          <button
            onClick={handleSubmit}
            disabled={!title.trim()}
            className="btn-primary text-sm flex-1 py-2"
          >
            Add task
          </button>
        </div>
      </div>
    </div>
  );
}
