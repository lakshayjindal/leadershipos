import { useAppStore } from '../store';

interface RecoveryOverlayProps {
  recoveredState?: {
    state: string;
    taskTitle?: string;
    elapsedSeconds?: number;
  };
}

export default function RecoveryOverlay({ recoveredState }: RecoveryOverlayProps) {
  const { overlays, setOverlay, setCurrentState } = useAppStore();
  const isOpen = overlays.recoveryOverlay;

  if (!isOpen) return null;

  const hour = new Date().getHours();
  const greeting = hour < 12 ? 'Good Morning' : hour < 17 ? 'Good Afternoon' : 'Good Evening';

  function handleResume() {
    if (recoveredState?.state === 'working' || recoveredState?.state === 'break') {
      setCurrentState(recoveredState.state as any);
    } else {
      setCurrentState('planning');
    }
    setOverlay('recoveryOverlay', false);
  }

  function handleDiscard() {
    setCurrentState('planning');
    setOverlay('recoveryOverlay', false);
  }

  return (
    <div className="modal-overlay" style={{ backdropFilter: 'blur(4px)' }}>
      <div style={{
        maxWidth: 420, width: '90vw',
        background: 'var(--color-bg-secondary)',
        border: '1px solid var(--color-warning)',
        borderRadius: 'var(--radius-lg)',
        boxShadow: 'var(--shadow-lg)',
        padding: 24,
        textAlign: 'center',
      }}>
        <div style={{ fontSize: 48, marginBottom: 12 }}>🔁</div>
        <h2 style={{ fontSize: 20, fontWeight: 700, marginBottom: 8 }}>Welcome Back, {greeting}</h2>

        <p style={{ fontSize: 14, color: 'var(--color-text-secondary)', lineHeight: 1.6, marginBottom: 16 }}>
          It looks like Leadership OS was not properly shut down last time.
          Your session state has been recovered.
        </p>

        {recoveredState && (
          <div style={{
            padding: '8px 12px', background: 'var(--color-bg-tertiary)',
            borderRadius: 'var(--radius-md)', marginBottom: 16, textAlign: 'left',
          }}>
            <div className="text-xs text-muted" style={{ marginBottom: 4, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
              Recovered State
            </div>
            <div className="text-sm">
              <strong>State:</strong> {recoveredState.state}
              {recoveredState.taskTitle && <>, <strong>Task:</strong> {recoveredState.taskTitle}</>}
              {recoveredState.elapsedSeconds && <>, <strong>Elapsed:</strong> {Math.floor(recoveredState.elapsedSeconds / 60)}m</>}
            </div>
          </div>
        )}

        <div style={{ display: 'flex', gap: 8, justifyContent: 'center' }}>
          <button className="btn btn-ghost" onClick={handleDiscard}>
            Start Fresh
          </button>
          <button className="btn btn-primary" onClick={handleResume}>
            {recoveredState?.state === 'working' || recoveredState?.state === 'break'
              ? '▶ Resume Session'
              : '📋 Start Planning'
            }
          </button>
        </div>
      </div>
    </div>
  );
}
