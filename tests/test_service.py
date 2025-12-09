"""Tests for NoteService."""

from notes.config import Config
from notes.services import NoteService


class TestNoteServiceCreate:
    """Tests for NoteService.create_note."""

    def test_create_note(self, config: Config):
        """Test creating a note."""
        service = NoteService(config)

        note = service.create_note(
            path="test/note",
            title="Test Note",
            content="Hello world",
            tags=["test"],
        )

        assert note.path == "test/note"
        assert note.title == "Test Note"
        assert note.content == "Hello world"
        assert note.tags == ["test"]

    def test_create_note_without_tags(self, config: Config):
        """Test creating a note without tags."""
        service = NoteService(config)

        note = service.create_note(
            path="simple",
            title="Simple",
            content="Content",
        )

        assert note.tags == []


class TestNoteServiceRead:
    """Tests for NoteService.read_note."""

    def test_read_note(self, config: Config):
        """Test reading a note."""
        service = NoteService(config)
        service.create_note(path="readable", title="Readable", content="Content")

        note = service.read_note("readable")

        assert note is not None
        assert note.title == "Readable"

    def test_read_note_not_found(self, config: Config):
        """Test reading a nonexistent note."""
        service = NoteService(config)

        note = service.read_note("nonexistent")

        assert note is None


class TestNoteServiceUpdate:
    """Tests for NoteService.update_note."""

    def test_update_note(self, config: Config):
        """Test updating a note."""
        service = NoteService(config)
        service.create_note(path="updatable", title="Original", content="Content")

        updated = service.update_note("updatable", title="Updated")

        assert updated is not None
        assert updated.title == "Updated"

    def test_update_note_not_found(self, config: Config):
        """Test updating a nonexistent note."""
        service = NoteService(config)

        updated = service.update_note("nonexistent", title="New")

        assert updated is None


class TestNoteServiceDelete:
    """Tests for NoteService.delete_note."""

    def test_delete_note(self, config: Config):
        """Test deleting a note."""
        service = NoteService(config)
        service.create_note(path="deletable", title="Delete Me", content="Bye")

        result = service.delete_note("deletable")

        assert result is True
        assert service.read_note("deletable") is None

    def test_delete_note_not_found(self, config: Config):
        """Test deleting a nonexistent note."""
        service = NoteService(config)

        result = service.delete_note("nonexistent")

        assert result is False


class TestNoteServiceList:
    """Tests for NoteService.list_notes."""

    def test_list_notes_empty(self, config: Config):
        """Test listing notes when none exist."""
        service = NoteService(config)

        paths = service.list_notes()

        assert paths == []

    def test_list_notes(self, config: Config):
        """Test listing notes."""
        service = NoteService(config)
        service.create_note(path="note1", title="Note 1", content="")
        service.create_note(path="note2", title="Note 2", content="")

        paths = service.list_notes()

        assert "note1" in paths
        assert "note2" in paths


class TestNoteServiceSearch:
    """Tests for NoteService.search_notes."""

    def test_search_notes(self, config: Config):
        """Test searching notes."""
        service = NoteService(config)
        service.create_note(path="python", title="Python Guide", content="Learn Python")
        service.create_note(path="rust", title="Rust Guide", content="Learn Rust")

        results = service.search_notes("Python")

        assert len(results) == 1
        assert results[0]["title"] == "Python Guide"

    def test_search_notes_no_results(self, config: Config):
        """Test search with no results."""
        service = NoteService(config)
        service.create_note(path="test", title="Test", content="Nothing")

        results = service.search_notes("nonexistent")

        assert results == []


class TestNoteServiceTags:
    """Tests for NoteService tag methods."""

    def test_list_tags(self, config: Config):
        """Test listing tags."""
        service = NoteService(config)
        service.create_note(path="note1", title="Note 1", content="", tags=["python", "guide"])
        service.create_note(path="note2", title="Note 2", content="", tags=["python"])

        tags = service.list_tags()

        assert tags["python"] == 2
        assert tags["guide"] == 1

    def test_list_tags_empty(self, config: Config):
        """Test listing tags when none exist."""
        service = NoteService(config)

        tags = service.list_tags()

        assert tags == {}

    def test_find_by_tag(self, config: Config):
        """Test finding notes by tag."""
        service = NoteService(config)
        service.create_note(path="note1", title="Python 1", content="", tags=["python"])
        service.create_note(path="note2", title="Python 2", content="", tags=["python"])
        service.create_note(path="note3", title="Rust", content="", tags=["rust"])

        notes = service.find_by_tag("python")

        assert len(notes) == 2
        titles = [n.title for n in notes]
        assert "Python 1" in titles
        assert "Python 2" in titles

    def test_find_by_tag_no_results(self, config: Config):
        """Test finding notes by nonexistent tag."""
        service = NoteService(config)
        service.create_note(path="note1", title="Note", content="", tags=["other"])

        notes = service.find_by_tag("nonexistent")

        assert notes == []
