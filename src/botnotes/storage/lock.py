"""Read/Write file lock for cross-process and cross-thread synchronization."""

from __future__ import annotations

import fcntl
import os
import threading
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path


@dataclass
class _ThreadLockState:
    """Per-thread lock state."""

    fd: int | None = None
    lock_count: int = 0
    lock_mode: int = 0  # 0=none, 1=read, 2=write


class RWFileLock:
    """Read/Write file lock using fcntl.

    Provides shared (read) and exclusive (write) locking:
    - Multiple readers can hold the lock simultaneously
    - Writers have exclusive access, blocking all readers and other writers

    Thread-safe: Each thread maintains its own lock state via thread-local storage.
    Cross-process safe: Uses OS-level fcntl.flock for synchronization.

    Supports reentrant locking within the same thread:
    - If already holding a write lock, nested read/write locks are no-ops
    - If already holding a read lock, nested read locks are no-ops
    - Nested write lock inside read lock is an error (would deadlock)

    This is an advisory lock - processes must cooperate by using the lock.
    """

    # Lock modes for internal tracking
    _MODE_NONE = 0
    _MODE_READ = 1
    _MODE_WRITE = 2

    def __init__(self, lock_path: Path) -> None:
        """Initialize the lock.

        Args:
            lock_path: Path to the lock file (will be created if needed)
        """
        self.lock_path = Path(lock_path)
        self.lock_path.parent.mkdir(parents=True, exist_ok=True)
        # Thread-local storage for per-thread lock state
        self._local = threading.local()

    def _get_state(self) -> _ThreadLockState:
        """Get the lock state for the current thread."""
        state: _ThreadLockState | None = getattr(self._local, "state", None)
        if state is None:
            state = _ThreadLockState()
            self._local.state = state
        return state

    @contextmanager
    def read_lock(self) -> Iterator[None]:
        """Acquire a shared (read) lock.

        Multiple readers can hold this lock simultaneously.
        Blocks if a writer holds an exclusive lock.

        Reentrant: if this thread already holds any lock, just increments count.
        """
        state = self._get_state()

        if state.lock_mode == self._MODE_WRITE:
            # This thread already has exclusive lock, read is implicitly allowed
            state.lock_count += 1
            try:
                yield
            finally:
                state.lock_count -= 1
            return

        if state.lock_mode == self._MODE_READ:
            # This thread already has shared lock, just increment count
            state.lock_count += 1
            try:
                yield
            finally:
                state.lock_count -= 1
            return

        # No lock held by this thread, acquire shared lock
        fd = os.open(str(self.lock_path), os.O_RDWR | os.O_CREAT)
        try:
            fcntl.flock(fd, fcntl.LOCK_SH)
            state.fd = fd
            state.lock_mode = self._MODE_READ
            state.lock_count = 1
            yield
        finally:
            state.lock_count -= 1
            if state.lock_count == 0:
                fcntl.flock(fd, fcntl.LOCK_UN)
                os.close(fd)
                state.fd = None
                state.lock_mode = self._MODE_NONE

    @contextmanager
    def write_lock(self) -> Iterator[None]:
        """Acquire an exclusive (write) lock.

        Only one writer can hold this lock at a time.
        Blocks all readers and other writers.

        Reentrant: if this thread already holds a write lock, just increments count.
        Raises RuntimeError if trying to upgrade from read to write lock.
        """
        state = self._get_state()

        if state.lock_mode == self._MODE_WRITE:
            # This thread already has exclusive lock, just increment count
            state.lock_count += 1
            try:
                yield
            finally:
                state.lock_count -= 1
            return

        if state.lock_mode == self._MODE_READ:
            # Cannot upgrade from read to write - would deadlock
            raise RuntimeError(
                "Cannot acquire write lock while holding read lock (would deadlock)"
            )

        # No lock held by this thread, acquire exclusive lock
        fd = os.open(str(self.lock_path), os.O_RDWR | os.O_CREAT)
        try:
            fcntl.flock(fd, fcntl.LOCK_EX)
            state.fd = fd
            state.lock_mode = self._MODE_WRITE
            state.lock_count = 1
            yield
        finally:
            state.lock_count -= 1
            if state.lock_count == 0:
                fcntl.flock(fd, fcntl.LOCK_UN)
                os.close(fd)
                state.fd = None
                state.lock_mode = self._MODE_NONE
