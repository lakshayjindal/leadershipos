import { useState, useEffect } from 'react';
import { useAppStore } from '../store';
import { useToast } from './Toast';

interface Command {
  id: string;
  label: string;
  shortcut?: string;
  action: () => void;
  category: string;
}

export default function CommandPalette() {
  const { overlays, setOverlay, currentState, setCurrentState, setWorkspaceView } = useAppStore();
  const isOpen = overlays.commandPaletteOpen;
  const { addToast } = useToast();

  const [query, setQuery] = useState('');
  const [selectedIndex, setSelectedIndex] = useState(0);

  // Build context-aware commands based on current state
  function getCommands(): Command[] {
    const navCommands: Command[] = [
      { id: 'nav-today', label: 'Today', shortcut: 'G 1', action: () => { setWorkspaceView('today'); }, category: 'Navigation' },
      { id: 'nav-history', label: 'History', shortcut: 'G 2', action: () => { setWorkspaceView('history'); }, category: 'Navigation' },
      { id: 'nav-settings', label: 'Settings', shortcut: 'G 3', action: () => { setWorkspaceView('settings'); }, category: 'Navigation' },
    ];

    const actionCommands: Command[] = [];

    // State-specific commands
    if (currentState === 'planning' || currentState === 'idle' || currentState === 'startup') {
      actionCommands.push(
        { id: 'create-task', label: 'Create New Task', shortcut: 'N', action: () => addToast('Create a task in the planner', 'info'), category: 'Actions' },
        { id: 'begin-work', label: 'Begin Work', shortcut: 'B', action: () => setCurrentState('working'), category: 'Actions' },
      );
    }

    if (currentState === 'working') {
      actionCommands.push(
        { id: 'pause-timer', label: 'Pause Timer', shortcut: 'P', action: () => addToast('Use the Execution Panel to pause', 'info'), category: 'Actions' },
        { id: 'complete-task', label: 'Complete Task', shortcut: 'C', action: () => addToast('Use the Execution Panel to complete', 'info'), category: 'Actions' },
        { id: 'start-break', label: 'Start Break', shortcut: 'B', action: () => addToast('Use the Execution Panel for breaks', 'info'), category: 'Actions' },
      );
    }

    if (currentState === 'break') {
      actionCommands.push(
        { id: 'resume-work', label: 'Resume Work', shortcut: 'R', action: () => addToast('Use the Execution Panel to resume', 'info'), category: 'Actions' },
      );
    }

    actionCommands.push(
      { id: 'end-day', label: 'End Day & Review', shortcut: 'E', action: () => { setCurrentState('review'); setWorkspaceView('today'); }, category: 'Actions' },
      { id: 'search', label: 'Search Tasks', shortcut: '/', action: () => { setOverlay('searchOpen', true); }, category: 'Actions' },
      { id: 'toggle-overlay', label: 'Toggle Overlay', shortcut: 'O', action: () => addToast('Overlay toggle from timer', 'info'), category: 'Actions' },
    );

    return [...navCommands, ...actionCommands];
  }

  const commands = getCommands();

  useEffect(() => {
    if (isOpen) {
      setQuery('');
      setSelectedIndex(0);
    }
  }, [isOpen]);

  useEffect(() => {
    setSelectedIndex(0);
  }, [query]);

  const filtered = commands.filter(cmd =>
    cmd.label.toLowerCase().includes(query.toLowerCase()) ||
    cmd.category.toLowerCase().includes(query.toLowerCase())
  );

  function handleKeyDown(e: React.KeyboardEvent) {
    if (e.key === 'ArrowDown') {
      e.preventDefault();
      setSelectedIndex(i => Math.min(i + 1, filtered.length - 1));
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      setSelectedIndex(i => Math.max(i - 1, 0));
    } else if (e.key === 'Enter' && filtered[selectedIndex]) {
      e.preventDefault();
      filtered[selectedIndex].action();
      setOverlay('commandPaletteOpen', false);
    } else if (e.key === 'Escape') {
      setOverlay('commandPaletteOpen', false);
    }
  }

  if (!isOpen) return null;

  return (
    <div className="modal-overlay" onClick={() => setOverlay('commandPaletteOpen', false)} style={{ alignItems: 'flex-start', paddingTop: '10vh' }}>
      <div
        className="command-palette"
        onClick={e => e.stopPropagation()}
        onKeyDown={handleKeyDown}
      >
        <div className="command-palette-input-wrapper">
          <span className="command-palette-icon">⌕</span>
          <input
            className="command-palette-input"
            placeholder="Type a command..."
            value={query}
            onChange={e => setQuery(e.target.value)}
            autoFocus
          />
        </div>
        <div className="command-palette-results">
          {filtered.length === 0 ? (
            <div className="command-palette-empty">No commands found</div>
          ) : (
            filtered.map((cmd, i) => (
              <div
                key={cmd.id}
                className={`command-item ${i === selectedIndex ? 'selected' : ''}`}
                onClick={() => { cmd.action(); setOverlay('commandPaletteOpen', false); }}
                onMouseEnter={() => setSelectedIndex(i)}
              >
                <div className="command-item-info">
                  <span className="command-item-label">{cmd.label}</span>
                  <span className="command-item-category">{cmd.category}</span>
                </div>
                {cmd.shortcut && (
                  <span className="command-item-shortcut">{cmd.shortcut}</span>
                )}
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}
