export function Loading() {
  return (
    <div className="flex h-full items-center justify-center">
      <div className="text-center space-y-3">
        <div className="w-6 h-6 rounded-full border-2 border-[var(--color-border)] border-t-[var(--color-primary)] animate-spin mx-auto" />
        <p className="text-sm text-[var(--color-text-tertiary)]">Loading</p>
      </div>
    </div>
  );
}
