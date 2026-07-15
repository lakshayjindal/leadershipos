"""Path utilities for Leadership OS.

Responsibilities:
- Cross-platform path resolution
- Application data directory detection
- Obsidian vault path handling
- File/firectory creation helpers
"""

from __future__ import annotations

import os
import sys
from pathlib import Path


def get_app_data_dir() -> Path:
    """Get the application data directory based on platform.

    Linux:   ~/.local/share/leadership-os/
    macOS:   ~/Library/Application Support/leadership-os/
    Windows: %APPDATA%\\leadership-os\\
    """
    if sys.platform == "linux":
        base = Path.home() / ".local" / "share"
    elif sys.platform == "darwin":
        base = Path.home() / "Library" / "Application Support"
    elif sys.platform == "win32":
        base = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
    else:
        # Fallback for unknown platforms
        base = Path.home() / ".local" / "share"

    return base / "leadership-os"


def get_default_vault_path() -> Path:
    """Get the default Obsidian vault path."""
    return Path.home() / "Documents" / "Obsidian"


def get_default_journal_dir() -> str:
    """Get the default journal directory name within the vault."""
    return "Daily Notes"


def ensure_directory(path: Path) -> Path:
    """Create directory and parents if they don't exist. Returns the path."""
    path.mkdir(parents=True, exist_ok=True)
    return path


def expand_user_path(path_str: str) -> Path:
    """Expand ~ and resolve path to absolute."""
    return Path(path_str).expanduser().resolve()


def is_valid_directory(path: Path) -> bool:
    """Check if path exists and is a directory."""
    return path.exists() and path.is_dir()


def is_writable_directory(path: Path) -> bool:
    """Check if directory exists and is writable."""
    if not path.exists():
        # Check if parent is writable
        return is_writable_directory(path.parent) if path.parent.exists() else False
    if not path.is_dir():
        return False
    # Test write access
    try:
        test_file = path / ".write_test"
        test_file.touch()
        test_file.unlink()
        return True
    except (OSError, PermissionError):
        return False


def get_journal_path(vault_path: str, journal_dir: str, date_str: str) -> Path:
    """Get the full path for a journal file.

    Args:
        vault_path: Root path of Obsidian vault
        journal_dir: Subdirectory for journals
        date_str: Date string in YYYY-MM-DD format

    Returns:
        Full path like ~/Documents/Obsidian/Daily Notes/2026-07-14.md
    """
    base = expand_user_path(vault_path)
    return base / journal_dir / f"{date_str}.md"


def get_relative_journal_path(journal_dir: str, date_str: str) -> str:
    """Get the relative journal path for storage in database.

    Returns:
        Relative path like "Daily Notes/2026-07-14.md"
    """
    return f"{journal_dir}/{date_str}.md"


def safe_delete(path: Path) -> bool:
    """Safely delete a file if it exists. Returns True if deleted."""
    try:
        if path.exists() and path.is_file():
            path.unlink()
            return True
        return False
    except (OSError, PermissionError):
        return False


def get_log_path() -> Path:
    """Get the log file path within app data directory."""
    app_dir = get_app_data_dir() / "logs"
    ensure_directory(app_dir)
    return app_dir / "leadership_os.log"
