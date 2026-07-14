import { useState, useEffect } from 'react';
import type { TodayStatus } from '../types';
import {
  getToday, saveReflection, getReflection, getTasks,
  formatDuration, generateJournal, shutdownDay,
} from '../utils';
import { useAppStore } from '../store';
import { useToast } from '../components/Toast';

export default function ReviewWorkspace() {
  const { todayStatus, setCurrentState } = useAppStore();
  const { addToast } = useToast();

  const [dayId, setDayId] = useState(todayStatus?.day?.id || '');
  const [accomplishments, setAccomplishments] = useState('');
  const [challenges, setChallenges] = useState('');
  const [tomorrowTask, setTomorrowTask] = useState('');
  const [journalContent, setJournalContent] = useState<string | null>(null);
  const [saved, setSaved] = useState(false);
  const [shutdown, setShutdown] = useState(false);
  const [shuttingDown, setShuttingDown] = useState(false);
  const [loading, setLoading] = useState(true);
  const [summary, setSummary] = useState<{ completed: number; total: number; focusSeconds: number } | null>(null);

  useEffect(() => {
    loadReviewData();
  }, []);

  async function loadReviewData() {
    try {
      const day = await getToday();
      setDayId(day.id);
      const loadedTasks = await getTasks(day.id);

      const existing = await getReflection(day.id);
      if (existing) {
        setAccomplishments(existing.accomplishments || '');
        setChallenges(existing.challenges || '');
        setTomorrowTask(existing.tomorrow_first_task || '');
      }

      const completed = loadedTasks.filter((t: any) => t.status === 'completed').length;
      const total = loadedTasks.filter((t: any) => t.status !== 'archived' && t.status !== 'deleted').length;
      const focusSeconds = loadedTasks.reduce((sum: number, t: any) => sum + t.actual_duration_seconds, 0);
      setSummary({ completed, total, focusSeconds });
    } catch (e) {
      console.error('Failed to load review data:', e);
    } finally {
      setLoading(false);
    }
  }

  async function handleSave() {
    try {
      await saveReflection(dayId, accomplishments, challenges, tomorrowTask);
      setSaved(true);
      addToast('Reflection saved', 'success');
    } catch (e) {
      addToast('Failed to save reflection', 'error');
    }
  }

  async function handleGenerateJournal() {
    try {
      await saveReflection(dayId, accomplishments, challenges, tomorrowTask);
      const content = await generateJournal(dayId);
      setJournalContent(content);
      setSaved(true);
      addToast('Journal generated', 'success');
    } catch (e) {
      addToast('Failed to generate journal', 'error');
    }
  }

  async function handleShutdown() {
    setShuttingDown(true);
    try {
      await saveReflection(dayId, accomplishments, challenges, tomorrowTask);
      const journal = await shutdownDay(dayId, true);
      if (journal) setJournalContent(journal);
      setShutdown(true);
      setSaved(true);
      setCurrentState('shutdown');
      addToast('Day complete! Journal saved.', 'success');
    } catch (e) {
      addToast('Failed to shut down day', 'error');
    } finally {
      setShuttingDown(false);
    }
  }

  if (loading) {
    return <div className="empty-state"><div className="empty-state-icon">⏳</div></div>;
  }

  return (
    <div className="review-workspace">
      <div className="page-header">
        <h1 className="page-title">End of Day Review</h1>
        <p className="page-subtitle">Reflect on today's work and prepare for tomorrow</p>
      </div>

      {/* Summary cards */}
      {summary && (
        <div className="grid-3" style={{ marginBottom: 24 }}>
          <div className="card">
            <div className="card-header"><span className="card-title">Completed Tasks</span></div>
            <div className="card-value">{summary.completed}<span className="text-muted" style={{ fontSize: 14 }}>/{summary.total}</span></div>
          </div>
          <div className="card">
            <div className="card-header"><span className="card-title">Focus Time</span></div>
            <div className="card-value font-mono">{formatDuration(summary.focusSeconds)}</div>
          </div>
          <div className="card">
            <div className="card-header"><span className="card-title">Status</span></div>
            <div className="card-value small" style={{ color: journalContent ? 'var(--color-success)' : 'var(--color-warning)' }}>
              {journalContent ? '✓ Journaled' : 'Pending'}
            </div>
          </div>
        </div>
      )}

      {/* Reflection Form */}
      <div className="card" style={{ marginBottom: 24 }}>
        <div className="flex items-center justify-between" style={{ marginBottom: 12 }}>
          <span className="card-title">Reflection</span>
          {saved && <span className="badge badge-completed">✓ Saved</span>}
        </div>

        <div className="form-group">
          <label className="form-label">What did you accomplish today?</label>
          <textarea className="form-input" placeholder="Key tasks and achievements..."
            value={accomplishments} onChange={e => setAccomplishments(e.target.value)} rows={3} />
        </div>
        <div className="form-group">
          <label className="form-label">What slowed you down?</label>
          <textarea className="form-input" placeholder="Blockers, distractions, challenges..."
            value={challenges} onChange={e => setChallenges(e.target.value)} rows={3} />
        </div>
        <div className="form-group">
          <label className="form-label">First thing to do tomorrow</label>
          <input className="form-input" placeholder="What should you start with tomorrow?"
            value={tomorrowTask} onChange={e => setTomorrowTask(e.target.value)} />
        </div>

        <div className="flex gap-2 mt-3">
          <button className="btn btn-primary" onClick={handleSave}>💾 Save Reflection</button>
          <button className="btn btn-primary" onClick={handleGenerateJournal}>📔 Generate Journal</button>
        </div>
      </div>

      {/* Shutdown */}
      {!shutdown && (
        <div className="card" style={{ marginBottom: 24, borderColor: 'var(--color-warning)' }}>
          <div className="card-header"><span className="card-title">End of Day</span></div>
          <p className="text-sm text-secondary" style={{ marginBottom: 16, lineHeight: 1.6 }}>
            Once you've completed your reflection and generated the journal, shut down the day.
            This archives today's work and saves the summary.
          </p>
          <button className="btn btn-primary" onClick={handleShutdown} disabled={shuttingDown}>
            {shuttingDown ? 'Shutting down...' : '🚀 End Day & Shutdown'}
          </button>
        </div>
      )}

      {/* Complete */}
      {shutdown && (
        <div className="card" style={{ textAlign: 'center', padding: 32, borderColor: 'var(--color-success)' }}>
          <div style={{ fontSize: 48, marginBottom: 16 }}>🌟</div>
          <h2 style={{ fontSize: 20, fontWeight: 700, marginBottom: 8 }}>Day Complete</h2>
          <p className="text-sm text-secondary" style={{ marginBottom: 16 }}>
            Today's work has been archived. Your journal has been saved.
          </p>
        </div>
      )}

      {/* Journal Preview */}
      {journalContent && (
        <div className="section">
          <div className="section-header">
            <h3 className="section-title">Generated Journal</h3>
            <button className="btn btn-secondary btn-sm" onClick={() => navigator.clipboard.writeText(journalContent)}>
              📋 Copy
            </button>
          </div>
          <div className="card" style={{
            fontFamily: 'var(--font-mono)', fontSize: 13, lineHeight: 1.6,
            whiteSpace: 'pre-wrap', maxHeight: 400, overflowY: 'auto',
          }}>
            {journalContent}
          </div>
        </div>
      )}
    </div>
  );
}
