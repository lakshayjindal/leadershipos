import { useState } from 'react';
import type { AppConfiguration } from '../types';
import { saveConfig } from '../utils';
import { useAppStore } from '../store';

interface SettingsViewProps {
  onRefresh: () => void;
}

export default function SettingsView({ onRefresh }: SettingsViewProps) {
  const { config, setConfig, setTheme } = useAppStore();
  const [localConfig, setLocalConfig] = useState<AppConfiguration>({ ...config! });
  const [saved, setSaved] = useState(false);

  function handleChange(field: keyof AppConfiguration, value: any) {
    setLocalConfig(prev => ({ ...prev, [field]: value }));
    setSaved(false);
  }

  async function handleSave() {
    try {
      await saveConfig(localConfig);
      setConfig(localConfig);
      setTheme(localConfig.theme as 'dark' | 'light');
      setSaved(true);
      setTimeout(() => setSaved(false), 2000);
      onRefresh();
    } catch (e) {
      console.error('Failed to save config:', e);
    }
  }

  return (
    <div style={{ maxWidth: 720 }}>
      <div className="page-header">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="page-title">Settings</h1>
            <p className="page-subtitle">Customize Leadership OS to fit your working style</p>
          </div>
          <button className="btn btn-primary" onClick={handleSave}>
            {saved ? '✓ Saved!' : '💾 Save'}
          </button>
        </div>
      </div>

      {/* Work Schedule */}
      <div className="card" style={{ marginBottom: 16 }}>
        <div className="card-header"><span className="card-title">Work Schedule</span></div>
        <div className="grid-2" style={{ gap: 12 }}>
          <div className="form-group">
            <label className="form-label">Working Hours Start</label>
            <input className="form-input" type="time" value={localConfig.working_hours_start}
              onChange={e => handleChange('working_hours_start', e.target.value)} />
          </div>
          <div className="form-group">
            <label className="form-label">Working Hours End</label>
            <input className="form-input" type="time" value={localConfig.working_hours_end}
              onChange={e => handleChange('working_hours_end', e.target.value)} />
          </div>
          <div className="form-group">
            <label className="form-label">Lunch Time</label>
            <input className="form-input" type="time" value={localConfig.lunch_time || '13:00'}
              onChange={e => handleChange('lunch_time', e.target.value)} />
          </div>
          <div className="form-group">
            <label className="form-label">Dinner Time</label>
            <input className="form-input" type="time" value={localConfig.dinner_time || '19:30'}
              onChange={e => handleChange('dinner_time', e.target.value)} />
          </div>
        </div>
      </div>

      {/* Timer & Breaks */}
      <div className="card" style={{ marginBottom: 16 }}>
        <div className="card-header"><span className="card-title">Timer & Breaks</span></div>
        <div className="grid-2" style={{ gap: 12 }}>
          <div className="form-group">
            <label className="form-label">Short Break (minutes)</label>
            <input className="form-input" type="number" min={1} max={30}
              value={localConfig.short_break_duration}
              onChange={e => handleChange('short_break_duration', parseInt(e.target.value))} />
          </div>
          <div className="form-group">
            <label className="form-label">Long Break (minutes)</label>
            <input className="form-input" type="number" min={5} max={60}
              value={localConfig.long_break_duration}
              onChange={e => handleChange('long_break_duration', parseInt(e.target.value))} />
          </div>
          <div className="form-group">
            <label className="form-label">Sessions Before Long Break</label>
            <input className="form-input" type="number" min={1} max={10}
              value={localConfig.sessions_before_long_break}
              onChange={e => handleChange('sessions_before_long_break', parseInt(e.target.value))} />
          </div>
          <div className="form-group">
            <label className="form-label">Deadline Reminder (min before)</label>
            <input className="form-input" type="number" min={5} max={120}
              value={localConfig.deadline_reminder_minutes}
              onChange={e => handleChange('deadline_reminder_minutes', parseInt(e.target.value))} />
          </div>
        </div>
      </div>

      {/* Appearance */}
      <div className="card" style={{ marginBottom: 16 }}>
        <div className="card-header"><span className="card-title">Appearance</span></div>
        <div className="grid-2" style={{ gap: 12 }}>
          <div className="form-group">
            <label className="form-label">Theme</label>
            <select className="form-select" value={localConfig.theme}
              onChange={e => handleChange('theme', e.target.value)}>
              <option value="dark">Dark</option>
              <option value="light">Light</option>
            </select>
          </div>
          <div className="form-group">
            <label className="form-label">Overlay Opacity</label>
            <input className="form-input" type="range" min={0.2} max={1} step={0.05}
              value={localConfig.overlay_opacity}
              onChange={e => handleChange('overlay_opacity', parseFloat(e.target.value))} />
          </div>
          <div className="form-group">
            <label className="form-label">Overlay Position</label>
            <select className="form-select" value={localConfig.overlay_position}
              onChange={e => handleChange('overlay_position', e.target.value)}>
              <option value="top-left">Top Left</option>
              <option value="top-right">Top Right</option>
              <option value="bottom-left">Bottom Left</option>
              <option value="bottom-right">Bottom Right</option>
            </select>
          </div>
        </div>
      </div>

      {/* Journal */}
      <div className="card" style={{ marginBottom: 16 }}>
        <div className="card-header"><span className="card-title">Journal</span></div>
        <div className="grid-2" style={{ gap: 12 }}>
          <div className="form-group">
            <label className="form-label">Markdown Vault Path</label>
            <input className="form-input" placeholder="/path/to/obsidian/vault"
              value={localConfig.markdown_vault_path || ''}
              onChange={e => handleChange('markdown_vault_path', e.target.value || null)} />
          </div>
          <div className="form-group">
            <label className="form-label">Journal Directory</label>
            <input className="form-input" placeholder="Daily Notes"
              value={localConfig.journal_directory}
              onChange={e => handleChange('journal_directory', e.target.value)} />
          </div>
        </div>
      </div>

      {/* Notifications */}
      <div className="card" style={{ marginBottom: 16 }}>
        <div className="card-header"><span className="card-title">Notifications</span></div>
        <div className="flex-col gap-2" style={{ display: 'flex' }}>
          <label className="flex items-center gap-2" style={{ cursor: 'pointer' }}>
            <input type="checkbox" checked={localConfig.notification_enabled}
              onChange={e => handleChange('notification_enabled', e.target.checked)} />
            <span>Enable Notifications</span>
          </label>
          <label className="flex items-center gap-2" style={{ cursor: 'pointer' }}>
            <input type="checkbox" checked={localConfig.break_reminder_enabled}
              onChange={e => handleChange('break_reminder_enabled', e.target.checked)} />
            <span>Break Reminders</span>
          </label>
          <label className="flex items-center gap-2" style={{ cursor: 'pointer' }}>
            <input type="checkbox" checked={localConfig.launch_at_startup}
              onChange={e => handleChange('launch_at_startup', e.target.checked)} />
            <span>Launch at System Startup</span>
          </label>
        </div>
      </div>

      {/* About */}
      <div className="card" style={{ marginBottom: 16 }}>
        <div className="card-header"><span className="card-title">About</span></div>
        <div className="text-sm text-secondary">
          <p><strong>Leadership OS</strong> v1.0.0</p>
          <p className="mt-1">A local-first personal execution system.</p>
          <p className="mt-1 text-muted">All data stored locally. No cloud services required.</p>
        </div>
      </div>
    </div>
  );
}
