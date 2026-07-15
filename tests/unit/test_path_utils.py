"""Tests for Leadership OS path utilities."""

import sys
from pathlib import Path

from leadership_os.utils.path_utils import (
    get_app_data_dir,
    get_default_vault_path,
    get_default_journal_dir,
    ensure_directory,
    expand_user_path,
    is_valid_directory,
    get_journal_path,
    get_relative_journal_path,
)


class TestGetAppDataDir:
    def test_returns_path(self):
        result = get_app_data_dir()
        assert isinstance(result, Path)

    def test_contains_leadership_os(self):
        result = get_app_data_dir()
        assert result.name == "leadership-os"

    def test_platform_specific(self):
        result = get_app_data_dir()
        if sys.platform == "linux":
            assert ".local" in str(result)
        elif sys.platform == "darwin":
            assert "Library" in str(result)
        elif sys.platform == "win32":
            assert "AppData" in str(result) or "Roaming" in str(result)


class TestGetDefaultVaultPath:
    def test_returns_path(self):
        result = get_default_vault_path()
        assert isinstance(result, Path)

    def test_ends_with_obsidian(self):
        result = get_default_vault_path()
        assert result.name == "Obsidian"


class TestGetDefaultJournalDir:
    def test_returns_daily_notes(self):
        assert get_default_journal_dir() == "Daily Notes"


class TestEnsureDirectory:
    def test_creates_directory(self, tmp_dir: Path):
        new_dir = tmp_dir / "new_subdir"
        result = ensure_directory(new_dir)
        assert result.exists()
        assert result.is_dir()

    def test_creates_nested_directories(self, tmp_dir: Path):
        nested = tmp_dir / "a" / "b" / "c"
        result = ensure_directory(nested)
        assert result.exists()

    def test_existing_directory_ok(self, tmp_dir: Path):
        result = ensure_directory(tmp_dir)
        assert result.exists()


class TestExpandUserPath:
    def test_expands_tilde(self):
        result = expand_user_path("~/test")
        assert "~" not in str(result)
        assert result.is_absolute()


class TestIsValidDirectory:
    def test_valid_directory(self, tmp_dir: Path):
        assert is_valid_directory(tmp_dir) is True

    def test_invalid_directory(self, tmp_dir: Path):
        assert is_valid_directory(tmp_dir / "nonexistent") is False

    def test_file_not_directory(self, tmp_dir: Path):
        test_file = tmp_dir / "file.txt"
        test_file.write_text("hello")
        assert is_valid_directory(test_file) is False


class TestGetJournalPath:
    def test_returns_correct_path(self):
        result = get_journal_path("~/Documents/Obsidian", "Daily Notes", "2026-07-14")
        assert isinstance(result, Path)
        assert "2026-07-14.md" in str(result)
        assert "Daily Notes" in str(result)


class TestGetRelativeJournalPath:
    def test_returns_correct_relative_path(self):
        result = get_relative_journal_path("Daily Notes", "2026-07-14")
        assert result == "Daily Notes/2026-07-14.md"

    def test_custom_journal_dir(self):
        result = get_relative_journal_path("Journals", "2026-12-31")
        assert result == "Journals/2026-12-31.md"
