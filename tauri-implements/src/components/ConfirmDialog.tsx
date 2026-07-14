interface ConfirmDialogProps {
  title: string;
  message: string;
  confirmLabel?: string;
  cancelLabel?: string;
  variant?: 'danger' | 'warning' | 'default';
  onConfirm: () => void;
  onCancel: () => void;
}

export default function ConfirmDialog({
  title,
  message,
  confirmLabel = 'Confirm',
  cancelLabel = 'Cancel',
  variant = 'default',
  onConfirm,
  onCancel,
}: ConfirmDialogProps) {
  return (
    <div className="modal-overlay" onClick={onCancel}>
      <div
        className="modal-content"
        onClick={e => e.stopPropagation()}
        style={{ minWidth: 360, maxWidth: 420 }}
      >
        <div className="modal-title" style={{
          color: variant === 'danger' ? 'var(--color-error)' : variant === 'warning' ? 'var(--color-high)' : 'var(--color-text)',
        }}>
          {title}
        </div>
        <p style={{ color: 'var(--color-text-secondary)', fontSize: 13, lineHeight: 1.6, marginBottom: 20 }}>
          {message}
        </p>
        <div className="modal-footer">
          <button className="btn btn-ghost" onClick={onCancel}>
            {cancelLabel}
          </button>
          <button
            className={`btn ${variant === 'danger' ? 'btn-danger' : 'btn-primary'}`}
            onClick={onConfirm}
            autoFocus
          >
            {confirmLabel}
          </button>
        </div>
      </div>
    </div>
  );
}
