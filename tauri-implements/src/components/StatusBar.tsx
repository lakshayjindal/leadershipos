import { useAppStore } from '../store';
import { formatDuration } from '../utils';

export default function StatusBar() {
  const { todayStatus, currentState } = useAppStore();
  const summary = todayStatus?.daily_summary;
  const focusSeconds = summary?.total_focus_seconds ?? 0;
  const completed = todayStatus?.completed_tasks ?? 0;
  const total = (summary?.total_planned) ?? 0;

  return (
    <footer className="status-bar">
      <span>
        Focus: <strong className="font-mono">{formatDuration(focusSeconds)}</strong>
      </span>
      <span>
        Tasks: <strong>{completed}/{total}</strong>
      </span>
      <span className="status-bar-hint">
        <kbd>Cmd+K</kbd> Commands
      </span>
    </footer>
  );
}
