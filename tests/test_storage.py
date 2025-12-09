"""Tests for storage backends."""

from notes.models.note import Note
from notes.storage import FilesystemStorage


def test_save_and_load(storage: FilesystemStorage):
    """Test saving and loading a note."""
    note = Note(
        path="test/note",
        title="Test Note",
        content="This is test content.",
        tags=["test", "example"],
    )

    storage.save(note)
    loaded = storage.load("test/note")

    assert loaded is not None
    assert loaded.path == "test/note"
    assert loaded.title == "Test Note"
    assert loaded.content == "This is test content."
    assert loaded.tags == ["test", "example"]


def test_load_nonexistent(storage: FilesystemStorage):
    """Test loading a note that doesn't exist."""
    result = storage.load("nonexistent")
    assert result is None


def test_delete(storage: FilesystemStorage):
    """Test deleting a note."""
    note = Note(path="to-delete", title="Delete Me", content="Content")
    storage.save(note)

    assert storage.load("to-delete") is not None
    assert storage.delete("to-delete") is True
    assert storage.load("to-delete") is None


def test_delete_nonexistent(storage: FilesystemStorage):
    """Test deleting a note that doesn't exist."""
    assert storage.delete("nonexistent") is False


def test_list_all(storage: FilesystemStorage):
    """Test listing all notes."""
    storage.save(Note(path="a", title="A", content="A"))
    storage.save(Note(path="b", title="B", content="B"))
    storage.save(Note(path="nested/c", title="C", content="C"))

    paths = storage.list_all()
    assert sorted(paths) == ["a", "b", "nested/c"]
