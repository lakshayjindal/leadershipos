import { useState } from 'react';
import type { Task, Priority } from '../types';
import { updateTask } from '../utils';
import { useToast } from './Toast';

interface TaskEditModalProps {
  task: Task;
  onClose: () => void;
  onSaved: () => Promise<void>;
}

export default function TaskEditModal({ task, onClose, onSaved }: TaskEditModalProps) {
  const { addToast } = useToast();
  const [title, setTitle] = useState(task.title);
  const [description, setDescription] = useState(task.description || '');
  const [priority, setPriority] = useState<Priority>(task.priority);
  const initialDeadline = task.deadline || '';
  const initialDate = initialDeadline ? initialDeadline.replace(' ', 'T').substring(0, 10) : '';
  const initialTime = initialDeadline ? initialDeadline.replace(' ', 'T').substring(11, 16) : '';
  const [deadlineDate, setDeadlineDate] = useState(initialDate);
  const [deadlineTime, setDeadlineTime] = useState(initialTime);
  const [estimatedDuration, setEstimatedDuration] = useState(
    task.estimated_duration_minutes?.toString() || ''
  );
  const [notes, setNotes] = useState(task.notes || '');
  const [saving, setSaving] = useState(false);

  async function handleSave() {
    if (!title.trim()) return;
    setSaving(true);
    try {
      await updateTask({
        id: task.id,
        title: title.trim(),
        description: description.trim() || null,
        priority: priority,
        deadline: deadlineDate && deadlineTime ? `${deadlineDate} ${deadlineTime}:00` : null,
        estimated_duration_minutes: estimatedDuration ? parseInt(estimatedDuration, 10) : null,
        notes: notes.trim() || null,
      });
      addToast('Task saved successfully', 'success');
      await onSaved();
      onClose();
    } catch (e) {
      const msg = e instanceof Error ? e.message : String(e);
      addToast(`Failed to save: ${msg}`, 'error', 6000);
      console.error('Failed to save task:', e);
    } finally {
      setSaving(false);
    }
  }

  function handleKeyDown(e: React.KeyboardEvent) {
    if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) {
      handleSave();
    }
    if (e.key === 'Escape') {
      onClose();
    }
  }

  return (
    <div className="modal-overlay" onClick={onClose} onKeyDown={handleKeyDown}>
      <div className="modal-content" onClick={e => e.stopPropagation()}>
        <div className="modal-title">Edit Task</div>

        <div className="form-group">
          <label className="form-label">Title</label>
          <input
            className="form-input"
            value={title}
            onChange={e => setTitle(e.target.value)}
            placeholder="What needs to be done?"
            autoFocus
          />
        </div>

        <div className="form-group">
          <label className="form-label">Description</label>
          <textarea
            className="form-input"
            value={description}
            onChange={e => setDescription(e.target.value)}
            placeholder="Optional details about this task..."
            rows={3}
          />
        </div>

        <div style={{ display: 'flex', gap: 12 }}>
          <div className="form-group" style={{ flex: 1 }}>
            <label className="form-label">Priority</label>
            <select
              className="form-select"
              value={priority}
              onChange={e => setPriority(e.target.value as Priority)}
            >
              <option value="critical">Critical</option>
              <option value="high">High</option>
              <option value="medium">Medium</option>
              <option value="low">Low</option>
            </select>
          </div>

          <div className="form-group" style={{ flex: 1 }}>
            <label className="form-label">Est. Duration (min)</label>
            <input
              className="form-input"
              type="number"
              min={1}
              value={estimatedDuration}
              onChange={e => setEstimatedDuration(e.target.value)}
              placeholder="e.g. 30"
            />
          </div>
        </div>

        <div className="form-group">
          <label className="form-label">Deadline</label>
          <div style={{ display: 'flex', gap: 8 }}>
            <input
              className="form-input"
              type="date"
              value={deadlineDate}
              onChange={e => setDeadlineDate(e.target.value)}
              style={{ flex: 1 }}
            />
            <input
              className="form-input"
              type="time"
              value={deadlineTime}
              onChange={e => setDeadlineTime(e.target.value)}
              style={{ flex: 1 }}
            />
          </div>
        </div>

        <div className="form-group">
          <label className="form-label">Notes</label>
          <textarea
            className="form-input"
            value={notes}
            onChange={e => setNotes(e.target.value)}
            placeholder="Any notes or additional context..."
            rows={3}
          />
        </div>

        <div className="modal-footer">
          <button className="btn btn-ghost" onClick={onClose}>
            Cancel
          </button>
          <button
            className="btn btn-primary"
            onClick={handleSave}
            disabled={!title.trim() || saving}
          >
            {saving ? 'Saving...' : 'Save Changes'}
          </button>
        </div>
      </div>
    </div>
  );
}
