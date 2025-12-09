"""Tests for search functionality."""

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
