import { useEffect, useState } from 'react';
import { useAppStore } from '../store';

export default function MorningGreeting() {
  const { overlays, setOverlay, todayStatus } = useAppStore();
  const isOpen = overlays.morningGreeting;
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    if (!isOpen) return;
    setVisible(true);
    const timer = setTimeout(() => {
      setVisible(false);
      setTimeout(() => setOverlay('morningGreeting', false), 300);
    }, 3000);
    return () => clearTimeout(timer);
  }, [isOpen]);

  if (!isOpen) return null;

  const hour = new Date().getHours();
  const greeting = hour < 12 ? 'Good Morning' : hour < 17 ? 'Good Afternoon' : 'Good Evening';
  const pendingTasks = todayStatus?.pending_tasks ?? 0;
  const completedTasks = todayStatus?.completed_tasks ?? 0;

  return (
    <div
      className="modal-overlay"
      style={{
        background: 'rgba(0,0,0,0.4)',
        backdropFilter: 'blur(8px)',
        transition: 'opacity 300ms ease, backdrop-filter 300ms ease',
        opacity: visible ? 1 : 0,
      }}
      onClick={() => { setVisible(false); setTimeout(() => setOverlay('morningGreeting', false), 300); }}
    >
      <div
        style={{
          textAlign: 'center',
          padding: '48px 64px',
          background: 'var(--color-bg-secondary)',
          border: '1px solid var(--color-border)',
          borderRadius: 'var(--radius-lg)',
          boxShadow: 'var(--shadow-lg)',
          animation: visible ? 'fadeInUp 0.4s ease' : 'fadeOutDown 0.3s ease',
        }}
      >
        <div style={{ fontSize: 64, marginBottom: 16 }}>🌅</div>
        <h1 style={{ fontSize: 32, fontWeight: 700, marginBottom: 8 }}>{greeting}</h1>
        <p style={{ fontSize: 16, color: 'var(--color-text-secondary)', marginBottom: 16 }}>
          {todayStatus?.day ? (
            <>
              {pendingTasks > 0
                ? `You have ${pendingTasks} task${pendingTasks !== 1 ? 's' : ''} waiting.`
                : completedTasks > 0
                  ? `${completedTasks} task${completedTasks !== 1 ? 's' : ''} completed yesterday.`
                  : 'Ready to plan your day.'}
            </>
          ) : (
            'Ready to plan your day.'
          )}
        </p>
        <div style={{ fontSize: 12, color: 'var(--color-text-muted)' }}>Let's begin.</div>
      </div>
    </div>
  );
}
