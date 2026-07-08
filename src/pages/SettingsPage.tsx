import { useState, useEffect } from "react";
import * as api from "../services/tauri";
import type { Settings } from "../types";

export function SettingsPage() {
  const [settings, setSettings] = useState<Settings | null>(null);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  useEffect(() => {
    api.getSettings().then(setSettings).catch(() => {});
  }, []);

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
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="flex-none px-8 pt-8 pb-4">
        <h1 className="text-[var(--text-h1)] font-semibold">Settings</h1>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto px-8 pb-4 space-y-8">
        {/* Obsidian vault */}
        <section className="space-y-2">
          <label htmlFor="vaultPath">Obsidian vault path</label>
          <input
            id="vaultPath"
            type="text"
            value={settings.obsidian_vault_path}
            onChange={(e) =>
              setSettings({
                ...settings,
                obsidian_vault_path: e.target.value,
              })
            }
            className="font-mono text-sm"
            placeholder="~/Documents/obsidian/days"
          />
          <p className="text-xs text-[var(--color-text-tertiary)]">
            Daily notes are saved as YYYY-MM-DD.md in this directory.
          </p>
        </section>

        {/* Two-column grid */}
        <div className="grid grid-cols-2 gap-6">
          <section className="space-y-2">
            <label htmlFor="reminderInterval">Reminder interval</label>
            <select
              id="reminderInterval"
              value={settings.reminder_interval_minutes}
              onChange={(e) =>
                setSettings({
                  ...settings,
                  reminder_interval_minutes: Number(e.target.value),
                })
              }
            >
              <option value={1}>1 minute</option>
              <option value={5}>5 minutes</option>
              <option value={10}>10 minutes</option>
              <option value={15}>15 minutes</option>
              <option value={30}>30 minutes</option>
            </select>
          </section>
          <section className="space-y-2">
            <label htmlFor="defaultDuration">Default task duration</label>
            <select
              id="defaultDuration"
              value={settings.default_task_duration_minutes}
              onChange={(e) =>
                setSettings({
                  ...settings,
                  default_task_duration_minutes: Number(e.target.value),
                })
              }
            >
              <option value={15}>15 min</option>
              <option value={30}>30 min</option>
              <option value={60}>1 hour</option>
              <option value={90}>1.5 hours</option>
              <option value={120}>2 hours</option>
              <option value={180}>3 hours</option>
            </select>
          </section>
        </div>

        {/* Two-column grid */}
        <div className="grid grid-cols-2 gap-6">
          <section className="space-y-2">
            <label htmlFor="workStart">Working hours start</label>
            <input
              id="workStart"
              type="time"
              value={settings.working_hours_start}
              onChange={(e) =>
                setSettings({
                  ...settings,
                  working_hours_start: e.target.value,
                })
              }
            />
          </section>
          <section className="space-y-2">
            <label htmlFor="workEnd">Working hours end</label>
            <input
              id="workEnd"
              type="time"
              value={settings.working_hours_end}
              onChange={(e) =>
                setSettings({
                  ...settings,
                  working_hours_end: e.target.value,
                })
              }
            />
          </section>
        </div>

        {/* Theme */}
        <section className="space-y-2">
          <label htmlFor="theme">Theme</label>
          <select
            id="theme"
            value={settings.theme}
            onChange={(e) =>
              setSettings({
                ...settings,
                theme: e.target.value as "system" | "light" | "dark",
              })
            }
          >
            <option value="system">System</option>
            <option value="light">Light</option>
            <option value="dark">Dark</option>
          </select>
        </section>

        {/* Message */}
        {message && (
          <div
            className={`rounded-xl p-4 text-sm border ${
              message === "Settings saved"
                ? "bg-[var(--color-success-subtle)] border-[var(--color-success)]/20 text-[var(--color-success)]"
                : "bg-[var(--color-danger-subtle)] border-[var(--color-danger)]/20 text-[var(--color-danger)]"
            }`}
          >
            {message}
          </div>
        )}
      </div>

      {/* Footer */}
      <div className="flex-none px-8 py-5 border-t border-[var(--color-border)]">
        <button
          onClick={handleSave}
          disabled={saving}
          className="btn-primary w-full"
        >
          {saving ? "Saving…" : "Save settings"}
        </button>
      </div>
    </div>
  );
}
