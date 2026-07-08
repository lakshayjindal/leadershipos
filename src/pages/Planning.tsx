import { useState } from "react";
import { useSession } from "../contexts/SessionContext";
import type { Priority, Task } from "../types";
import * as api from "../services/tauri";

const priorityOptions: { value: Priority; label: string }[] = [
  { value: "urgent-important", label: "Urgent & Important" },
  { value: "important", label: "Important" },
  { value: "urgent", label: "Urgent" },
];

const priorityMeta: Record<Priority, { dot: string; label: string }> = {
  "urgent-important": { dot: "bg-red-500", label: "Urgent & Important" },
  important: { dot: "bg-blue-500", label: "Important" },
  urgent: { dot: "bg-amber-500", label: "Urgent" },
};

export function Planning() {
  const { session, tasks, setTasks, setView } = useSession();
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
      const task = await api.createTask(
        session.id,
        newTitle.trim(),
        "",
        newPriority,
        newEstimate,
      );
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
      setTasks(
        tasks.map((t) =>
          t.id === task.id ? { ...t, status: "completed" as const } : t,
        ),
      );
    } catch (err) {
      console.error("Failed to complete task:", err);
    }
  };

  const handleSaveEdit = async (task: Task) => {
    try {
      const updated = {
        ...task,
        title: editTitle,
        priority: editPriority,
        estimated_duration_minutes: editEstimate,
      };
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
    [newTasks[index - 1], newTasks[index]] = [
      newTasks[index],
      newTasks[index - 1],
    ];
    setTasks(newTasks);
    try {
      await api.reorderTasks(newTasks.map((t) => t.id));
    } catch {
      setTasks(tasks);
    }
  };

  const handleMoveDown = async (index: number) => {
    if (index >= tasks.length - 1) return;
    const newTasks = [...tasks];
    [newTasks[index], newTasks[index + 1]] = [
      newTasks[index + 1],
      newTasks[index],
    ];
    setTasks(newTasks);
    try {
      await api.reorderTasks(newTasks.map((t) => t.id));
    } catch {
      setTasks(tasks);
    }
  };

  const allTasksHaveMetadata = tasks
    .filter((t) => t.status !== "completed")
    .every(
      (t) => t.title.trim() && t.priority && t.estimated_duration_minutes > 0,
    );

  const pendingTasks = tasks.filter(
    (t) => t.status === "pending" || t.status === "paused",
  );
  const completedTasks = tasks.filter((t) => t.status === "completed");
  const sortedTasks = [
    ...pendingTasks.sort((a, b) => a.sort_order - b.sort_order),
    ...completedTasks,
  ];

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="flex-none px-8 pt-8 pb-4">
        <h1 className="text-[var(--text-h1)] font-semibold">Plan your day</h1>
        <p className="text-[var(--color-text-secondary)] mt-1.5 text-[var(--text-body)]">
          Set your priorities and estimate each task's duration.
        </p>
      </div>

      {/* Task list */}
      <div className="flex-1 overflow-y-auto px-8 pb-4 space-y-3">
        {sortedTasks.map((task, index) => {
          const isCompleted = task.status === "completed";
          const meta = priorityMeta[task.priority as Priority] || priorityMeta.important;

          if (editingTask === task.id) {
            return (
              <div
                key={task.id}
                className="rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] p-5 shadow-sm space-y-4"
              >
                <input
                  type="text"
                  value={editTitle}
                  onChange={(e) => setEditTitle(e.target.value)}
                  placeholder="Task title"
                  autoFocus
                />
                <div className="flex items-center gap-3">
                  <select
                    value={editPriority}
                    onChange={(e) => setEditPriority(e.target.value as Priority)}
                    className="flex-1"
                  >
                    {priorityOptions.map((o) => (
                      <option key={o.value} value={o.value}>
                        {o.label}
                      </option>
                    ))}
                  </select>
                  <div className="flex items-center gap-2">
                    <input
                      type="number"
                      value={editEstimate}
                      onChange={(e) =>
                        setEditEstimate(Math.max(1, Number(e.target.value)))
                      }
                      className="w-20 text-center"
                      min={1}
                    />
                    <span className="text-sm text-[var(--color-text-tertiary)]">
                      min
                    </span>
                  </div>
                </div>
                <div className="flex gap-2">
                  <button
                    onClick={() => handleSaveEdit(task)}
                    className="btn-primary text-sm px-4 py-2"
                  >
                    Save
                  </button>
                  <button
                    onClick={() => setEditingTask(null)}
                    className="btn-ghost text-sm"
                  >
                    Cancel
                  </button>
                </div>
              </div>
            );
          }

          return (
            <div
              key={task.id}
              className={`rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] p-4 shadow-sm transition-all duration-150 ${
                isCompleted ? "opacity-50" : "hover:shadow-md"
              }`}
            >
              <div className="flex items-center gap-4">
                {/* Reorder */}
                <div className="flex flex-col gap-0.5 flex-none">
                  <button
                    onClick={() => handleMoveUp(index)}
                    disabled={index === 0 || isCompleted}
                    className="text-[var(--color-text-tertiary)] hover:text-[var(--color-text)] disabled:opacity-20 transition-colors leading-none cursor-pointer disabled:cursor-default"
                  >
                    <svg width="10" height="6" viewBox="0 0 10 6" fill="currentColor"><path d="M5 0L10 6H0z"/></svg>
                  </button>
                  <button
                    onClick={() => handleMoveDown(index)}
                    disabled={index >= sortedTasks.length - 1 || isCompleted}
                    className="text-[var(--color-text-tertiary)] hover:text-[var(--color-text)] disabled:opacity-20 transition-colors leading-none cursor-pointer disabled:cursor-default"
                  >
                    <svg width="10" height="6" viewBox="0 0 10 6" fill="currentColor"><path d="M5 6L0 0h10z"/></svg>
                  </button>
                </div>

                {/* Checkbox */}
                <button
                  onClick={() => handleCompleteTask(task)}
                  className={`w-5 h-5 rounded-md border-2 flex items-center justify-center flex-none transition-all duration-150 cursor-pointer ${
                    isCompleted
                      ? "border-[var(--color-success)] bg-[var(--color-success)]"
                      : "border-[var(--color-border)] hover:border-[var(--color-primary)]"
                  }`}
                >
                  {isCompleted && (
                    <svg width="10" height="10" viewBox="0 0 10 10" fill="none" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <path d="M2 5L4 7L8 3"/>
                    </svg>
                  )}
                </button>

                {/* Content */}
                <div className="flex-1 min-w-0">
                  <p
                    className={`text-sm font-medium ${
                      isCompleted
                        ? "line-through text-[var(--color-text-tertiary)]"
                        : "text-[var(--color-text)]"
                    }`}
                  >
                    {task.title}
                  </p>
                  {!isCompleted && (
                    <div className="flex items-center gap-3 mt-1.5">
                      <span className="flex items-center gap-1.5">
                        <span className={`w-1.5 h-1.5 rounded-full ${meta.dot}`} />
                        <span className="text-xs text-[var(--color-text-tertiary)]">
                          {meta.label}
                        </span>
                      </span>
                      <span className="text-xs text-[var(--color-text-tertiary)]">
                        {task.estimated_duration_minutes}m
                      </span>
                      {task.carry_forward_count > 0 && (
                        <span className="text-xs text-[var(--color-warning)]">
                          Carried&nbsp;forward&nbsp;×{task.carry_forward_count}
                        </span>
                      )}
                    </div>
                  )}
                </div>

                {/* Actions */}
                {!isCompleted && (
                  <div className="flex gap-1.5 flex-none">
                    <button
                      onClick={() => handleStartEdit(task)}
                      className="btn-ghost text-xs px-2 py-1"
                    >
                      Edit
                    </button>
                    <button
                      onClick={() => handleDeleteTask(task.id)}
                      className="btn-danger text-xs px-2 py-1"
                    >
                      Delete
                    </button>
                  </div>
                )}
              </div>
            </div>
          );
        })}

        {/* Add new task */}
        <div className="rounded-xl border border-dashed border-[var(--color-border)] bg-[var(--color-surface)] p-5 space-y-4">
          <input
            type="text"
            value={newTitle}
            onChange={(e) => setNewTitle(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleAddTask()}
            placeholder="Add a new task…"
          />
          <div className="flex items-center gap-3">
            <select
              value={newPriority}
              onChange={(e) => setNewPriority(e.target.value as Priority)}
              className="flex-1"
            >
              {priorityOptions.map((o) => (
                <option key={o.value} value={o.value}>
                  {o.label}
                </option>
              ))}
            </select>
            <div className="flex items-center gap-2">
              <input
                type="number"
                value={newEstimate}
                onChange={(e) =>
                  setNewEstimate(Math.max(1, Number(e.target.value)))
                }
                className="w-20 text-center"
                min={1}
              />
              <span className="text-sm text-[var(--color-text-tertiary)]">min</span>
            </div>
            <button
              onClick={handleAddTask}
              disabled={!newTitle.trim()}
              className="btn-primary text-sm px-5 py-2"
            >
              Add
            </button>
          </div>
        </div>
      </div>

      {/* Footer */}
      <div className="flex-none px-8 py-5 border-t border-[var(--color-border)]">
        <button
          onClick={() => setView("commitment")}
          disabled={
            !allTasksHaveMetadata ||
            tasks.filter((t) => t.status !== "completed").length === 0
          }
          className="btn-primary w-full"
        >
          Review plan
        </button>
      </div>
    </div>
  );
}
