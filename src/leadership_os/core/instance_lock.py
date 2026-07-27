"""Single-instance lock for Leadership OS.

Prevents multiple instances of the application from running simultaneously.
Uses a file lock (leadership_os.lock) in the app data directory.

Design: On startup, acquire a lock file. If the lock exists and the process
is still alive, refuse to start and focus the existing window. If the lock
is stale (process died), remove it and proceed.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)

LOCK_FILENAME = "leadership_os.lock"


class InstanceLock:
    """File-based single-instance lock.

    Usage:
        lock = InstanceLock(app_data_dir)
        try:
            lock.acquire()
        except InstanceLockError:
            # Another instance is already running
            print("Application is already running")
            sys.exit(0)
        # ... run app ...
        lock.release()
    """

    def __init__(self, app_data_dir: Path) -> None:
        self._lock_path = app_data_dir / LOCK_FILENAME
        self._pid: int | None = None

    def acquire(self) -> bool:
        """Attempt to acquire the single-instance lock.

        Returns:
            True if lock was acquired, False if another instance holds it.

        Raises:
            InstanceLockError: If lock exists and process is alive.
        """
        if self._lock_path.exists():
            try:
                existing_pid = int(self._lock_path.read_text().strip())
                # Check if the existing process is still alive
                if self._is_process_alive(existing_pid):
                    raise InstanceLockError(
                        f"Another instance is already running (PID: {existing_pid}). "
                        "Close it before starting a new one."
                    )
                else:
                    # Stale lock — remove it
                    logger.warning(
                        "Removing stale lock file (PID %d no longer running)",
                        existing_pid,
                    )
                    self._lock_path.unlink()
            except (ValueError, OSError):
                # Corrupted lock file — remove it
                logger.warning("Removing corrupted lock file")
                self._lock_path.unlink(missing_ok=True)

        # Create new lock file
        self._pid = os.getpid()
        self._lock_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock_path.write_text(str(self._pid))
        logger.info("Instance lock acquired (PID: %d)", self._pid)
        return True

    def release(self) -> None:
        """Release the instance lock.

        Only removes the lock file if it contains our PID to prevent
        accidentally removing another instance's lock in race conditions.
        """
        try:
            if self._lock_path.exists():
                stored_pid_str = self._lock_path.read_text().strip()
                stored_pid = int(stored_pid_str)
                if stored_pid == self._pid:
                    self._lock_path.unlink()
                    logger.info("Instance lock released")
        except (ValueError, OSError) as e:
            logger.warning("Failed to release lock: %s", e)

    def is_locked(self) -> bool:
        """Check if the lock is currently held."""
        return self._lock_path.exists()

    @staticmethod
    def _is_process_alive(pid: int) -> bool:
        """Check if a process with the given PID is running."""
        try:
            # Signal 0 checks if the process exists (sends no actual signal)
            os.kill(pid, 0)
            return True
        except (OSError, PermissionError):
            return False


class InstanceLockError(Exception):
    """Raised when the instance lock cannot be acquired."""
    pass
