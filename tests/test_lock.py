"""Tests for the read/write file lock."""

import multiprocessing
import time
from pathlib import Path
from typing import Any

import pytest

from botnotes.storage.lock import RWFileLock


@pytest.fixture
def lock_path(tmp_path: Path) -> Path:
    """Create a temporary lock file path."""
    return tmp_path / "test.lock"


# Module-level functions for multiprocessing (can't pickle local functions)
def _reader_process(lock_path: Path, result_queue: Any) -> None:
    """Reader process for concurrent reader test."""
    lock = RWFileLock(lock_path)
    with lock.read_lock():
        start = time.time()
        time.sleep(0.1)
        end = time.time()
        result_queue.put((start, end))


def _writer_process(lock_path: Path, event_queue: Any) -> None:
    """Writer process for writer blocks reader test."""
    lock = RWFileLock(lock_path)
    with lock.write_lock():
        event_queue.put(("writer_start", time.time()))
        time.sleep(0.2)
        event_queue.put(("writer_end", time.time()))


def _reader_after_delay_process(lock_path: Path, event_queue: Any) -> None:
    """Reader process that starts with a small delay."""
    time.sleep(0.05)  # Small delay to ensure writer starts first
    lock = RWFileLock(lock_path)
    with lock.read_lock():
        event_queue.put(("reader_start", time.time()))
        event_queue.put(("reader_end", time.time()))


def _named_writer_process(lock_path: Path, event_queue: Any, name: str) -> None:
    """Named writer process for writer blocks writer test."""
    lock = RWFileLock(lock_path)
    with lock.write_lock():
        event_queue.put((f"{name}_start", time.time()))
        time.sleep(0.1)
        event_queue.put((f"{name}_end", time.time()))


def _create_note_process(config_dict: dict, path: str, result_queue: Any) -> None:
    """Process for concurrent note creation test."""
    from botnotes.config import Config
    from botnotes.services import NoteService

    cfg = Config(
        notes_dir=Path(config_dict["notes_dir"]),
        index_dir=Path(config_dict["index_dir"]),
    )
    service = NoteService(cfg)
    try:
        service.create_note(path=path, title=f"Note {path}", content="Test content")
        result_queue.put(("success", path))
    except Exception as e:
        result_queue.put(("error", str(e)))


class TestRWFileLock:
    """Tests for RWFileLock."""

    def test_read_lock_basic(self, lock_path: Path) -> None:
        """Test basic read lock acquisition and release."""
        lock = RWFileLock(lock_path)
        with lock.read_lock():
            state = lock._get_state()
            assert state.lock_mode == lock._MODE_READ
            assert state.lock_count == 1
        state = lock._get_state()
        assert state.lock_mode == lock._MODE_NONE
        assert state.lock_count == 0

    def test_write_lock_basic(self, lock_path: Path) -> None:
        """Test basic write lock acquisition and release."""
        lock = RWFileLock(lock_path)
        with lock.write_lock():
            state = lock._get_state()
            assert state.lock_mode == lock._MODE_WRITE
            assert state.lock_count == 1
        state = lock._get_state()
        assert state.lock_mode == lock._MODE_NONE
        assert state.lock_count == 0

    def test_read_lock_reentrant(self, lock_path: Path) -> None:
        """Test nested read locks increment count."""
        lock = RWFileLock(lock_path)
        with lock.read_lock():
            assert lock._get_state().lock_count == 1
            with lock.read_lock():
                assert lock._get_state().lock_count == 2
                with lock.read_lock():
                    assert lock._get_state().lock_count == 3
                assert lock._get_state().lock_count == 2
            assert lock._get_state().lock_count == 1
        assert lock._get_state().lock_count == 0

    def test_write_lock_reentrant(self, lock_path: Path) -> None:
        """Test nested write locks increment count."""
        lock = RWFileLock(lock_path)
        with lock.write_lock():
            assert lock._get_state().lock_count == 1
            with lock.write_lock():
                assert lock._get_state().lock_count == 2
            assert lock._get_state().lock_count == 1
        assert lock._get_state().lock_count == 0

    def test_read_lock_inside_write_lock(self, lock_path: Path) -> None:
        """Test read lock inside write lock succeeds (write implies read)."""
        lock = RWFileLock(lock_path)
        with lock.write_lock():
            assert lock._get_state().lock_mode == lock._MODE_WRITE
            with lock.read_lock():
                # Should still be in write mode, just increment count
                state = lock._get_state()
                assert state.lock_mode == lock._MODE_WRITE
                assert state.lock_count == 2
            assert lock._get_state().lock_count == 1
        assert lock._get_state().lock_count == 0

    def test_write_lock_inside_read_lock_raises(self, lock_path: Path) -> None:
        """Test write lock inside read lock raises RuntimeError."""
        lock = RWFileLock(lock_path)
        with (
            lock.read_lock(),
            pytest.raises(RuntimeError, match="Cannot acquire write lock"),
            lock.write_lock(),
        ):
            pass

    def test_lock_file_created(self, lock_path: Path) -> None:
        """Test lock file is created when lock is acquired."""
        lock = RWFileLock(lock_path)
        assert not lock_path.exists()
        with lock.read_lock():
            assert lock_path.exists()

    def test_lock_parent_dirs_created(self, tmp_path: Path) -> None:
        """Test parent directories are created for lock file."""
        lock_path = tmp_path / "nested" / "dirs" / "test.lock"
        assert not lock_path.parent.exists()
        # Parent is created on init
        _lock = RWFileLock(lock_path)
        assert lock_path.parent.exists()
        assert _lock.lock_path == lock_path  # Use the variable

    def test_thread_isolation(self, lock_path: Path) -> None:
        """Test that different threads have independent lock state tracking."""
        import threading

        lock = RWFileLock(lock_path)
        main_state: list[int] = []
        thread_state: list[int] = []
        barrier = threading.Barrier(2)

        def thread_func() -> None:
            # Thread should have its own state tracking
            state = lock._get_state()
            thread_state.append(state.lock_count)
            thread_state.append(state.lock_mode)
            # Wait for main thread to also check its state
            barrier.wait()

        # Main thread acquires lock
        with lock.write_lock():
            main_state_obj = lock._get_state()
            main_state.append(main_state_obj.lock_count)
            main_state.append(main_state_obj.lock_mode)

        # After releasing, start thread to check its state is independent
        t = threading.Thread(target=thread_func)
        t.start()

        # Main thread's state after release
        main_state_after = lock._get_state()
        main_state.append(main_state_after.lock_count)
        main_state.append(main_state_after.lock_mode)
        barrier.wait()  # Sync with thread
        t.join()

        # Main thread: had lock [1, WRITE], then released [0, NONE]
        assert main_state == [1, lock._MODE_WRITE, 0, lock._MODE_NONE]
        # Thread: has its own fresh state [0, NONE]
        assert thread_state == [0, lock._MODE_NONE]

    def test_cross_thread_write_blocking(self, lock_path: Path) -> None:
        """Test that flock blocks writes across threads."""
        import threading

        lock = RWFileLock(lock_path)
        events: list[tuple[str, float]] = []
        events_lock = threading.Lock()

        def record(event: str) -> None:
            with events_lock:
                events.append((event, time.time()))

        def writer_thread() -> None:
            time.sleep(0.05)  # Ensure main thread gets lock first
            record("thread_try")
            with lock.write_lock():
                record("thread_got")
                time.sleep(0.05)
                record("thread_release")

        # Main thread acquires write lock
        with lock.write_lock():
            record("main_got")
            # Start thread that will try to get write lock (should block)
            t = threading.Thread(target=writer_thread)
            t.start()
            time.sleep(0.1)  # Hold lock while thread tries to acquire
            record("main_release")

        t.join()

        # Thread should have gotten lock after main released
        event_names = [e[0] for e in events]
        assert event_names.index("thread_got") > event_names.index("main_release")


class TestCrossProcessLocking:
    """Tests for cross-process locking behavior."""

    def test_concurrent_readers(self, lock_path: Path) -> None:
        """Test multiple readers can hold the lock simultaneously."""
        ctx = multiprocessing.get_context("fork")
        queue: Any = ctx.Queue()
        processes = [
            ctx.Process(target=_reader_process, args=(lock_path, queue))
            for _ in range(3)
        ]

        for p in processes:
            p.start()
        for p in processes:
            p.join()

        # Collect results
        times = []
        while not queue.empty():
            times.append(queue.get())

        # All readers should overlap (concurrent execution)
        # Check that at least two readers were active at the same time
        starts = [t[0] for t in times]
        ends = [t[1] for t in times]
        # The max start should be less than the min end if they overlapped
        assert max(starts) < min(ends), "Readers did not overlap"

    def test_writer_blocks_readers(self, lock_path: Path) -> None:
        """Test writer blocks other readers."""
        ctx = multiprocessing.get_context("fork")
        queue: Any = ctx.Queue()
        writer_proc = ctx.Process(target=_writer_process, args=(lock_path, queue))
        reader_proc = ctx.Process(
            target=_reader_after_delay_process, args=(lock_path, queue)
        )

        writer_proc.start()
        reader_proc.start()
        writer_proc.join()
        reader_proc.join()

        # Collect events
        events = []
        while not queue.empty():
            events.append(queue.get())

        events.sort(key=lambda x: x[1])
        event_names = [e[0] for e in events]

        # Reader should start after writer ends
        writer_end_idx = event_names.index("writer_end")
        reader_start_idx = event_names.index("reader_start")
        assert reader_start_idx > writer_end_idx, "Reader started before writer finished"

    def test_writer_blocks_writers(self, lock_path: Path) -> None:
        """Test writer blocks other writers."""
        ctx = multiprocessing.get_context("fork")
        queue: Any = ctx.Queue()
        writer1 = ctx.Process(target=_named_writer_process, args=(lock_path, queue, "w1"))
        writer2 = ctx.Process(target=_named_writer_process, args=(lock_path, queue, "w2"))

        writer1.start()
        time.sleep(0.02)  # Small delay to ensure w1 starts first
        writer2.start()
        writer1.join()
        writer2.join()

        # Collect events
        events = []
        while not queue.empty():
            events.append(queue.get())

        events.sort(key=lambda x: x[1])
        event_names = [e[0] for e in events]

        # Writers should be serialized - one must complete before other starts
        # Either w1 finishes before w2 starts, or vice versa
        if event_names[0].startswith("w1"):
            w1_end_idx = event_names.index("w1_end")
            w2_start_idx = event_names.index("w2_start")
            assert w2_start_idx > w1_end_idx, "Writers overlapped"
        else:
            w2_end_idx = event_names.index("w2_end")
            w1_start_idx = event_names.index("w1_start")
            assert w1_start_idx > w2_end_idx, "Writers overlapped"


class TestNoteServiceLocking:
    """Integration tests for NoteService with locking."""

    def test_service_uses_same_lock_instance(self, tmp_path: Path) -> None:
        """Test that a service instance reuses the same lock."""
        from botnotes.config import Config
        from botnotes.services import NoteService

        config = Config(
            notes_dir=tmp_path / "notes",
            index_dir=tmp_path / "index",
        )
        service = NoteService(config)

        # Access lock twice - should be same instance
        lock1 = service._lock
        lock2 = service._lock
        assert lock1 is lock2

    def test_service_lock_path(self, tmp_path: Path) -> None:
        """Test service creates lock in index directory."""
        from botnotes.config import Config
        from botnotes.services import NoteService

        config = Config(
            notes_dir=tmp_path / "notes",
            index_dir=tmp_path / "index",
        )
        service = NoteService(config)

        expected_lock_path = config.index_dir / "botnotes.lock"
        assert service._lock.lock_path == expected_lock_path

    def test_concurrent_creates_succeed(self, tmp_path: Path) -> None:
        """Test concurrent note creates both succeed with locking.

        This verifies that locking prevents data corruption when multiple
        processes try to create notes at the same time. Without locking,
        we could see file corruption or git errors.
        """
        from botnotes.config import Config
        from botnotes.services import NoteService

        config = Config(
            notes_dir=tmp_path / "notes",
            index_dir=tmp_path / "index",
        )

        config_dict = {
            "notes_dir": str(config.notes_dir),
            "index_dir": str(config.index_dir),
        }

        ctx = multiprocessing.get_context("fork")
        queue: Any = ctx.Queue()
        processes = [
            ctx.Process(target=_create_note_process, args=(config_dict, f"note{i}", queue))
            for i in range(5)
        ]

        # Start all processes to create maximum contention
        for p in processes:
            p.start()
        for p in processes:
            p.join()

        # Collect results
        results = []
        while not queue.empty():
            results.append(queue.get())

        # All creates should succeed
        for status, info in results:
            assert status == "success", f"Create failed: {info}"

        # Verify all notes were created correctly
        service = NoteService(config)
        for i in range(5):
            note = service.read_note(f"note{i}")
            assert note is not None, f"note{i} not found"
            assert note.title == f"Note note{i}"
            assert note.content == "Test content"
