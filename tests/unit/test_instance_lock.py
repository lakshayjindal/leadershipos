"""Tests for the single-instance lock."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from leadership_os.core.instance_lock import (
    LOCK_FILENAME,
    InstanceLock,
    InstanceLockError,
)


@pytest.fixture
def lock_dir(tmp_path: Path) -> Path:
    return tmp_path


class TestInstanceLock:
    def test_acquire_creates_lock_file(self, lock_dir: Path):
        lock = InstanceLock(lock_dir)
        assert lock.acquire() is True
        assert (lock_dir / LOCK_FILENAME).exists()
        assert (lock_dir / LOCK_FILENAME).read_text().strip() == str(os.getpid())
        lock.release()

    def test_release_removes_lock_file(self, lock_dir: Path):
        lock = InstanceLock(lock_dir)
        lock.acquire()
        lock.release()
        assert not (lock_dir / LOCK_FILENAME).exists()

    def test_second_instance_raises(self, lock_dir: Path):
        lock1 = InstanceLock(lock_dir)
        lock1.acquire()
        try:
            lock2 = InstanceLock(lock_dir)
            with pytest.raises(InstanceLockError):
                lock2.acquire()
        finally:
            lock1.release()

    def test_stale_lock_is_removed(self, lock_dir: Path):
        # Write a PID that is very unlikely to exist
        stale_pid = 99999999
        (lock_dir / LOCK_FILENAME).write_text(str(stale_pid))
        lock = InstanceLock(lock_dir)
        assert lock.acquire() is True
        assert (lock_dir / LOCK_FILENAME).read_text().strip() == str(os.getpid())
        lock.release()

    def test_corrupted_lock_is_removed(self, lock_dir: Path):
        (lock_dir / LOCK_FILENAME).write_text("not-an-int")
        lock = InstanceLock(lock_dir)
        assert lock.acquire() is True
        lock.release()

    def test_release_does_not_remove_other_pid_lock(self, lock_dir: Path):
        # Simulate lock held by another PID
        (lock_dir / LOCK_FILENAME).write_text(str(os.getpid() + 1))
        lock = InstanceLock(lock_dir)
        # Even though we can't acquire, release should not remove the other PID's lock
        lock.release()
        assert (lock_dir / LOCK_FILENAME).exists()

    def test_is_locked(self, lock_dir: Path):
        lock = InstanceLock(lock_dir)
        assert not lock.is_locked()
        lock.acquire()
        assert lock.is_locked()
        lock.release()
        assert not lock.is_locked()
