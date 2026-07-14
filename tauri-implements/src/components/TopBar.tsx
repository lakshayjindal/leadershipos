import { useAppStore } from '../store';

export default function TopBar() {
  const { currentState, todayStatus, setOverlay, setWorkspaceView } = useAppStore();
  const activeTask = todayStatus?.active_task;
  const stateLabel = currentState.charAt(0).toUpperCase() + currentState.slice(1);

  const stateColors: Record<string, string> = {
    startup: 'var(--color-text-muted)',
    planning: 'var(--color-primary)',
    working: 'var(--color-success)',
    break: 'var(--color-warning)',
    idle: 'var(--color-text-muted)',
    review: 'var(--color-high)',
    shutdown: 'var(--color-error)',
  };

  return (
    <header className="app-topbar">
      <div className="topbar-state">
        <span
          className="topbar-state-dot"
          style={{ background: stateColors[currentState] || 'var(--color-text-muted)' }}
        />
        <span className="topbar-state-label">{stateLabel}</span>
      </div>

      <div className="topbar-current-task">
        {activeTask ? (
          <span className="topbar-task-name">
            ◉ {activeTask.title}
            <span className={`badge badge-${activeTask.priority}`} style={{ fontSize: 10, marginLeft: 8 }}>
              {activeTask.priority}
            </span>
          </span>
        ) : (
          <span className="topbar-task-name" style={{ color: 'var(--color-text-muted)' }}>
            No active task
          </span>
        )}
      </div>

      <div className="topbar-spacer" />

      <button className="topbar-btn" onClick={() => setOverlay('searchOpen', true)} title="Search (Cmd+Shift+F)">
        🔍 Search
      </button>
      <button className="topbar-btn" onClick={() => setOverlay('commandPaletteOpen', true)} title="Commands (Cmd+K)">
        ⌨ Commands
      </button>
      <button className="topbar-btn" onClick={() => setWorkspaceView('settings')} title="Settings">
        ⚙ Settings
      </button>
    </header>
  );
}
