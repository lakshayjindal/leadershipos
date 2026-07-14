import { useAppStore } from '../store';

export default function IdleWorkspace() {
  const { setCurrentState } = useAppStore();
  const hour = new Date().getHours();
  const greeting = hour < 12 ? 'Good Morning' : hour < 17 ? 'Good Afternoon' : 'Good Evening';

  return (
    <div className="workspace-idle">
      <div className="workspace-idle-content">
        <div className="workspace-idle-greeting">{greeting}</div>
        <div className="workspace-idle-title">Ready when you are</div>
        <div className="workspace-idle-desc">
          Plan your day to get started, or jump back into your tasks.
        </div>
        <div className="workspace-idle-actions">
          <button
            className="btn btn-primary btn-lg"
            onClick={() => setCurrentState('planning')}
          >
            📋 Start Planning
          </button>
        </div>
      </div>
    </div>
  );
}
