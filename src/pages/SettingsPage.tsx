import { useState, useEffect } from "react";
import * as api from "../services/tauri";
import type { Settings } from "../types";

export function SettingsPage() {
  const [settings, setSettings] = useState<Settings | null>(null);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  useEffect(() => { api.getSettings().then(setSettings).catch(() => {}); }, []);

  const handleSave = async () => {
    if (!settings) return;
    setSaving(true);
    setMessage(null);
    try {
      await api.updateSettings(settings);
      setMessage("Settings saved");
    } catch {
      setMessage("Failed to save settings");
    } finally {
      setSaving(false);
    }
  };

  if (!settings) {
    return (
      <div className="flex h-full items-center justify-center">
        <p className="text-sm text-[var(--color-text-tertiary)]">Loading…</p>
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col max-w-[600px] mx-auto w-full">
      <div className="flex-none px-6 pt-6 pb-5">
        <h1 className="text-[var(--text-h1)] font-semibold">Settings</h1>
      </div>

      <div className="flex-1 overflow-y-auto px-6 pb-4 space-y-5">
        {/* Obsidian vault */}
        <div className="card p-4 space-y-2">
          <label htmlFor="vaultPath">Obsidian vault path</label>
          <input id="vaultPath" type="text" value={settings.obsidian_vault_path}
            onChange={(e) => setSettings({ ...settings, obsidian_vault_path: e.target.value })}
            className="font-mono text-sm" placeholder="~/Documents/obsidian/days" />
          <p className="text-xs text-[var(--color-text-tertiary)]">Notes saved as YYYY-MM-DD.md</p>
        </div>

        {/* Reminder + Default duration */}
        <div className="card p-4 space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <label htmlFor="remind">Reminder interval</label>
              <select id="remind" value={settings.reminder_interval_minutes}
                onChange={(e) => setSettings({ ...settings, reminder_interval_minutes: Number(e.target.value) })}>
                {[1, 5, 10, 15, 30].map((v) => <option key={v} value={v}>{v} minute{v !== 1 ? "s" : ""}</option>)}
              </select>
            </div>
            <div className="space-y-2">
              <label htmlFor="defDur">Default task duration</label>
              <select id="defDur" value={settings.default_task_duration_minutes}
                onChange={(e) => setSettings({ ...settings, default_task_duration_minutes: Number(e.target.value) })}>
                {[15, 30, 60, 90, 120, 180].map((v) => <option key={v} value={v}>{v >= 60 ? `${Math.floor(v / 60)}h${v % 60 ? ` ${v % 60}m` : ""}` : `${v} min`}</option>)}
              </select>
            </div>
          </div>
        </div>

        {/* Working hours + Theme */}
        <div className="card p-4 space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <label htmlFor="ws">Start</label>
              <input id="ws" type="time" value={settings.working_hours_start}
                onChange={(e) => setSettings({ ...settings, working_hours_start: e.target.value })} />
            </div>
            <div className="space-y-2">
              <label htmlFor="we">End</label>
              <input id="we" type="time" value={settings.working_hours_end}
                onChange={(e) => setSettings({ ...settings, working_hours_end: e.target.value })} />
            </div>
          </div>
          <div className="space-y-2">
            <label htmlFor="theme">Theme</label>
            <select id="theme" value={settings.theme}
              onChange={(e) => setSettings({ ...settings, theme: e.target.value as "system" | "light" | "dark" })}>
              <option value="system">System</option>
              <option value="light">Light</option>
              <option value="dark">Dark</option>
            </select>
          </div>
        </div>

        {/* Desktop notifications */}
        <div className="card p-4">
          <div className="flex items-center justify-between">
            <div>
              <label className="block mb-0">Desktop notifications</label>
              <p className="text-xs text-[var(--color-text-tertiary)] mt-0.5">Get notified when task time is up</p>
            </div>
            <label className="relative inline-flex items-center cursor-pointer">
              <input type="checkbox" checked={settings.desktop_notifications}
                onChange={() => setSettings({ ...settings, desktop_notifications: !settings.desktop_notifications })}
                className="sr-only peer" />
              <div className="w-9 h-5 bg-[var(--color-border)] rounded-full peer peer-checked:bg-[var(--color-primary)] transition-colors duration-150 after:content-[''] after:absolute after:top-0.5 after:left-0.5 after:bg-white after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:after:translate-x-4" />
            </label>
          </div>
        </div>

        {/* Message */}
        {message && (
          <div className={`card p-3 text-sm ${message === "Settings saved" ? "border-[var(--color-success)]/20 bg-[var(--color-success-subtle)] text-[var(--color-success)]" : "border-[var(--color-danger)]/20 bg-[var(--color-danger-subtle)] text-[var(--color-danger)]"}`}>
            {message}
          </div>
        )}
      </div>

      <div className="flex-none px-6 py-4 border-t border-[var(--color-border)]">
        <button onClick={handleSave} disabled={saving} className="btn-primary w-full btn-press">
          {saving ? "Saving…" : "Save settings"}
        </button>
      </div>
    </div>
  );
}
