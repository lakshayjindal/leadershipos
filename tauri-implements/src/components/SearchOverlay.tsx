import { useState, useEffect, useRef, useCallback } from 'react';
import type { Task } from '../types';
import { search, formatDuration, getPriorityColor } from '../utils';
import { useAppStore } from '../store';

const RECENT_SEARCHES_KEY = 'leadership_os_recent_searches';
const MAX_RECENT = 10;

export default function SearchOverlay() {
  const { overlays, setOverlay } = useAppStore();
  const isOpen = overlays.searchOpen;

  const [query, setQuery] = useState('');
  const [results, setResults] = useState<Task[]>([]);
  const [searched, setSearched] = useState(false);
  const [searching, setSearching] = useState(false);
  const [selectedIndex, setSelectedIndex] = useState(-1);
  const [recentSearches, setRecentSearches] = useState<string[]>(() => {
    try { return JSON.parse(localStorage.getItem(RECENT_SEARCHES_KEY) || '[]'); }
    catch { return []; }
  });
  const inputRef = useRef<HTMLInputElement>(null);
  const debounceRef = useRef<ReturnType<typeof setTimeout>>();

  const performSearch = useCallback(async (q: string) => {
    if (!q.trim()) { setResults([]); setSearched(false); return; }
    setSearching(true);
    try {
      const tasks = await search(q);
      setResults(tasks);
      setSearched(true);
      setSelectedIndex(-1);
    } catch (err) {
      console.error('Search failed:', err);
    } finally {
      setSearching(false);
    }
  }, []);

  useEffect(() => {
    if (isOpen) {
      setQuery('');
      setResults([]);
      setSearched(false);
      setSelectedIndex(-1);
      setTimeout(() => inputRef.current?.focus(), 50);
    }
  }, [isOpen]);

  useEffect(() => {
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => performSearch(query), 200);
    return () => { if (debounceRef.current) clearTimeout(debounceRef.current); };
  }, [query, performSearch]);

  function addRecentSearch(q: string) {
    const trimmed = q.trim();
    if (!trimmed) return;
    const updated = [trimmed, ...recentSearches.filter(s => s !== trimmed)].slice(0, MAX_RECENT);
    setRecentSearches(updated);
    localStorage.setItem(RECENT_SEARCHES_KEY, JSON.stringify(updated));
  }

  function handleKeyDown(e: React.KeyboardEvent) {
    if (e.key === 'ArrowDown') {
      e.preventDefault();
      setSelectedIndex(i => Math.min(i + 1, results.length - 1));
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      setSelectedIndex(i => Math.max(i - 1, -1));
    } else if (e.key === 'Enter') {
      e.preventDefault();
      addRecentSearch(query);
      if (selectedIndex >= 0 && results[selectedIndex]) {
        setOverlay('searchOpen', false);
      }
    } else if (e.key === 'Escape') {
      e.preventDefault();
      if (query) {
        setQuery('');
        setResults([]);
        setSearched(false);
      } else {
        setOverlay('searchOpen', false);
      }
    }
  }

  // Group results by status
  const grouped = results.reduce((acc: Record<string, Task[]>, task) => {
    const group = task.status === 'completed' ? 'Completed'
      : task.status === 'active' ? 'Active'
      : task.status === 'paused' ? 'Paused'
      : task.status === 'archived' ? 'Archived'
      : 'Pending';
    if (!acc[group]) acc[group] = [];
    acc[group].push(task);
    return acc;
  }, {});

  const groupOrder = ['Active', 'Pending', 'Paused', 'Completed', 'Archived'];

  if (!isOpen) return null;

  return (
    <div className="modal-overlay" onClick={() => setOverlay('searchOpen', false)} onKeyDown={handleKeyDown}>
      <div
        className="search-overlay"
        onClick={e => e.stopPropagation()}
        style={{
          width: 600, maxWidth: '90vw', maxHeight: '70vh',
          background: 'var(--color-bg-secondary)',
          border: '1px solid var(--color-border)',
          borderRadius: 'var(--radius-lg)',
          overflow: 'hidden',
          boxShadow: 'var(--shadow-lg)',
          display: 'flex', flexDirection: 'column',
        }}
      >
        {/* Search Input */}
        <div style={{
          display: 'flex', alignItems: 'center', gap: 8,
          padding: '12px 16px', borderBottom: '1px solid var(--color-border)',
        }}>
          <span style={{ fontSize: 16, color: 'var(--color-text-muted)' }}>⌕</span>
          <input
            ref={inputRef}
            style={{
              flex: 1, background: 'transparent', border: 'none', outline: 'none',
              color: 'var(--color-text)', fontSize: 15, padding: 0,
            }}
            placeholder="Search tasks, notes, journals..."
            value={query}
            onChange={e => setQuery(e.target.value)}
          />
          {searching && <span style={{ fontSize: 12, color: 'var(--color-text-muted)' }}>...</span>}
        </div>

        {/* Results */}
        <div style={{ flex: 1, overflowY: 'auto', padding: 4 }}>
          {!query.trim() && recentSearches.length > 0 && (
            <div style={{ padding: '8px 12px' }}>
              <div className="text-xs text-muted" style={{ marginBottom: 4 }}>Recent Searches</div>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4 }}>
                {recentSearches.map(s => (
                  <button key={s} className="btn btn-ghost btn-sm" onClick={() => setQuery(s)}>{s}</button>
                ))}
              </div>
            </div>
          )}

          {searched && !searching && results.length === 0 && (
            <div style={{ padding: 24, textAlign: 'center', color: 'var(--color-text-muted)' }}>
              <div style={{ fontSize: 32, marginBottom: 8 }}>🔍</div>
              <div>No results for "{query}"</div>
            </div>
          )}

          {results.length > 0 && (
            <div>
              {groupOrder.filter(g => grouped[g]?.length > 0).map(group => (
                <div key={group} style={{ marginBottom: 8 }}>
                  <div className="text-xs text-muted" style={{
                    padding: '4px 12px', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.05em',
                  }}>
                    {group} ({grouped[group].length})
                  </div>
                  {grouped[group].map((task, i) => {
                    const globalIndex = results.indexOf(task);
                    return (
                      <div
                        key={task.id}
                        className={`command-item ${globalIndex === selectedIndex ? 'selected' : ''}`}
                        style={{
                          borderLeft: `3px solid ${getPriorityColor(task.priority)}`,
                          margin: '0 4px', borderRadius: 'var(--radius-md)',
                        }}
                        onMouseEnter={() => setSelectedIndex(globalIndex)}
                      >
                        <div className="command-item-info">
                          <span className="command-item-label">
                            <HighlightMatch text={task.title} query={query} />
                          </span>
                          <span className="command-item-category">
                            <span className={`badge badge-${task.priority}`} style={{ fontSize: 10 }}>{task.priority}</span>
                            {' '}
                            <span className={`task-status-badge status-${task.status}`} style={{ fontSize: 10 }}>
                              {task.status === 'active' ? '● Working' : task.status === 'paused' ? '⏸ Paused' :
                               task.status === 'completed' ? '✓ Done' : '○ Pending'}
                            </span>
                            {task.actual_duration_seconds > 0 && (
                              <span className="text-xs font-mono text-muted"> {formatDuration(task.actual_duration_seconds)}</span>
                            )}
                          </span>
                        </div>
                        <span className="text-xs text-muted">{task.created_at.substring(0, 10)}</span>
                      </div>
                    );
                  })}
                </div>
              ))}
            </div>
          )}

          {!searched && !searching && !query.trim() && (
            <div style={{ padding: 24, textAlign: 'center', color: 'var(--color-text-muted)' }}>
              <div style={{ fontSize: 32, marginBottom: 8 }}>🔍</div>
              <div>Start typing to search</div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div style={{
          padding: '6px 12px', borderTop: '1px solid var(--color-border)',
          fontSize: 11, color: 'var(--color-text-muted)', display: 'flex', gap: 12, justifyContent: 'center',
        }}>
          <span>↑↓ Navigate</span>
          <span>↵ Open</span>
          <span>Esc Close</span>
        </div>
      </div>
    </div>
  );
}

function HighlightMatch({ text, query }: { text: string; query: string }) {
  if (!query.trim() || !text) return <>{text}</>;
  const idx = text.toLowerCase().indexOf(query.toLowerCase());
  if (idx === -1) return <>{text}</>;
  return (
    <>
      {text.substring(0, idx)}
      <strong style={{ color: 'var(--color-primary)' }}>{text.substring(idx, idx + query.length)}</strong>
      {text.substring(idx + query.length)}
    </>
  );
}
