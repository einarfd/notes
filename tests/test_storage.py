"""Tests for storage backends."""

from botnotes.models.note import Note
from botnotes.storage import FilesystemStorage


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


def test_list_by_prefix_top_level(storage: FilesystemStorage):
    """Test listing only top-level notes and subfolders."""
    storage.save(Note(path="top1", title="Top 1", content=""))
    storage.save(Note(path="top2", title="Top 2", content=""))
    storage.save(Note(path="folder/nested1", title="Nested 1", content=""))
    storage.save(Note(path="folder/deep/nested2", title="Nested 2", content=""))

    result = storage.list_by_prefix("")
    assert result["notes"] == ["top1", "top2"]
    assert result["subfolders"] == ["folder"]


def test_list_by_prefix_folder(storage: FilesystemStorage):
    """Test listing notes and subfolders in a specific folder."""
    storage.save(Note(path="top1", title="Top 1", content=""))
    storage.save(Note(path="projects/proj1", title="Proj 1", content=""))
    storage.save(Note(path="projects/proj2", title="Proj 2", content=""))
    storage.save(Note(path="projects/sub/proj3", title="Proj 3", content=""))
    storage.save(Note(path="other/note", title="Other", content=""))

    result = storage.list_by_prefix("projects")
    assert result["notes"] == ["projects/proj1", "projects/proj2"]
    assert result["subfolders"] == ["projects/sub"]


def test_list_by_prefix_nested_folder(storage: FilesystemStorage):
    """Test listing notes in a nested folder with no further subfolders."""
    storage.save(Note(path="projects/sub/a", title="A", content=""))
    storage.save(Note(path="projects/sub/b", title="B", content=""))
    storage.save(Note(path="projects/other", title="Other", content=""))

    result = storage.list_by_prefix("projects/sub")
    assert result["notes"] == ["projects/sub/a", "projects/sub/b"]
    assert result["subfolders"] == []


def test_list_by_prefix_empty_result(storage: FilesystemStorage):
    """Test listing from a folder with no notes or subfolders."""
    storage.save(Note(path="elsewhere/note", title="Note", content=""))

    result = storage.list_by_prefix("nonexistent")
    assert result == {"notes": [], "subfolders": [], "has_index": False}


def test_list_by_prefix_strips_slashes(storage: FilesystemStorage):
    """Test that prefix strips leading/trailing slashes."""
    storage.save(Note(path="folder/note", title="Note", content=""))

    expected = {"notes": ["folder/note"], "subfolders": [], "has_index": False}
    assert storage.list_by_prefix("folder") == expected
    assert storage.list_by_prefix("/folder") == expected
    assert storage.list_by_prefix("folder/") == expected
    assert storage.list_by_prefix("/folder/") == expected


def test_list_by_prefix_only_subfolders(storage: FilesystemStorage):
    """Test listing when folder has only subfolders, no direct notes."""
    storage.save(Note(path="projects/web/note1", title="Note 1", content=""))
    storage.save(Note(path="projects/api/note2", title="Note 2", content=""))

    result = storage.list_by_prefix("projects")
    assert result["notes"] == []
    assert result["subfolders"] == ["projects/api", "projects/web"]


def test_list_by_prefix_with_index_note(storage: FilesystemStorage):
    """Test that index notes are detected but excluded from notes list."""
    # Create an index note for projects folder
    storage.save(Note(path="projects/index", title="Projects Index", content=""))
    storage.save(Note(path="projects/proj1", title="Project 1", content=""))
    storage.save(Note(path="projects/proj2", title="Project 2", content=""))
    storage.save(Note(path="projects/sub/proj3", title="Project 3", content=""))

    result = storage.list_by_prefix("projects")
    # Index note should be excluded from list but has_index should be True
    assert result["notes"] == ["projects/proj1", "projects/proj2"]
    assert result["subfolders"] == ["projects/sub"]
    assert result["has_index"] is True


def test_list_by_prefix_root_index(storage: FilesystemStorage):
    """Test that root index note is detected."""
    storage.save(Note(path="index", title="Home", content=""))
    storage.save(Note(path="other", title="Other Note", content=""))

    result = storage.list_by_prefix("")
    assert result["notes"] == ["other"]
    assert result["has_index"] is True


def test_save_rejects_overlapping_note(storage: FilesystemStorage):
    """Test that saving a note at a path with children is rejected."""
    # First create a child note
    storage.save(Note(path="projects/foo", title="Foo", content=""))

    # Trying to create "projects" note should fail (overlap)
    import pytest
    with pytest.raises(ValueError, match="folder with that name exists"):
        storage.save(Note(path="projects", title="Projects", content=""))


def test_save_allows_index_note(storage: FilesystemStorage):
    """Test that index notes are allowed even when folder has children."""
    # First create a child note
    storage.save(Note(path="projects/foo", title="Foo", content=""))

    # Creating index note should work
    storage.save(Note(path="projects/index", title="Projects Index", content=""))
    assert storage.load("projects/index") is not None
