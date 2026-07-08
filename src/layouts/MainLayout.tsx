import { useState, useEffect, type ReactNode } from "react";
import { useSession } from "../contexts/SessionContext";
import { MiniTimerBar } from "../components/MiniTimerBar";
import { QuickAddModal } from "../components/QuickAddPopover";
import { ToastContainer } from "../components/Toast";

export function MainLayout({ children }: { children: ReactNode }) {
  const {
    view,
    setView,
    session: currentSession,
    handleCompleteTask,
    handleSkipTask,
    extendTime,
    stillWorking,
    handlePauseTask,
    tasks,
    activeTaskId,
    showTimeUp,
    timeUpTask,
  } = useSession();

  // ─── Keyboard shortcuts ─────────────────────────────────────────────
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (
        e.target instanceof HTMLInputElement ||
        e.target instanceof HTMLTextAreaElement ||
        e.target instanceof HTMLSelectElement
      ) {
        return;
      }

      switch (e.key) {
        case "n":
        case "N":
          if (currentSession) setShowQuickAdd(true);
          break;
        case " ":
          e.preventDefault();
          if (activeTaskId) handlePauseTask(activeTaskId);
          break;
        case "Enter":
          if (activeTaskId) {
            const t = tasks.find((t) => t.id === activeTaskId);
            if (t) handleCompleteTask(t);
          }
          break;
        case "Escape":
          if (showTimeUp) stillWorking();
          if (showQuickAdd) setShowQuickAdd(false);
          break;
      }
    };
    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, [activeTaskId, tasks, handleCompleteTask, handlePauseTask, showTimeUp, stillWorking, currentSession]);

  const [showQuickAdd, setShowQuickAdd] = useState(false);

  const isHome =
    view === "welcome" ||
    view === "planning" ||
    view === "commitment" ||
    view === "dashboard";

  const navItems = [
    {
      id: "home",
      icon: (
        <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
          <path d="M2 8L8 2l6 6" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
          <path d="M4 6v6h8V6" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
        </svg>
      ),
      label: "Home",
      active: isHome,
      action: () => setView("welcome"),
    },
    {
      id: "planning",
      icon: (
        <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
          <rect x="2.5" y="2.5" width="11" height="11" rx="1.5" stroke="currentColor" strokeWidth="1.4"/>
          <path d="M5 6h6" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round"/>
          <path d="M5 8.5h4" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round"/>
          <path d="M5 11h5" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round"/>
        </svg>
      ),
      label: "Plan",
      active: view === "planning",
      action: () => setView("planning"),
      hidden: !currentSession,
    },
    {
      id: "add-task",
      icon: (
        <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
          <path d="M8 3v10M3 8h10" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
        </svg>
      ),
      label: "Add task",
      active: false,
      action: () => setShowQuickAdd(true),
      hidden: !currentSession,
    },
    { separator: true },
    {
      id: "settings",
      icon: (
        <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
          <circle cx="8" cy="8" r="2" stroke="currentColor" strokeWidth="1.4"/>
          <path d="M8 1.5v1M8 13.5v1M14.5 8h-1M2.5 8h-1M12.5 3.5l-.5.5M4 12l-.5.5M12.5 12.5l-.5-.5M4 4l-.5-.5" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round"/>
        </svg>
      ),
      label: "Settings",
      active: view === "settings",
      action: () => setView("settings"),
    },
  ];

  return (
    <div className="h-full flex bg-[var(--color-bg)]">
      {/* Sidebar */}
      <nav className="w-[48px] flex-none flex flex-col items-center py-3 gap-1 border-r border-[var(--color-border)] bg-[var(--color-surface)] z-30">
        {navItems.map((item, i) => {
          if ("separator" in item) {
            return (
              <div key={`sep-${i}`} className="w-full px-3 py-1.5">
                <div className="h-px bg-[var(--color-border)]" />
              </div>
            );
          }
          if (item.hidden) return null;

          return (
            <button
              key={item.id}
              onClick={item.action}
              className={`w-9 h-9 flex items-center justify-center rounded-lg transition-all duration-120 btn-press ${
                item.active
                  ? "sidebar-item-active"
                  : "text-[var(--color-text-tertiary)] hover:text-[var(--color-text)] hover:bg-[var(--color-surface-subtle)]"
              }`}
              title={item.label}
            >
              {item.icon}
            </button>
          );
        })}
      </nav>

      {/* Main content */}
      <div className="flex-1 min-w-0 flex flex-col">
        <MiniTimerBar />
        <main className="flex-1 min-h-0 overflow-hidden page-enter">
          {children}
        </main>
      </div>

      {/* Quick add modal */}
      <QuickAddModal
        open={showQuickAdd}
        onClose={() => setShowQuickAdd(false)}
      />

      {/* Toast container */}
      <ToastContainer />

      {/* Time-up Notification Modal */}
      {showTimeUp && timeUpTask && (
        <div className="modal-backdrop" style={{ zIndex: 60 }}>
          <div className="modal-panel p-6">
            <div className="flex items-center gap-3 mb-1">
              <div className="w-9 h-9 rounded-lg bg-[var(--color-warning-subtle)] flex items-center justify-center">
                <svg width="18" height="18" viewBox="0 0 18 18" fill="none" stroke="var(--color-warning)" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M9 1.5L1.5 16.5h15L9 1.5z" />
                  <path d="M9 7v4" />
                  <path d="M9 12.5v.5" />
                </svg>
              </div>
              <div>
                <p className="text-sm font-semibold">Time's up</p>
                <p className="text-xs text-[var(--color-text-tertiary)] mt-0.5">
                  {timeUpTask.title}
                </p>
              </div>
            </div>
            <div className="mt-5 space-y-2">
              <button
                onClick={() => { handleCompleteTask(timeUpTask); }}
                className="btn-primary w-full text-sm"
              >
                ✓ Finish
              </button>
              <div className="grid grid-cols-2 gap-2">
                <button onClick={() => extendTime(15)} className="btn-secondary text-sm">+15 min</button>
                <button onClick={() => extendTime(30)} className="btn-secondary text-sm">+30 min</button>
              </div>
              <button onClick={stillWorking} className="btn-ghost w-full text-sm">
                Still working
              </button>
              <button
                onClick={() => { handleSkipTask(timeUpTask); }}
                className="btn-ghost w-full text-sm text-[var(--color-danger)] hover:bg-[var(--color-danger-subtle)]"
              >
                Switch task
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
