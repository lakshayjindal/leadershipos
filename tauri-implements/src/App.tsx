import { useState, useEffect, useRef } from 'react';
import './App.css';
import type { AppConfiguration } from './types';
import { getTodayStatus, getConfig } from './utils';
import { useAppStore } from './store';
import { ToastProvider } from './components/Toast';
import CommandPalette from './components/CommandPalette';
import SearchOverlay from './components/SearchOverlay';
import MorningGreeting from './components/MorningGreeting';
import RecoveryOverlay from './components/RecoveryOverlay';
import Sidebar from './components/Sidebar';
import TopBar from './components/TopBar';
import ExecutionPanel from './components/ExecutionPanel';
import StatusBar from './components/StatusBar';
import MainWorkspace from './components/MainWorkspace';

function App() {
  const { setTodayStatus, setConfig, setTheme, currentState, setCurrentState, setOverlay, todayStatus } = useAppStore();
  const [loaded, setLoaded] = useState(false);
  const commandPaletteRef = useRef(false);

  useEffect(() => {
    loadInitialData();
  }, []);

  // Listen for overlay state changes for keyboard handling
  const overlays = useAppStore(s => s.overlays);
  commandPaletteRef.current = overlays.commandPaletteOpen;

  useEffect(() => {
    function handleKeyDown(e: KeyboardEvent) {
      // Cmd+K or Ctrl+K to open command palette
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        setOverlay('commandPaletteOpen', !overlays.commandPaletteOpen);
      }
      // Cmd+Shift+F or Ctrl+Shift+F for search
      if ((e.metaKey || e.ctrlKey) && e.shiftKey && e.key === 'F') {
        e.preventDefault();
        setOverlay('searchOpen', !overlays.searchOpen);
      }
      // Cmd+1/2/3 for nav
      if ((e.metaKey || e.ctrlKey) && ['1','2','3'].includes(e.key)) {
        e.preventDefault();
        const views = ['today', 'history', 'settings'] as const;
        useAppStore.getState().setWorkspaceView(views[parseInt(e.key) - 1]);
      }
      // Escape to close command palette
      if (e.key === 'Escape' && commandPaletteRef.current) {
        setOverlay('commandPaletteOpen', false);
      }
    }
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [overlays.commandPaletteOpen, overlays.searchOpen]);

  async function loadInitialData() {
    try {
      const status = await getTodayStatus();
      setTodayStatus(status);
      const cfg = await getConfig();
      setConfig(cfg);
      setTheme(cfg.theme as 'dark' | 'light');

      // Check for recovery needed
      if (status.state === 'working' || status.state === 'break') {
        if (status.active_task) {
          // Need recovery - show recovery overlay
          setCurrentState(status.state as any);
          setOverlay('recoveryOverlay', true);
        } else {
          // State says working but no active task - go to idle
          setCurrentState('idle');
        }
      } else if (status.state === 'shutdown') {
        // Just shut down - start fresh
        setCurrentState('planning');
      } else if (status.state === 'idle' || status.state === 'startup') {
        if (status.pending_tasks > 0 || status.completed_tasks > 0) {
          setCurrentState('working');
          setOverlay('morningGreeting', true);
        } else {
          setCurrentState('planning');
          setOverlay('morningGreeting', true);
        }
      } else {
        setCurrentState(status.state as any);
      }
    } catch (e) {
      console.error('Failed to load initial data:', e);
    } finally {
      setLoaded(true);
    }
  }

  if (!loaded) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100vh', color: 'var(--color-text-muted)' }}>
        <div style={{ textAlign: 'center' }}>
          <div style={{ fontSize: 24, marginBottom: 8 }}>⏳</div>
          <div>Loading Leadership OS...</div>
        </div>
      </div>
    );
  }

  return (
    <ToastProvider>
      <div className="app-shell">
        <TopBar />
        <div className="app-body">
          <Sidebar />
          <MainWorkspace />
          <ExecutionPanel />
        </div>
        <StatusBar />
      </div>

      {/* Overlays */}
      <MorningGreeting />
      <RecoveryOverlay recoveredState={
        currentState === 'working' || currentState === 'break'
          ? { state: currentState, taskTitle: todayStatus?.active_task?.title }
          : undefined
      } />
      <CommandPalette />
      <SearchOverlay />
    </ToastProvider>
  );
}

export default App;
