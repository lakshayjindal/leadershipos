import { useState, useEffect } from 'react';
import type { Task, Priority } from '../types';
import {
  getTasks, getToday, createTask, updateTask, setTaskStatus,
  reorderTasks, getCarryForwardTasks, carryForwardTask,
} from '../utils';
import { useAppStore } from '../store';
import { useToast } from '../components/Toast';
import ConfirmDialog from '../components/ConfirmDialog';

export default function PlanningWorkspace() {
  const { todayStatus, setCurrentState } = useAppStore();
  const { addToast } = useToast();

  const [tasks, setTasks] = useState<Task[]>([]);
  const [dayId, setDayId] = useState(todayStatus?.day?.id || '');
  const [loading, setLoading] = useState(true);

  // Carry forward
  const [carryForwardTasks, setCarryForwardTasks] = useState<Task[]>([]);
  const [cfDecisions, setCfDecisions] = useState<Record<string, 'keep' | 'archive' | 'delete'>>({});
  const [showCF, setShowCF] = useState(false);

  // New task
  const [newTitle, setNewTitle] = useState('');
  const [newPriority, setNewPriority] = useState<Priority>('medium');
  const [showNewTaskExpanded, setShowNewTaskExpanded] = useState(false);
  const [newDescription, setNewDescription] = useState('');
  const [newDeadlineDate, setNewDeadlineDate] = useState('');
  const [newDeadlineTime, setNewDeadlineTime] = useState('');
  const [newEstDuration, setNewEstDuration] = useState('');

  // Edit
  const [editingTask, setEditingTask] = useState<string | null>(null);
  const [editTitle, setEditTitle] = useState('');

  // Confirm
  const [deletingTask, setDeletingTask] = useState<Task | null>(null);

  useEffect(() => {
    loadData();
  }, []);

  async function loadData() {
    try {
      const day = await getToday();
      setDayId(day.id);
      const loaded = await getTasks(day.id);
      setTasks(loaded.filter(t => t.status !== 'archived' && t.status !== 'deleted'));

      const cf = await getCarryForwardTasks();
      setCarryForwardTasks(cf);
      if (cf.length > 0) setShowCF(true);
    } catch (e) {
      console.error('Failed to load planner:', e);
    } finally {
      setLoading(false);
    }
  }

  // Track duplicate title warning
  const [titleWarning, setTitleWarning] = useState('');

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    if (!newTitle.trim() || !dayId) return;

    // Validate: check for duplicate titles
    const trimmed = newTitle.trim();
    const duplicate = tasks.find(t => t.title.toLowerCase() === trimmed.toLowerCase());
    if (duplicate) {
      setTitleWarning(`A task with this title already exists ("${duplicate.title}").`);
      return;
    }
    setTitleWarning('');

    try {
      const deadline = newDeadlineDate && newDeadlineTime ? `${newDeadlineDate} ${newDeadlineTime}:00` : null;
      const task = await createTask(dayId, {
        title: trimmed,
        priority: newPriority,
        description: newDescription.trim() || null,
        deadline,
        estimated_duration_minutes: newEstDuration ? parseInt(newEstDuration, 10) : null,
        notes: null,
      });
      setTasks(prev => [...prev, task]);
      setNewTitle('');
      setNewDescription('');
      setNewDeadlineDate('');
      setNewDeadlineTime('');
      setNewEstDuration('');
      addToast(`✓ "${task.title}" added to today's plan`, 'success');
    } catch (e) {
      const msg = String(e);
      if (msg.includes('duplicate') || msg.includes('already exists')) {
        addToast('A task with this title already exists. Use a different title.', 'warning');
      } else {
        addToast(`Could not create task. ${msg}`, 'error');
      }
    }
  }

  async function handleEditSave(taskId: string) {
    if (!editTitle.trim()) return;
    try {
      await updateTask({ id: taskId, title: editTitle.trim() });
      setTasks(prev => prev.map(t => t.id === taskId ? { ...t, title: editTitle.trim() } : t));
      setEditingTask(null);
    } catch (e) {
      addToast(`Failed to save: ${e}`, 'error');
    }
  }

  async function handleDelete(taskId: string) {
    try {
      await setTaskStatus(taskId, 'deleted');
      setTasks(prev => prev.filter(t => t.id !== taskId));
      addToast('Task deleted', 'info');
    } catch (e) {
      addToast(`Failed to delete: ${e}`, 'error');
    }
  }

  async function handleArchive(taskId: string) {
    try {
      await setTaskStatus(taskId, 'archived');
      setTasks(prev => prev.filter(t => t.id !== taskId));
    } catch (e) {
      addToast(`Failed to archive: ${e}`, 'error');
    }
  }

  async function handleMoveUp(index: number) {
    if (index === 0) return;
    const newTasks = [...tasks];
    [newTasks[index - 1], newTasks[index]] = [newTasks[index], newTasks[index - 1]];
    setTasks(newTasks);
    await reorderTasks(newTasks.map(t => t.id));
  }

  async function handleMoveDown(index: number) {
    if (index === tasks.length - 1) return;
    const newTasks = [...tasks];
    [newTasks[index], newTasks[index + 1]] = [newTasks[index + 1], newTasks[index]];
    setTasks(newTasks);
    await reorderTasks(newTasks.map(t => t.id));
  }

  async function handleApplyCF() {
    try {
      for (const task of carryForwardTasks) {
        const decision = cfDecisions[task.id] || 'keep';
        if (decision === 'keep') {
          await carryForwardTask(task.id, dayId);
        } else if (decision === 'archive') {
          await setTaskStatus(task.id, 'archived');
        } else if (decision === 'delete') {
          await setTaskStatus(task.id, 'deleted');
        }
      }
      addToast(`Processed ${carryForwardTasks.length} tasks`, 'success');
      setShowCF(false);
      const loaded = await getTasks(dayId);
      setTasks(loaded.filter(t => t.status !== 'archived' && t.status !== 'deleted'));
    } catch (e) {
      addToast(`Failed to process: ${e}`, 'error');
    }
  }

  function handleBeginWork() {
    if (tasks.length === 0) {
      addToast('Create at least one task first', 'warning');
      return;
    }
    setCurrentState('working');
  }

  const sortedTasks = [...tasks].sort((a, b) => {
    const order: Priority[] = ['critical', 'high', 'medium', 'low'];
    const pa = order.indexOf(a.priority as Priority);
    const pb = order.indexOf(b.priority as Priority);
    if (pa !== pb) return pa - pb;
    return a.display_order - b.display_order;
  });

  if (loading) {
    return <div className="empty-state"><div className="empty-state-icon">⏳</div><div>Loading planner...</div></div>;
  }

  return (
    <div className="planning-workspace">
      <div className="page-header">
        <h1 className="page-title">Daily Planner</h1>
        <p className="page-subtitle">Plan your day with intention and clarity</p>
      </div>

      {/* Carry Forward Section */}
      {showCF && carryForwardTasks.length > 0 && (
        <div className="card" style={{ marginBottom: 20, borderColor: 'var(--color-warning)' }}>
          <div className="flex items-center gap-2" style={{ marginBottom: 12 }}>
            <span style={{ fontSize: 20 }}>↻</span>
            <div>
              <div style={{ fontSize: 14, fontWeight: 600 }}>Unfinished Tasks</div>
              <div className="text-xs text-secondary">
                {carryForwardTasks.length} task{carryForwardTasks.length !== 1 ? 's' : ''} from previous days
              </div>
            </div>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
            {carryForwardTasks.map(task => (
              <div key={task.id} className="flex items-center justify-between" style={{
                padding: '8px 12px', borderRadius: 'var(--radius-md)', background: 'var(--color-bg-tertiary)',
              }}>
                <div className="flex items-center gap-2" style={{ flex: 1, minWidth: 0 }}>
                  <span className={`badge badge-${task.priority}`} style={{ fontSize: 10, flexShrink: 0 }}>
                    {task.priority}
                  </span>
                  <span style={{ fontSize: 13, fontWeight: 500, wordBreak: 'break-word' }}>{task.title}</span>
                  {task.carry_forward_count > 0 && (
                    <span className="text-xs" style={{ color: 'var(--color-warning)', flexShrink: 0 }}>
                      ↻ x{task.carry_forward_count + 1}
                    </span>
                  )}
                </div>
                <div className="flex gap-1" style={{ flexShrink: 0, marginLeft: 8 }}>
                  {(['keep', 'archive', 'delete'] as const).map(opt => (
                    <button
                      key={opt}
                      className={`btn btn-sm ${cfDecisions[task.id] === opt ? 'btn-primary' : 'btn-ghost'}`}
                      style={cfDecisions[task.id] !== opt ? {
                        color: opt === 'keep' ? 'var(--color-primary)' : opt === 'archive' ? 'var(--color-text-muted)' : 'var(--color-error)'
                      } : {}}
                      onClick={() => setCfDecisions(prev => ({ ...prev, [task.id]: opt }))}
                    >
                      {opt === 'keep' ? '✓ Keep' : opt === 'archive' ? '▤ Archive' : '✕ Delete'}
                    </button>
                  ))}
                </div>
              </div>
            ))}
          </div>
          <div className="flex justify-between mt-3">
            <button className="btn btn-ghost btn-sm" onClick={() => setShowCF(false)}>Skip</button>
            <button className="btn btn-primary btn-sm" onClick={handleApplyCF}>
              Apply ({carryForwardTasks.length})
            </button>
          </div>
        </div>
      )}

      {/* New Task Creation */}
      <div className="card" style={{ marginBottom: 20 }}>
        <div className="flex items-center justify-between" style={{ marginBottom: 12 }}>
          <span className="card-title" style={{ fontSize: 13 }}>✏️ New Task</span>
          <button
            className="btn btn-ghost btn-sm"
            onClick={() => setShowNewTaskExpanded(!showNewTaskExpanded)}
          >
            {showNewTaskExpanded ? '▲ Less' : '▼ More'}
          </button>
        </div>
        <form onSubmit={handleCreate}>
          <div className="flex gap-2 items-start">
            <input
              className="form-input"
              style={{ flex: 1 }}
              placeholder="What do you want to accomplish?"
              value={newTitle}
              onChange={e => setNewTitle(e.target.value)}
              autoFocus
            />
            <select
              className="form-select"
              style={{ width: 110 }}
              value={newPriority}
              onChange={e => setNewPriority(e.target.value as Priority)}
            >
              <option value="critical">Critical</option>
              <option value="high">High</option>
              <option value="medium">Medium</option>
              <option value="low">Low</option>
            </select>
            <button className="btn btn-primary" type="submit" disabled={!newTitle.trim()}>
              + Add
            </button>
          </div>

          {titleWarning && (
            <div style={{
              marginTop: 6, padding: '4px 10px', fontSize: 12,
              color: 'var(--color-warning)', background: 'rgba(210, 153, 34, 0.08)',
              borderRadius: 'var(--radius-md)',
            }}>
              ⚠ {titleWarning}
            </div>
          )}

          {showNewTaskExpanded && (
            <div style={{ marginTop: 8 }}>
              <div className="form-group">
                <label className="form-label">Description</label>
                <textarea
                  className="form-input"
                  placeholder="Optional details..."
                  value={newDescription}
                  onChange={e => setNewDescription(e.target.value)}
                  rows={2}
                />
              </div>
              <div className="flex gap-3">
                <div className="form-group" style={{ flex: 1 }}>
                  <label className="form-label">Est. Duration (min)</label>
                  <input
                    className="form-input"
                    type="number" min={1}
                    value={newEstDuration}
                    onChange={e => setNewEstDuration(e.target.value)}
                    placeholder="e.g. 30"
                  />
                </div>
                <div className="form-group" style={{ flex: 1 }}>
                  <label className="form-label">Deadline</label>
                  <div className="flex gap-1">
                    <input className="form-input" type="date" value={newDeadlineDate}
                      onChange={e => setNewDeadlineDate(e.target.value)} />
                    <input className="form-input" type="time" value={newDeadlineTime}
                      onChange={e => setNewDeadlineTime(e.target.value)} />
                  </div>
                </div>
              </div>
            </div>
          )}
        </form>
      </div>

      {/* Task List */}
      {sortedTasks.length > 0 && (
        <div className="planning-task-list">
          <div className="flex items-center justify-between" style={{ marginBottom: 8 }}>
            <span style={{ fontSize: 14, fontWeight: 600 }}>
              Today's Tasks ({sortedTasks.length})
            </span>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
            {sortedTasks.map((task, index) => (
              <div
                key={task.id}
                className="card"
                style={{
                  padding: '8px 12px',
                  borderLeft: `3px solid var(--color-${
                    task.priority === 'critical' ? 'error' :
                    task.priority === 'high' ? 'high' :
                    task.priority === 'medium' ? 'primary' : 'low'
                  })`,
                }}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2" style={{ flex: 1, minWidth: 0 }}>
                    <span className="text-xs text-muted" style={{ minWidth: 18, textAlign: 'right', fontVariantNumeric: 'tabular-nums' }}>
                      {index + 1}
                    </span>
                    {editingTask === task.id ? (
                      <input
                        className="form-input"
                        style={{ padding: '4px 8px', fontSize: 13, flex: 1 }}
                        value={editTitle}
                        onChange={e => setEditTitle(e.target.value)}
                        onBlur={() => handleEditSave(task.id)}
                        onKeyDown={e => {
                          if (e.key === 'Enter') handleEditSave(task.id);
                          if (e.key === 'Escape') setEditingTask(null);
                        }}
                        autoFocus
                      />
                    ) : (
                      <span
                        style={{ flex: 1, cursor: 'pointer', fontSize: 13, wordBreak: 'break-word' }}
                        onDoubleClick={() => { setEditingTask(task.id); setEditTitle(task.title); }}
                      >
                        {task.title}
                      </span>
                    )}
                    <span className={`badge badge-${task.priority}`} style={{ fontSize: 10, flexShrink: 0 }}>
                      {task.priority}
                    </span>
                    {task.estimated_duration_minutes && (
                      <span className="text-xs text-muted flex-shrink-0">{task.estimated_duration_minutes}m</span>
                    )}
                  </div>
                  <div className="flex gap-1" style={{ flexShrink: 0, marginLeft: 8 }}>
                    <button className="btn btn-ghost btn-icon" onClick={() => handleMoveUp(index)} disabled={index === 0}>↑</button>
                    <button className="btn btn-ghost btn-icon" onClick={() => handleMoveDown(index)} disabled={index === sortedTasks.length - 1}>↓</button>
                    <button className="btn btn-ghost btn-icon" onClick={() => handleArchive(task.id)} title="Archive">▤</button>
                    <button className="btn btn-ghost btn-icon" style={{ color: 'var(--color-error)' }} onClick={() => setDeletingTask(task)}>✕</button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Empty state */}
      {sortedTasks.length === 0 && !showCF && (
        <div className="card">
          <div className="empty-state" style={{ padding: 24 }}>
            <div className="empty-state-icon">📋</div>
            <div className="empty-state-title">No Tasks Yet</div>
            <div className="empty-state-desc">Create your first task above to begin planning your day.</div>
          </div>
        </div>
      )}

      {/* Begin Work */}
      {sortedTasks.length > 0 && (
        <div style={{ marginTop: 20, display: 'flex', justifyContent: 'flex-end' }}>
          <button className="btn btn-primary btn-lg" onClick={handleBeginWork}>
            ✓ Begin Work →
          </button>
        </div>
      )}

      {/* Delete Confirmation */}
      {deletingTask && (
        <ConfirmDialog
          title="Delete Task"
          message={`Delete "${deletingTask.title}"? This cannot be undone.`}
          confirmLabel="Delete"
          variant="danger"
          onConfirm={() => { handleDelete(deletingTask.id); setDeletingTask(null); }}
          onCancel={() => setDeletingTask(null)}
        />
      )}
    </div>
  );
}
