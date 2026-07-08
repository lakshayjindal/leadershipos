import type { ReactNode } from "react";
import { useSession } from "../contexts/SessionContext";

export function MainLayout({ children }: { children: ReactNode }) {
  const { view, setView } = useSession();

  const isHome =
    view === "welcome" ||
    view === "planning" ||
    view === "commitment" ||
    view === "dashboard";

  return (
    <div className="h-full flex">
      {/* Sidebar */}
      <nav className="w-12 flex-none flex flex-col items-center py-4 gap-3 border-r border-[var(--color-border)] bg-[var(--color-surface)]">
        <button
          onClick={() => setView("welcome")}
          className={`w-8 h-8 rounded-lg flex items-center justify-center transition-all duration-150 ${
            isHome
              ? "bg-[var(--color-primary)] text-white shadow-sm"
              : "text-[var(--color-text-tertiary)] hover:text-[var(--color-text)] hover:bg-[var(--color-surface-subtle)]"
          }`}
          title="Home"
        >
          <svg width="15" height="15" viewBox="0 0 15 15" fill="none">
            <path d="M1.5 7.5L7.5 1.5L13.5 7.5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
            <path d="M3.5 5.5V12.5H11.5V5.5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
          </svg>
        </button>

        {/* Separator */}
        <div className="w-4 h-px bg-[var(--color-border)]" />

        <button
          onClick={() => setView("settings")}
          className={`w-8 h-8 rounded-lg flex items-center justify-center transition-all duration-150 ${
            view === "settings"
              ? "bg-[var(--color-primary)] text-white shadow-sm"
              : "text-[var(--color-text-tertiary)] hover:text-[var(--color-text)] hover:bg-[var(--color-surface-subtle)]"
          }`}
          title="Settings"
        >
          <svg width="15" height="15" viewBox="0 0 15 15" fill="none">
            <path d="M7.5 9.5C8.60457 9.5 9.5 8.60457 9.5 7.5C9.5 6.39543 8.60457 5.5 7.5 5.5C6.39543 5.5 5.5 6.39543 5.5 7.5C5.5 8.60457 6.39543 9.5 7.5 9.5Z" stroke="currentColor" strokeWidth="1.5"/>
            <path d="M12.5 7.5C12.5 7.7 12.48 7.88 12.45 8.06L13.82 9.16C13.92 9.24 13.94 9.38 13.86 9.5L12.5 11.5C12.42 11.62 12.28 11.64 12.16 11.56L10.5 10.7C10.16 10.94 9.78 11.14 9.38 11.28L9 13C8.98 13.2 8.86 13.3 8.66 13.3H6.34C6.14 13.3 6.02 13.2 6 13L5.62 11.28C5.22 11.14 4.84 10.94 4.5 10.7L2.84 11.56C2.72 11.64 2.58 11.62 2.5 11.5L1.14 9.5C1.06 9.38 1.08 9.24 1.18 9.16L2.55 8.06C2.52 7.88 2.5 7.7 2.5 7.5C2.5 7.3 2.52 7.12 2.55 6.94L1.18 5.84C1.08 5.76 1.06 5.62 1.14 5.5L2.5 3.5C2.58 3.38 2.72 3.36 2.84 3.44L4.5 4.3C4.84 4.06 5.22 3.86 5.62 3.72L6 2C6.02 1.8 6.14 1.7 6.34 1.7H8.66C8.86 1.7 8.98 1.8 9 2L9.38 3.72C9.78 3.86 10.16 4.06 10.5 4.3L12.16 3.44C12.28 3.36 12.42 3.38 12.5 3.5L13.86 5.5C13.94 5.62 13.92 5.76 13.82 5.84L12.45 6.94C12.48 7.12 12.5 7.3 12.5 7.5Z" stroke="currentColor" strokeWidth="1.5"/>
          </svg>
        </button>
      </nav>

      {/* Main content */}
      <main className="flex-1 min-w-0 bg-[var(--color-bg)]">{children}</main>
    </div>
  );
}
