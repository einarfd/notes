"""Tests for search functionality."""

from datetime import datetime, timedelta
from unittest.mock import patch

from notes.models.note import Note
from notes.search import SearchIndex
from notes.search.tantivy_index import _preprocess_date_math


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


class TestDateMathPreprocessing:
    """Tests for date math preprocessing."""

    def test_now_replacement(self):
        """Test 'now' is replaced with current timestamp."""
        with patch("notes.search.tantivy_index.datetime") as mock_dt:
            mock_dt.now.return_value = datetime(2024, 6, 15, 12, 0, 0)
            result = _preprocess_date_math("created_at:[now TO *]")
            assert "2024-06-15T12:00:00Z" in result

    def test_now_minus_days(self):
        """Test 'now-7d' is replaced correctly."""
        with patch("notes.search.tantivy_index.datetime") as mock_dt:
            mock_dt.now.return_value = datetime(2024, 6, 15, 12, 0, 0)
            result = _preprocess_date_math("created_at:[now-7d TO now]")
            assert "2024-06-08T12:00:00Z" in result
            assert "2024-06-15T12:00:00Z" in result

    def test_now_plus_weeks(self):
        """Test 'now+2w' is replaced correctly."""
        with patch("notes.search.tantivy_index.datetime") as mock_dt:
            mock_dt.now.return_value = datetime(2024, 6, 15, 12, 0, 0)
            result = _preprocess_date_math("updated_at:[now TO now+2w]")
            assert "2024-06-15T12:00:00Z" in result
            assert "2024-06-29T12:00:00Z" in result

    def test_explicit_date(self):
        """Test explicit date YYYY-MM-DD is converted to ISO."""
        result = _preprocess_date_math("created_at:[2024-01-15 TO 2024-02-15]")
        assert "2024-01-15T00:00:00Z" in result
        assert "2024-02-15T00:00:00Z" in result

    def test_explicit_date_with_math(self):
        """Test explicit date with arithmetic."""
        result = _preprocess_date_math("created_at:[2024-01-01 TO 2024-01-01+1M]")
        assert "2024-01-01T00:00:00Z" in result
        assert "2024-01-31T00:00:00Z" in result  # +30 days

    def test_mixed_query(self):
        """Test date math mixed with text query."""
        with patch("notes.search.tantivy_index.datetime") as mock_dt:
            mock_dt.now.return_value = datetime(2024, 6, 15, 12, 0, 0)
            result = _preprocess_date_math("python AND created_at:[now-1M TO now]")
            assert "python AND" in result
            assert "2024-05-16T12:00:00Z" in result  # now - 30 days

    def test_no_date_expressions(self):
        """Test query without date expressions is unchanged."""
        query = "python tutorial"
        result = _preprocess_date_math(query)
        assert result == query


def test_search_with_date_math(search_index: SearchIndex):
    """Test searching with date math expressions."""
    # Create notes with specific dates
    recent_note = Note(
        path="recent",
        title="Recent Note",
        content="Created recently",
        created_at=datetime.now() - timedelta(days=3),
        updated_at=datetime.now() - timedelta(days=3),
    )
    old_note = Note(
        path="old",
        title="Old Note",
        content="Created long ago",
        created_at=datetime.now() - timedelta(days=30),
        updated_at=datetime.now() - timedelta(days=30),
    )

    search_index.index_note(recent_note)
    search_index.index_note(old_note)

    # Search for notes from last 7 days
    results = search_index.search("created_at:[now-7d TO now]")
    assert len(results) == 1
    assert results[0]["path"] == "recent"

    # Search for notes from last 60 days (should get both)
    results = search_index.search("created_at:[now-60d TO now]")
    assert len(results) == 2


class TestSearchIndexRebuild:
    """Tests for clear and rebuild functionality."""

    def test_clear_removes_all_documents(self, search_index: SearchIndex):
        """Test that clear removes all documents from the index."""
        note1 = Note(path="note1", title="First Note", content="Content 1")
        note2 = Note(path="note2", title="Second Note", content="Content 2")
        search_index.index_note(note1)
        search_index.index_note(note2)

        # Verify notes are indexed
        assert len(search_index.search("Note")) == 2

        search_index.clear()

        # Verify index is empty
        assert len(search_index.search("Note")) == 0

    def test_rebuild_reindexes_all_notes(self, search_index: SearchIndex):
        """Test that rebuild reindexes all provided notes."""
        notes = [
            Note(path="note1", title="First Note", content="Content 1"),
            Note(path="note2", title="Second Note", content="Content 2"),
            Note(path="note3", title="Third Note", content="Content 3"),
        ]

        count = search_index.rebuild(notes)

        assert count == 3
        assert len(search_index.search("Note")) == 3

    def test_rebuild_replaces_existing_index(self, search_index: SearchIndex):
        """Test that rebuild replaces the existing index."""
        # Index some initial notes
        old_note = Note(path="old", title="Old Note", content="Old content")
        search_index.index_note(old_note)

        # Rebuild with different notes
        new_notes = [
            Note(path="new1", title="New Note 1", content="New content"),
            Note(path="new2", title="New Note 2", content="New content"),
        ]
        search_index.rebuild(new_notes)

        # Old note should not be found
        assert len(search_index.search("Old")) == 0
        # New notes should be found
        assert len(search_index.search("New")) == 2

    def test_rebuild_empty_list(self, search_index: SearchIndex):
        """Test rebuild with empty list clears the index."""
        note = Note(path="note", title="Some Note", content="Content")
        search_index.index_note(note)

        count = search_index.rebuild([])

        assert count == 0
        assert len(search_index.search("Note")) == 0


def test_tag_exact_match_with_hyphen(search_index: SearchIndex):
    """Tags with hyphens are matched exactly, not split."""
    note = Note(
        path="ml-note",
        title="ML Guide",
        content="General content",
        tags=["machine-learning", "python"],
    )
    search_index.index_note(note)

    # Exact tag match should work
    results = search_index.search("tags:machine-learning")
    assert len(results) == 1

    # Partial match should NOT work (raw tokenizer)
    results = search_index.search("tags:machine")
    assert len(results) == 0


def test_title_boost_ranks_higher(search_index: SearchIndex):
    """Notes with search term in title rank higher than content-only."""
    content_note = Note(
        path="content-match",
        title="Programming Guide",
        content="Learn python programming.",
    )
    title_note = Note(
        path="title-match",
        title="Python Tutorial",
        content="Learn programming basics.",
    )
    search_index.index_note(content_note)
    search_index.index_note(title_note)

    results = search_index.search("python")
    assert len(results) == 2
    # Title match should rank first due to 2.0x boost
    assert results[0]["path"] == "title-match"
