import { useState, useEffect, useCallback } from "react";

export type ToastType = "success" | "error" | "info";

interface ToastMessage {
  id: number;
  type: ToastType;
  message: string;
}

let toastId = 0;
let addToastFn: ((type: ToastType, message: string) => void) | null = null;

export function showToast(type: ToastType, message: string) {
  if (addToastFn) addToastFn(type, message);
}

export function ToastContainer() {
  const [toasts, setToasts] = useState<ToastMessage[]>([]);

  const addToast = useCallback((type: ToastType, message: string) => {
    const id = ++toastId;
    setToasts((prev) => [...prev, { id, type, message }]);
    setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id));
    }, 3500);
  }, []);

  useEffect(() => {
    addToastFn = addToast;
    return () => {
      addToastFn = null;
    };
  }, [addToast]);

  if (toasts.length === 0) return null;

  return (
    <div className="fixed top-4 right-4 z-[100] flex flex-col gap-2 pointer-events-none">
      {toasts.map((toast) => (
        <div
          key={toast.id}
          className={`pointer-events-auto animate-toast-in rounded-xl border px-4 py-3 shadow-lg text-sm max-w-xs ${
            toast.type === "success"
              ? "bg-[var(--color-success-subtle)] border-[var(--color-success)]/20 text-[var(--color-success)]"
              : toast.type === "error"
                ? "bg-[var(--color-danger-subtle)] border-[var(--color-danger)]/20 text-[var(--color-danger)]"
                : "bg-[var(--color-primary-subtle)] border-[var(--color-primary)]/20 text-[var(--color-primary)]"
          }`}
        >
          {toast.message}
        </div>
      ))}
    </div>
  );
}
