import { useState, useEffect } from 'react';
import type { Day, Task, DailySummary } from '../types';
import { getPreviousDays, getTasks, formatDuration, formatDate } from '../utils';
import { useAppStore } from '../store';

interface HistoryDay {
  day: Day;
  summary: DailySummary | null;
  tasks: Task[];
  expanded: boolean;
}

export default function HistoryView() {
  const [historyDays, setHistoryDays] = useState<HistoryDay[]>([]);
  const [loading, setLoading] = useState(true);
  const [expandedDay, setExpandedDay] = useState<string | null>(null);
  const [filter, setFilter] = useState<'all' | 'completed' | 'incomplete'>('all');

  useEffect(() => {
    loadHistory();
  }, []);

  async function loadHistory() {
    try {
      const rawDays = await getPreviousDays(30);
      const loaded: HistoryDay[] = [];

      for (const [day, summary] of rawDays) {
        try {
          const tasks = await getTasks(day.id);
          loaded.push({
            day,
            summary,
            tasks: tasks.filter(t => t.status !== 'deleted'),
            expanded: false,
          });
        } catch {
          loaded.push({ day, summary, tasks: [], expanded: false });
        }
      }

      setHistoryDays(loaded);
    } catch (e) {
      console.error('Failed to load history:', e);
    } finally {
      setLoading(false);
    }
  }

  function toggleExpand(dayId: string) {
    setExpandedDay(prev => prev === dayId ? null : dayId);
  }

  const filteredDays = historyDays.filter(hd => {
    if (filter === 'all') return true;
    const pct = hd.summary?.completion_percentage ?? 0;
    return filter === 'completed' ? pct >= 100 : pct < 100;
  });

  if (loading) {
    return (
      <div>
        <div className="page-header">
          <h1 className="page-title">History</h1>
          <p className="page-subtitle">Explore past work days</p>
        </div>
        <div className="empty-state"><div className="empty-state-icon">⏳</div></div>
      </div>
    );
  }

  if (filteredDays.length === 0) {
    return (
      <div>
        <div className="page-header">
          <h1 className="page-title">History</h1>
          <p className="page-subtitle">Explore past work days</p>
        </div>
        <div className="card">
          <div className="empty-state">
            <div className="empty-state-icon">📅</div>
            <div className="empty-state-title">No History Yet</div>
            <div className="empty-state-desc">Complete a work day to start building your history.</div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div>
      <div className="page-header">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="page-title">History</h1>
            <p className="page-subtitle">Chronological record of your work</p>
          </div>
          <div className="flex gap-1">
            {(['all', 'completed', 'incomplete'] as const).map(f => (
              <button
                key={f}
                className={`btn btn-sm ${filter === f ? 'btn-primary' : 'btn-ghost'}`}
                onClick={() => setFilter(f)}
              >
                {f === 'all' ? 'All' : f === 'completed' ? '✓ Complete' : '○ Incomplete'}
              </button>
            ))}
          </div>
        </div>
      </div>

      {filteredDays.map(hd => (
        <div key={hd.day.id} className="section">
          <div
            className="card"
            style={{ cursor: 'pointer', transition: 'all 0.2s ease' }}
            onClick={() => toggleExpand(hd.day.id)}
          >
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div style={{ fontSize: 20, opacity: 0.6 }}>
                  {(hd.summary?.completion_percentage ?? 0) >= 100 ? '✅' : '📋'}
                </div>
                <div>
                  <div style={{ fontSize: 14, fontWeight: 600 }}>{formatDate(hd.day.date)}</div>
                  <div className="flex items-center gap-2 mt-1">
                    <span className="text-xs text-muted">
                      {hd.day.start_time ? hd.day.start_time.substring(11, 16) : '--:--'}
                      {' → '}
                      {hd.day.end_time ? hd.day.end_time.substring(11, 16) : '--:--'}
                    </span>
                    <span className="text-xs text-muted">·</span>
                    <span className="text-xs" style={{ color: hd.day.status === 'completed' ? 'var(--color-success)' : 'var(--color-text-muted)' }}>
                      {hd.day.status}
                    </span>
                  </div>
                </div>
              </div>
              {hd.summary && (
                <div className="text-right">
                  <div className="text-sm font-mono" style={{ fontWeight: 600 }}>
                    {formatDuration(hd.summary.total_focus_seconds)}
                  </div>
                  <div className="progress-bar mt-1" style={{ width: 80 }}>
                    <div
                      className={`progress-bar-fill ${hd.summary.completion_percentage >= 80 ? 'success' : 'warning'}`}
                      style={{ width: `${Math.min(hd.summary.completion_percentage, 100)}%` }}
                    />
                  </div>
                  <div className="text-xs text-muted mt-1">
                    {hd.summary.completed}/{hd.summary.total_planned} tasks
                  </div>
                </div>
              )}
              <span style={{ color: 'var(--color-text-muted)', fontSize: 12, transition: 'transform 0.2s', transform: expandedDay === hd.day.id ? 'rotate(180deg)' : '' }}>
                ▼
              </span>
            </div>
          </div>

          {expandedDay === hd.day.id && (
            <div
              className="state-transition"
              style={{ marginTop: 8, paddingLeft: 16 }}
            >
              {hd.summary && (
                <div className="grid-3 mb-4" style={{ gap: 8 }}>
                  <div className="card" style={{ padding: '8px 12px' }}>
                    <div className="card-title" style={{ fontSize: 11 }}>Focus Time</div>
                    <div className="font-mono text-sm mt-1">{formatDuration(hd.summary.total_focus_seconds)}</div>
                  </div>
                  <div className="card" style={{ padding: '8px 12px' }}>
                    <div className="card-title" style={{ fontSize: 11 }}>Tasks</div>
                    <div className="text-sm mt-1">{hd.summary.completed} / {hd.summary.total_planned}</div>
                  </div>
                  <div className="card" style={{ padding: '8px 12px' }}>
                    <div className="card-title" style={{ fontSize: 11 }}>Sessions</div>
                    <div className="text-sm mt-1">{hd.summary.session_count}</div>
                  </div>
                </div>
              )}

              {hd.tasks.length > 0 && (
                <div style={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
                  <div className="text-xs text-muted" style={{ fontWeight: 600, marginBottom: 4, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                    Tasks
                  </div>
                  {hd.tasks.map(task => (
                    <div
                      key={task.id}
                      className="card"
                      style={{
                        padding: '6px 12px',
                        borderLeft: `3px solid ${task.status === 'completed' ? 'var(--color-success)' : 'var(--color-text-muted)'}`,
                      }}
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2" style={{ flex: 1, minWidth: 0 }}>
                          <span style={{ fontSize: 12 }}>
                            {task.status === 'completed' ? '✓' : task.status === 'active' ? '◉' : '○'}
                          </span>
                          <span className="text-sm" style={{
                            textDecoration: task.status === 'completed' ? 'line-through' : 'none',
                            color: task.status === 'completed' ? 'var(--color-text-muted)' : 'var(--color-text)',
                            wordBreak: 'break-word',
                          }}>
                            {task.title}
                          </span>
                          <span className={`badge badge-${task.priority}`} style={{ fontSize: 9 }}>{task.priority}</span>
                        </div>
                        <span className="text-xs font-mono text-muted" style={{ flexShrink: 0 }}>
                          {task.actual_duration_seconds > 0 ? formatDuration(task.actual_duration_seconds) : '—'}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              )}

              {hd.tasks.length === 0 && (
                <div className="text-xs text-muted" style={{ padding: '8px 12px' }}>
                  No tasks recorded for this day.
                </div>
              )}
            </div>
          )}
        </div>
      ))}
    </div>
  );
}
