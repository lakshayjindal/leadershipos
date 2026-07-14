import { useState, useEffect } from 'react';
import type { Task, Priority } from '../types';
import { getTasks, getToday, startTask, formatDuration, getPriorityColor, createTask } from '../utils';
import { useAppStore } from '../store';
import { useToast } from '../components/Toast';
import TaskEditModal from '../components/TaskEditModal';

export default function WorkingWorkspace() {
  const { todayStatus } = useAppStore();
  const { addToast } = useToast();

  const [tasks, setTasks] = useState<Task[]>([]);
  const [dayId, setDayId] = useState(todayStatus?.day?.id || '');
  const [loading, setLoading] = useState(true);
  const [editingTask, setEditingTask] = useState<Task | null>(null);
  const [showNewTask, setShowNewTask] = useState(false);
  const [newTitle, setNewTitle] = useState('');
  const [newPriority, setNewPriority] = useState<Priority>('medium');

  const activeTask = todayStatus?.active_task;

  useEffect(() => {
    loadTasks();
  }, []);

  async function loadTasks() {
    try {
      const day = await getToday();
      setDayId(day.id);
      const loaded = await getTasks(day.id);
      setTasks(loaded.filter(t => t.status !== 'deleted'));
    } catch (e) {
      console.error('Failed to load tasks:', e);
    } finally {
      setLoading(false);
    }
  }

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    if (!newTitle.trim() || !dayId) return;
    try {
      const task = await createTask(dayId, {
        title: newTitle.trim(), priority: newPriority,
        description: null, deadline: null, estimated_duration_minutes: null, notes: null,
      });
      setTasks(prev => [...prev, task]);
      setNewTitle('');
      setShowNewTask(false);
      addToast('Task created', 'success');
    } catch (e) {
      addToast('Failed to create task', 'error');
    }
  }

  // Get the task to focus on next (first pending or paused that isn't active)
  const nextTask = tasks.find(t =>
    t.status === 'pending' || t.status === 'carried_forward'
  );

  const workingTasks = tasks.filter(t => t.status === 'active' || t.status === 'paused');
  const pendingTasks = tasks.filter(t => t.status === 'pending' || t.status === 'carried_forward');
  const completedTasks = tasks.filter(t => t.status === 'completed');

  if (loading) {
    return <div className="empty-state"><div className="empty-state-icon">⏳</div><div>Loading...</div></div>;
  }

  return (
    <div className="working-workspace">
      {/* Quick add task */}
      <div style={{ marginBottom: 16 }}>
        {showNewTask ? (
          <div className="card" style={{ padding: '8px 12px' }}>
            <form onSubmit={handleCreate} className="flex gap-2 items-center">
              <input
                className="form-input"
                style={{ flex: 1 }}
                placeholder="Quick add task..."
                value={newTitle}
                onChange={e => setNewTitle(e.target.value)}
                autoFocus
              />
              <select className="form-select" style={{ width: 100 }} value={newPriority}
                onChange={e => setNewPriority(e.target.value as Priority)}>
                <option value="critical">Critical</option>
                <option value="high">High</option>
                <option value="medium">Medium</option>
                <option value="low">Low</option>
              </select>
              <button className="btn btn-primary btn-sm" type="submit">Add</button>
              <button className="btn btn-ghost btn-sm" type="button" onClick={() => setShowNewTask(false)}>✕</button>
            </form>
          </div>
        ) : (
          <button className="btn btn-ghost btn-sm" onClick={() => setShowNewTask(true)}>
            + Quick Add Task
          </button>
        )}
      </div>

      {/* Task Queue */}
      {tasks.filter(t => t.status !== 'deleted').length === 0 ? (
        <div className="card">
          <div className="empty-state" style={{ padding: 24 }}>
            <div className="empty-state-icon">☐</div>
            <div className="empty-state-title">No Tasks</div>
            <div className="empty-state-desc">Create a task to get started.</div>
          </div>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
          {/* Active Task first */}
          {activeTask && (
            <>
              <div style={{ fontSize: 11, fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.05em', color: 'var(--color-text-secondary)' }}>
                Current Task
              </div>
              <TaskQueueItem task={activeTask} isActive={true} onRefresh={loadTasks} />
            </>
          )}

          {/* Pending Tasks */}
          {pendingTasks.length > 0 && (
            <>
              <div style={{ fontSize: 11, fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.05em', color: 'var(--color-text-secondary)', marginTop: 12 }}>
                Ready ({pendingTasks.length})
              </div>
              {pendingTasks.map(task => (
                <TaskQueueItem key={task.id} task={task} isActive={false} onRefresh={loadTasks} />
              ))}
            </>
          )}

          {/* Paused tasks */}
          {workingTasks.filter(t => t.status === 'paused').length > 0 && (
            <>
              <div style={{ fontSize: 11, fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.05em', color: 'var(--color-text-secondary)', marginTop: 12 }}>
                Paused
              </div>
              {workingTasks.filter(t => t.status === 'paused').map(task => (
                <TaskQueueItem key={task.id} task={task} isActive={false} onRefresh={loadTasks} />
              ))}
            </>
          )}

          {/* Completed (collapsed) */}
          {completedTasks.length > 0 && (
            <>
              <div style={{ fontSize: 11, fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.05em', color: 'var(--color-text-secondary)', marginTop: 12 }}>
                Completed ({completedTasks.length})
              </div>
              {completedTasks.slice(0, 5).map(task => (
                <TaskQueueItem key={task.id} task={task} isActive={false} onRefresh={loadTasks} />
              ))}
              {completedTasks.length > 5 && (
                <div className="text-xs text-muted" style={{ textAlign: 'center', padding: 4 }}>
                  +{completedTasks.length - 5} more
                </div>
              )}
            </>
          )}
        </div>
      )}

      {/* Edit modal */}
      {editingTask && (
        <TaskEditModal
          task={editingTask}
          onClose={() => setEditingTask(null)}
          onSaved={loadTasks}
        />
      )}
    </div>
  );
}

// ─── Task Queue Item ──────────────────────────────────────────────

function TaskQueueItem({ task, isActive, onRefresh }: {
  task: Task; isActive: boolean; onRefresh: () => Promise<void>;
}) {
  const { setCurrentState } = useAppStore();
  const { addToast } = useToast();

  async function handleFocus() {
    try {
      await startTask(task.id);
      setCurrentState('working');
      await onRefresh();
    } catch (e) {
      addToast('Failed to start task', 'error');
    }
  }

  return (
    <div
      className="task-item-card"
      style={{
        borderLeft: `3px solid ${getPriorityColor(task.priority)}`,
        opacity: isActive ? 1 : 0.85,
      }}
    >
      <div className="task-item-row">
        <div style={{ flex: 1, minWidth: 0 }}>
          <div className={`task-title ${task.status === 'completed' ? 'completed' : ''}`}
            style={{ fontWeight: isActive ? 600 : 400, color: isActive ? 'var(--color-primary)' : undefined }}>
            {isActive ? '◉ ' : ''}{task.title}
          </div>
          <div className="task-meta" style={{ marginTop: 2 }}>
            <span className={`badge badge-${task.priority}`} style={{ fontSize: 10 }}>{task.priority}</span>
            <span className={`task-status-badge status-${task.status}`} style={{ fontSize: 10 }}>
              {task.status === 'active' ? '● Working' :
               task.status === 'paused' ? '⏸ Paused' :
               task.status === 'completed' ? '✓ Done' :
               '○ Pending'}
            </span>
            {task.actual_duration_seconds > 0 && (
              <span className="text-xs font-mono text-muted">{formatDuration(task.actual_duration_seconds)}</span>
            )}
            {task.deadline && (
              <span className="text-xs text-muted">Due: {task.deadline.substring(0, 10)}</span>
            )}
          </div>
        </div>
        <div className="flex gap-1" style={{ flexShrink: 0 }}>
          {task.status === 'pending' || task.status === 'carried_forward' || task.status === 'paused' ? (
            <button className="btn btn-primary btn-sm" onClick={handleFocus}>
              {task.status === 'paused' ? '▶ Resume' : 'Focus Now'}
            </button>
          ) : task.status === 'completed' ? (
            <span className="text-xs text-muted">✓ Done</span>
          ) : null}
        </div>
      </div>
    </div>
  );
}
