import { useAppStore, type WorkspaceView } from '../store';
import { formatDuration } from '../utils';

export default function Sidebar() {
  const { workspaceView, setWorkspaceView, setCurrentState, currentState, todayStatus } = useAppStore();
  const summary = todayStatus?.daily_summary;
  const focusSeconds = summary?.total_focus_seconds ?? 0;
  const completed = todayStatus?.completed_tasks ?? 0;
  const total = (summary?.total_planned) ?? 0;

  function handleClick(view: WorkspaceView) {
    if (view === 'today') {
      // If current state is idle/startup, transition to planning
      if (currentState === 'idle' || currentState === 'startup') {
        setCurrentState('planning');
      }
    }
    setWorkspaceView(view);
  }

  const stateLabel = currentState.charAt(0).toUpperCase() + currentState.slice(1);

  return (
    <aside className="app-sidebar">
      <div className="app-sidebar-header">
        <div className="app-sidebar-title">Leadership OS</div>
        <div className="app-sidebar-subtitle">Execution System</div>
      </div>
      <nav className="app-sidebar-nav">
        <div
          className={`nav-item ${workspaceView === 'today' ? 'active' : ''}`}
          onClick={() => handleClick('today')}
        >
          <span className="nav-icon">◉</span>
          <span>Today</span>
        </div>
        <div
          className={`nav-item ${workspaceView === 'history' ? 'active' : ''}`}
          onClick={() => handleClick('history')}
        >
          <span className="nav-icon">📅</span>
          <span>History</span>
        </div>
        <div
          className={`nav-item ${workspaceView === 'settings' ? 'active' : ''}`}
          onClick={() => handleClick('settings')}
        >
          <span className="nav-icon">⚙</span>
          <span>Settings</span>
        </div>
      </nav>
      <div className="sidebar-info">
        <div className="sidebar-info-state">
          <span className="sidebar-info-dot" data-state={currentState} />
          {stateLabel}
        </div>
        <div className="sidebar-info-stats">
          {completed}/{total} Complete
        </div>
        <div className="sidebar-info-stats">
          Focus: {formatDuration(focusSeconds)}
        </div>
      </div>
    </aside>
  );
}
