import { useState } from "react";
import { useSession } from "../contexts/SessionContext";
import type { Priority, Task } from "../types";
import * as api from "../services/tauri";

const priorityOptions: { value: Priority; label: string }[] = [
  { value: "urgent-important", label: "Urgent & Important" },
  { value: "important", label: "Important" },
  { value: "urgent", label: "Urgent" },
];

function PriorityBadge({ priority }: { priority: string }) {
  const cls = priority === "urgent-important" ? "priority-badge-urgent-important"
    : priority === "important" ? "priority-badge-important"
    : "priority-badge-urgent";
  const label = priority === "urgent-important" ? "Urgent & Important"
    : priority === "important" ? "Important"
    : "Urgent";
  return (
    <span className={`priority-badge ${cls}`}>
      <span className={`priority-dot priority-dot-${priority}`} />
      {label}
    </span>
  );
}

export function Planning() {
  const { session, tasks, setTasks, setView } = useSession();
  const isMidDay = session?.status === "active";
  const [newTitle, setNewTitle] = useState("");
  const [newPriority, setNewPriority] = useState<Priority>("important");
  const [newEstimate, setNewEstimate] = useState(30);
  const [editingTask, setEditingTask] = useState<string | null>(null);
  const [editTitle, setEditTitle] = useState("");
  const [editPriority, setEditPriority] = useState<Priority>("important");
  const [editEstimate, setEditEstimate] = useState(30);

  if (!session) return null;

  const handleAddTask = async () => {
    if (!newTitle.trim()) return;
    try {
      const task = await api.createTask(session.id, newTitle.trim(), "", newPriority, newEstimate);
      setTasks([...tasks, task]);
      setNewTitle("");
      setNewPriority("important");
      setNewEstimate(30);
    } catch (err) {
      console.error("Failed to create task:", err);
    }
  };

  const handleDeleteTask = async (taskId: string) => {
    try {
      await api.deleteTask(taskId);
      setTasks(tasks.filter((t) => t.id !== taskId));
    } catch (err) {
      console.error("Failed to delete task:", err);
    }
  };

  const handleCompleteTask = async (task: Task) => {
    try {
      await api.updateTaskStatus(task.id, "completed");
      setTasks(tasks.map((t) => t.id === task.id ? { ...t, status: "completed" as const } : t));
    } catch (err) {
      console.error("Failed to complete task:", err);
    }
  };

  const handleSaveEdit = async (task: Task) => {
    try {
      const updated = { ...task, title: editTitle, priority: editPriority, estimated_duration_minutes: editEstimate };
      await api.updateTask(updated);
      setTasks(tasks.map((t) => (t.id === task.id ? updated : t)));
      setEditingTask(null);
    } catch (err) {
      console.error("Failed to update task:", err);
    }
  };

  const handleStartEdit = (task: Task) => {
    setEditingTask(task.id);
    setEditTitle(task.title);
    setEditPriority(task.priority as Priority);
    setEditEstimate(task.estimated_duration_minutes);
  };

  const handleMoveUp = async (index: number) => {
    if (index === 0) return;
    const newTasks = [...tasks];
    [newTasks[index - 1], newTasks[index]] = [newTasks[index], newTasks[index - 1]];
    setTasks(newTasks);
    try { await api.reorderTasks(newTasks.map((t) => t.id)); } catch { setTasks(tasks); }
  };

  const handleMoveDown = async (index: number) => {
    if (index >= tasks.length - 1) return;
    const newTasks = [...tasks];
    [newTasks[index], newTasks[index + 1]] = [newTasks[index + 1], newTasks[index]];
    setTasks(newTasks);
    try { await api.reorderTasks(newTasks.map((t) => t.id)); } catch { setTasks(tasks); }
  };

  const allTasksHaveMetadata = tasks
    .filter((t) => t.status !== "completed")
    .every((t) => t.title.trim() && t.priority && t.estimated_duration_minutes > 0);

  const pendingCount = tasks.filter((t) => t.status === "pending" || t.status === "paused").length;
  const completedCount = tasks.filter((t) => t.status === "completed").length;
  const totalEst = tasks.filter((t) => t.status !== "completed")
    .reduce((s, t) => s + t.estimated_duration_minutes, 0);

  const pendingTasks = tasks.filter((t) => t.status === "pending" || t.status === "paused")
    .sort((a, b) => a.sort_order - b.sort_order);
  const completedTasks = tasks.filter((t) => t.status === "completed");

  return (
    <div className="h-full flex flex-col max-w-[960px] mx-auto w-full">
      {/* Header */}
      <div className="flex-none px-6 pt-6 pb-4">
        <h1 className="text-[var(--text-h1)] font-semibold">Plan your day</h1>
        <p className="text-sm text-[var(--color-text-secondary)] mt-1.5">
          {pendingCount} task{pendingCount !== 1 ? "s" : ""} · {formatMinutes(totalEst)} estimated
          {completedCount > 0 && ` · ${completedCount} completed`}
        </p>
      </div>

      {/* Content: two-column on wider screens */}
      <div className="flex-1 min-h-0 flex flex-col lg:flex-row gap-4 px-6 pb-6 overflow-hidden">
        {/* Task list */}
        <div className="flex-1 min-h-0 overflow-y-auto space-y-0.5 pr-1">
          {pendingTasks.length === 0 && completedTasks.length === 0 && (
            <div className="text-center py-16">
              <p className="text-sm text-[var(--color-text-secondary)]">No tasks yet</p>
              <p className="text-xs text-[var(--color-text-tertiary)] mt-1">Add your first task below.</p>
            </div>
          )}

          {pendingTasks.map((task, index) => (
            <TaskRow
              key={task.id}
              task={task}
              index={index}
              total={pendingTasks.length}
              isEditing={editingTask === task.id}
              editTitle={editTitle}
              editPriority={editPriority}
              editEstimate={editEstimate}
              onStartEdit={() => handleStartEdit(task)}
              onSaveEdit={() => handleSaveEdit(task)}
              onCancelEdit={() => setEditingTask(null)}
              onComplete={() => handleCompleteTask(task)}
              onDelete={() => handleDeleteTask(task.id)}
              onMoveUp={() => handleMoveUp(index)}
              onMoveDown={() => handleMoveDown(index)}
              onEditTitleChange={setEditTitle}
              onEditPriorityChange={setEditPriority}
              onEditEstimateChange={setEditEstimate}
            />
          ))}

          {completedTasks.length > 0 && (
            <>
              <div className="section-header pt-4 pb-0 mb-0">
                <span>Completed</span>
                <span className="font-normal text-[var(--color-text-tertiary)]">({completedTasks.length})</span>
              </div>
              {completedTasks.map((task) => (
                <div key={task.id} className="task-row opacity-40">
                  <div className="w-[18px] h-[18px] rounded-md bg-[var(--color-success)] flex items-center justify-center flex-none">
                    <svg width="9" height="9" viewBox="0 0 9 9" fill="none" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <path d="M2 4.5L3.5 6L7 2.5" />
                    </svg>
                  </div>
                  <span className="text-sm line-through flex-1 truncate text-[var(--color-text-tertiary)]">
                    {task.title}
                  </span>
                  <span className="text-xs text-[var(--color-text-tertiary)]">{task.estimated_duration_minutes}m</span>
                </div>
              ))}
            </>
          )}
        </div>

        {/* Add task panel (right column on wide, bottom on narrow) */}
        <div className="lg:w-72 flex-none">
          <div className="card p-4 space-y-3">
            <p className="text-xs font-semibold text-[var(--color-text-secondary)] tracking-wide">Add task</p>
            <input
              type="text"
              value={newTitle}
              onChange={(e) => setNewTitle(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleAddTask()}
              placeholder="Task title…"
            />
            <div className="flex items-center gap-2">
              <select
                value={newPriority}
                onChange={(e) => setNewPriority(e.target.value as Priority)}
                className="flex-1 text-sm"
              >
                {priorityOptions.map((o) => (
                  <option key={o.value} value={o.value}>{o.label}</option>
                ))}
              </select>
              <div className="flex items-center gap-1.5 flex-none">
                <input
                  type="number"
                  value={newEstimate}
                  onChange={(e) => setNewEstimate(Math.max(1, Number(e.target.value)))}
                  className="w-14 text-center text-sm"
                  min={1}
                />
                <span className="text-xs text-[var(--color-text-tertiary)]">m</span>
              </div>
            </div>
            <button
              onClick={handleAddTask}
              disabled={!newTitle.trim()}
              className="btn-primary w-full text-sm"
            >
              + Add task
            </button>
          </div>
        </div>
      </div>

      {/* Floating action button - Review Plan */}
      {!isMidDay && (
        <button
          onClick={() => setView("commitment")}
          disabled={!allTasksHaveMetadata || pendingCount === 0}
          className="float-action"
        >
          <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
            <path d="M3 8l3 3 7-6" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
          </svg>
          Review plan
        </button>
      )}
      {isMidDay && (
        <button
          onClick={() => setView("dashboard")}
          className="float-action"
        >
          <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
            <path d="M10 4L6 8l4 4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
          </svg>
          Back to dashboard
        </button>
      )}
    </div>
  );
}

// ─── Task Row Component ───────────────────────────────────────────────────

function TaskRow({
  task, index, total, isEditing,
  editTitle, editPriority, editEstimate,
  onStartEdit, onSaveEdit, onCancelEdit,
  onComplete, onDelete, onMoveUp, onMoveDown,
  onEditTitleChange, onEditPriorityChange, onEditEstimateChange,
}: {
  task: Task; index: number; total: number; isEditing: boolean;
  editTitle: string; editPriority: Priority; editEstimate: number;
  onStartEdit: () => void; onSaveEdit: () => void; onCancelEdit: () => void;
  onComplete: () => void; onDelete: () => void;
  onMoveUp: () => void; onMoveDown: () => void;
  onEditTitleChange: (v: string) => void;
  onEditPriorityChange: (v: Priority) => void;
  onEditEstimateChange: (v: number) => void;
}) {
  if (isEditing) {
    return (
      <div className="card p-3 space-y-2 my-1 animate-fade-in">
        <input type="text" value={editTitle} onChange={(e) => onEditTitleChange(e.target.value)} placeholder="Task title" autoFocus className="text-sm" />
        <div className="flex items-center gap-2">
          <select value={editPriority} onChange={(e) => onEditPriorityChange(e.target.value as Priority)} className="flex-1 text-sm">
            {[{ v: "urgent-important" as Priority, l: "Urgent & Important" }, { v: "important" as Priority, l: "Important" }, { v: "urgent" as Priority, l: "Urgent" }].map(o => (
              <option key={o.v} value={o.v}>{o.l}</option>
            ))}
          </select>
          <div className="flex items-center gap-1.5 flex-none">
            <input type="number" value={editEstimate} onChange={(e) => onEditEstimateChange(Math.max(1, Number(e.target.value)))} className="w-14 text-center text-sm" min={1} />
            <span className="text-xs text-[var(--color-text-tertiary)]">m</span>
          </div>
        </div>
        <div className="flex gap-1.5 pt-1">
          <button onClick={onSaveEdit} className="btn-primary text-xs py-1.5 px-3">Save</button>
          <button onClick={onCancelEdit} className="btn-ghost text-xs py-1.5">Cancel</button>
        </div>
      </div>
    );
  }

  return (
    <div className="task-row card-hover group cursor-default">
      {/* Reorder */}
      <div className="flex flex-col items-center gap-px flex-none opacity-20 group-hover:opacity-60 transition-opacity">
        <button onClick={onMoveUp} disabled={index === 0} className="text-[var(--color-text-tertiary)] hover:text-[var(--color-text)] disabled:opacity-20 leading-none p-px">
          <svg width="8" height="5" viewBox="0 0 8 5" fill="currentColor"><path d="M4 0L8 5H0z"/></svg>
        </button>
        <button onClick={onMoveDown} disabled={index >= total - 1} className="text-[var(--color-text-tertiary)] hover:text-[var(--color-text)] disabled:opacity-20 leading-none p-px">
          <svg width="8" height="5" viewBox="0 0 8 5" fill="currentColor"><path d="M4 5L0 0h8z"/></svg>
        </button>
      </div>

      {/* Checkbox */}
      <button
        onClick={onComplete}
        className="w-[18px] h-[18px] rounded-md border-2 border-[var(--color-border)] hover:border-[var(--color-primary)] flex items-center justify-center flex-none transition-colors flex-shrink-0"
      />

      {/* Content */}
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium truncate">{task.title}</p>
        <div className="flex items-center gap-2 mt-1">
          <PriorityBadge priority={task.priority} />
          <span className="text-xs text-[var(--color-text-tertiary)]">{task.estimated_duration_minutes} min</span>
          {task.carry_forward_count > 0 && (
            <span className="text-xs text-[var(--color-warning)]">×{task.carry_forward_count}</span>
          )}
        </div>
      </div>

      {/* Actions */}
      <div className="flex gap-1 flex-none opacity-0 group-hover:opacity-100 transition-opacity">
        <button onClick={onStartEdit} className="btn-ghost text-xs px-2 py-1">Edit</button>
        <button onClick={onDelete} className="btn-danger text-xs px-2 py-1">Del</button>
      </div>
    </div>
  );
}

function formatMinutes(minutes: number) {
  if (minutes < 60) return `${minutes}m`;
  const h = Math.floor(minutes / 60);
  const m = minutes % 60;
  return `${h}h ${m}m`;
}
