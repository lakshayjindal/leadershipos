import { useSession } from "../contexts/SessionContext";

export function Welcome() {
  const { handleStartSession } = useSession();

  return (
    <div className="flex h-full items-center justify-center animate-fade-in">
      <div className="max-w-sm mx-auto px-8 text-center">
        <div className="w-12 h-12 rounded-xl bg-[var(--color-primary)]/8 flex items-center justify-center mx-auto mb-8">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="var(--color-primary)" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
            <path d="M12 2L2 7l10 5 10-5-10-5z"/>
            <path d="M2 17l10 5 10-5"/>
            <path d="M2 12l10 5 10-5"/>
          </svg>
        </div>

        <h1 className="text-[var(--text-hero)] font-semibold tracking-tight mb-3">
          Leadership OS
        </h1>
        <p className="text-sm text-[var(--color-text-secondary)] leading-relaxed mb-8">
          Build daily leadership habits through intentional planning, focused execution, and honest reflection.
        </p>
        <button onClick={handleStartSession} className="btn-primary w-full btn-press">
          Start today's session
        </button>
      </div>
    </div>
  );
}
