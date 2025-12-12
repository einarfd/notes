"""Tests for search functionality."""

from datetime import datetime

from notes.models.note import Note
from notes.search import SearchIndex


def test_index_and_search(search_index: SearchIndex):
    """Test indexing and searching notes."""
    note = Note(
        path="test/note",
        title="Python Programming",
        content="Learn Python programming with examples.",
        tags=["python", "tutorial"],
    )

    search_index.index_note(note)
    results = search_index.search("python")

    assert len(results) == 1
    assert results[0]["path"] == "test/note"
    assert results[0]["title"] == "Python Programming"


def test_search_no_results(search_index: SearchIndex):
    """Test search with no matching results."""
    note = Note(path="test", title="Test", content="Nothing here")
    search_index.index_note(note)

    results = search_index.search("nonexistent")
    assert len(results) == 0


def test_remove_from_index(search_index: SearchIndex):
    """Test removing a note from the index."""
    note = Note(path="removable", title="Remove Me", content="Some content")
    search_index.index_note(note)

    # Search for text in the title (path is not a searchable field)
    results = search_index.search("Remove")
    assert len(results) == 1

    search_index.remove_note("removable")
    results = search_index.search("Remove")
    assert len(results) == 0


def test_update_note_replaces_in_index(search_index: SearchIndex):
    """Test that updating a note replaces the old version in the index."""
    # Create initial note
    note = Note(
        path="projects/myproject",
        title="Original Title",
        content="Original content about testing.",
    )
    search_index.index_note(note)

    # Verify initial indexing
    results = search_index.search("Original")
    assert len(results) == 1
    assert results[0]["title"] == "Original Title"

    # Update the note with new title/content
    note.title = "Updated Title"
    note.content = "Updated content about testing."
    search_index.index_note(note)

    # Search should return only ONE result with the new title
    results = search_index.search("testing")
    assert len(results) == 1, f"Expected 1 result, got {len(results)}: {results}"
    assert results[0]["title"] == "Updated Title"

    # Old title should not be found
    results = search_index.search("Original")
    assert len(results) == 0


def test_search_by_date_range(search_index: SearchIndex):
    """Test searching notes by date range."""
    old_note = Note(
        path="old-note",
        title="Old Note",
        content="Created long ago",
        created_at=datetime(2023, 1, 15),
        updated_at=datetime(2023, 1, 15),
    )
    new_note = Note(
        path="new-note",
        title="New Note",
        content="Created recently",
        created_at=datetime(2024, 6, 15),
        updated_at=datetime(2024, 6, 15),
    )

    search_index.index_note(old_note)
    search_index.index_note(new_note)

    # Search for notes created in 2024
    results = search_index.search("created_at:[2024-01-01T00:00:00Z TO 2024-12-31T23:59:59Z]")
    assert len(results) == 1
    assert results[0]["path"] == "new-note"

    # Search for notes created in 2023
    results = search_index.search("created_at:[2023-01-01T00:00:00Z TO 2023-12-31T23:59:59Z]")
    assert len(results) == 1
    assert results[0]["path"] == "old-note"

    # Search for all notes (any date)
    results = search_index.search("created_at:[2020-01-01T00:00:00Z TO *]")
    assert len(results) == 2
