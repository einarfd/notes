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

        result = service.update_note("updatable", title="Updated")

        assert result is not None
        assert result.note.title == "Updated"

    def test_update_note_not_found(self, config: Config):
        """Test updating a nonexistent note."""
        service = NoteService(config)

        result = service.update_note("nonexistent", title="New")

        assert result is None

    def test_update_note_add_tags(self, config: Config):
        """Test adding tags to a note."""
        service = NoteService(config)
        service.create_note(path="note", title="Note", content="", tags=["existing"])

        result = service.update_note("note", add_tags=["new", "another"])

        assert result is not None
        assert sorted(result.note.tags) == ["another", "existing", "new"]

    def test_update_note_remove_tags(self, config: Config):
        """Test removing tags from a note."""
        service = NoteService(config)
        service.create_note(path="note", title="Note", content="", tags=["keep", "remove"])

        result = service.update_note("note", remove_tags=["remove"])

        assert result is not None
        assert result.note.tags == ["keep"]

    def test_update_note_add_and_remove_tags(self, config: Config):
        """Test adding and removing tags simultaneously."""
        service = NoteService(config)
        service.create_note(path="note", title="Note", content="", tags=["a", "b", "c"])

        result = service.update_note("note", add_tags=["d"], remove_tags=["b"])

        assert result is not None
        assert sorted(result.note.tags) == ["a", "c", "d"]

    def test_update_note_tags_mutually_exclusive(self, config: Config):
        """Test that tags is mutually exclusive with add_tags/remove_tags."""
        import pytest

        service = NoteService(config)
        service.create_note(path="note", title="Note", content="", tags=["old"])

        with pytest.raises(ValueError, match="Cannot use 'tags' with 'add_tags' or 'remove_tags'"):
            service.update_note("note", tags=["new"], add_tags=["extra"])

        with pytest.raises(ValueError, match="Cannot use 'tags' with 'add_tags' or 'remove_tags'"):
            service.update_note("note", tags=["new"], remove_tags=["old"])

    def test_update_note_add_duplicate_tag(self, config: Config):
        """Test adding a tag that already exists is idempotent."""
        service = NoteService(config)
        service.create_note(path="note", title="Note", content="", tags=["existing"])

        result = service.update_note("note", add_tags=["existing"])

        assert result is not None
        assert result.note.tags == ["existing"]

    def test_update_note_remove_nonexistent_tag(self, config: Config):
        """Test removing a nonexistent tag is a no-op."""
        service = NoteService(config)
        service.create_note(path="note", title="Note", content="", tags=["existing"])

        result = service.update_note("note", remove_tags=["nonexistent"])

        assert result is not None
        assert result.note.tags == ["existing"]


class TestNoteServiceDelete:
    """Tests for NoteService.delete_note."""

    def test_delete_note(self, config: Config):
        """Test deleting a note."""
        service = NoteService(config)
        service.create_note(path="deletable", title="Delete Me", content="Bye")

        result = service.delete_note("deletable")

        assert result.deleted is True
        assert service.read_note("deletable") is None

    def test_delete_note_not_found(self, config: Config):
        """Test deleting a nonexistent note."""
        service = NoteService(config)

        result = service.delete_note("nonexistent")

        assert result.deleted is False

    def test_delete_note_warns_about_backlinks(self, config: Config):
        """Test deleting a note that has backlinks warns about broken links."""
        service = NoteService(config)
        service.create_note(path="target", title="Target", content="Content")
        service.create_note(path="source", title="Source", content="Link to [[target]]")

        result = service.delete_note("target")

        assert result.deleted is True
        assert len(result.backlinks_warning) == 1
        assert result.backlinks_warning[0].source_path == "source"


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


class TestNoteServiceListInFolder:
    """Tests for NoteService.list_notes_in_folder."""

    def test_list_notes_in_folder_top_level(self, config: Config):
        """Test listing top-level notes and subfolders."""
        service = NoteService(config)
        service.create_note(path="top1", title="Top 1", content="")
        service.create_note(path="top2", title="Top 2", content="")
        service.create_note(path="folder/nested", title="Nested", content="")

        result = service.list_notes_in_folder("")

        assert result["notes"] == ["top1", "top2"]
        assert result["subfolders"] == ["folder"]

    def test_list_notes_in_folder(self, config: Config):
        """Test listing notes and subfolders in a specific folder."""
        service = NoteService(config)
        service.create_note(path="top", title="Top", content="")
        service.create_note(path="projects/proj1", title="Proj 1", content="")
        service.create_note(path="projects/proj2", title="Proj 2", content="")
        service.create_note(path="projects/sub/note", title="Sub", content="")
        service.create_note(path="other/note", title="Other", content="")

        result = service.list_notes_in_folder("projects")

        assert result["notes"] == ["projects/proj1", "projects/proj2"]
        assert result["subfolders"] == ["projects/sub"]

    def test_list_notes_in_folder_empty_result(self, config: Config):
        """Test listing from a folder with no notes or subfolders."""
        service = NoteService(config)
        service.create_note(path="elsewhere/note", title="Note", content="")

        result = service.list_notes_in_folder("nonexistent")

        assert result == {"notes": [], "subfolders": []}


class TestNoteServiceMove:
    """Tests for NoteService.update_note with new_path (moving notes)."""

    def test_move_note(self, config: Config):
        """Test moving a note to a new path."""
        service = NoteService(config)
        service.create_note(path="old/path", title="Note", content="Content")

        result = service.update_note("old/path", new_path="new/path")

        assert result is not None
        assert result.note.path == "new/path"
        assert service.read_note("old/path") is None
        assert service.read_note("new/path") is not None

    def test_move_note_updates_backlinks(self, config: Config):
        """Test that moving a note updates links in other notes."""
        service = NoteService(config)
        service.create_note(path="target", title="Target", content="Target content")
        service.create_note(path="source", title="Source", content="Link to [[target]]")

        result = service.update_note("target", new_path="moved/target", update_backlinks=True)

        assert result is not None
        assert result.backlinks_updated == ["source"]
        assert result.backlinks_warning == []

        # Check that source note was updated
        source = service.read_note("source")
        assert source is not None
        assert "[[moved/target]]" in source.content
        assert "[[target]]" not in source.content

    def test_move_note_updates_backlinks_preserves_display_text(self, config: Config):
        """Test that moving preserves display text in links."""
        service = NoteService(config)
        service.create_note(path="target", title="Target", content="Content")
        service.create_note(path="source", title="Source", content="Link to [[target|My Target]]")

        service.update_note("target", new_path="moved", update_backlinks=True)

        source = service.read_note("source")
        assert source is not None
        assert "[[moved|My Target]]" in source.content

    def test_move_note_warns_without_update(self, config: Config):
        """Test that moving without update_backlinks warns about broken links."""
        service = NoteService(config)
        service.create_note(path="target", title="Target", content="Content")
        service.create_note(path="source", title="Source", content="Link to [[target]]")

        result = service.update_note("target", new_path="moved", update_backlinks=False)

        assert result is not None
        assert result.backlinks_updated == []
        assert len(result.backlinks_warning) == 1
        assert result.backlinks_warning[0].source_path == "source"

        # Check that source was NOT updated
        source = service.read_note("source")
        assert source is not None
        assert "[[target]]" in source.content

    def test_move_note_to_existing_path_raises(self, config: Config):
        """Test that moving to an existing path raises ValueError."""
        import pytest

        service = NoteService(config)
        service.create_note(path="note1", title="Note 1", content="Content")
        service.create_note(path="note2", title="Note 2", content="Content")

        with pytest.raises(ValueError, match="Note already exists at 'note2'"):
            service.update_note("note1", new_path="note2")

    def test_move_note_same_path_no_op(self, config: Config):
        """Test that moving to the same path is a no-op."""
        service = NoteService(config)
        service.create_note(path="note", title="Note", content="Content")

        result = service.update_note("note", new_path="note")

        assert result is not None
        assert result.note.path == "note"
        assert result.backlinks_updated == []
        assert result.backlinks_warning == []

    def test_move_note_updates_search_index(self, config: Config):
        """Test that moving a note updates the search index."""
        service = NoteService(config)
        service.create_note(path="old", title="Searchable", content="Find me")

        service.update_note("old", new_path="new")

        # Search should find it at new path
        results = service.search_notes("Searchable")
        assert len(results) == 1
        assert results[0]["path"] == "new"

    def test_move_note_updates_backlinks_index(self, config: Config):
        """Test that moving a note updates the backlinks index for its outgoing links."""
        service = NoteService(config)
        service.create_note(path="target", title="Target", content="Target")
        service.create_note(path="source", title="Source", content="Link to [[target]]")

        service.update_note("source", new_path="moved-source")

        # Backlinks to target should now show moved-source
        backlinks = service.get_backlinks("target")
        assert len(backlinks) == 1
        assert backlinks[0].source_path == "moved-source"


class TestNoteServiceBacklinks:
    """Tests for NoteService backlinks functionality."""

    def test_create_note_indexes_links(self, config: Config):
        """Test that creating a note indexes its wiki links."""
        service = NoteService(config)
        service.create_note(path="target", title="Target", content="Target content")
        service.create_note(path="source", title="Source", content="Link to [[target]]")

        backlinks = service.get_backlinks("target")

        assert len(backlinks) == 1
        assert backlinks[0].source_path == "source"

    def test_update_note_updates_links(self, config: Config):
        """Test that updating note content updates the links index."""
        service = NoteService(config)
        service.create_note(path="target-a", title="Target A", content="A")
        service.create_note(path="target-b", title="Target B", content="B")
        service.create_note(path="source", title="Source", content="Link to [[target-a]]")

        # Verify initial state
        assert len(service.get_backlinks("target-a")) == 1
        assert len(service.get_backlinks("target-b")) == 0

        # Update to link to target-b instead
        service.update_note("source", content="Link to [[target-b]]")

        # Old link should be gone, new link should exist
        assert len(service.get_backlinks("target-a")) == 0
        assert len(service.get_backlinks("target-b")) == 1

    def test_get_backlinks_nonexistent_path(self, config: Config):
        """Test getting backlinks for a non-existent path (broken links)."""
        service = NoteService(config)
        service.create_note(path="source", title="Source", content="Link to [[nonexistent]]")

        backlinks = service.get_backlinks("nonexistent")

        assert len(backlinks) == 1
        assert backlinks[0].source_path == "source"

    def test_get_backlinks_empty(self, config: Config):
        """Test getting backlinks when none exist."""
        service = NoteService(config)
        service.create_note(path="lonely", title="Lonely", content="No one links to me")

        backlinks = service.get_backlinks("lonely")

        assert backlinks == []

    def test_multiple_links_tracked(self, config: Config):
        """Test that multiple links from the same note are tracked."""
        service = NoteService(config)
        service.create_note(path="target", title="Target", content="Target")
        service.create_note(
            path="source",
            title="Source",
            content="Line 1: [[target]]\nLine 3: [[target|Display]]",
        )

        backlinks = service.get_backlinks("target")

        assert len(backlinks) == 1
        assert backlinks[0].source_path == "source"
        assert backlinks[0].link_count == 2
        assert 1 in backlinks[0].line_numbers
        # Line 2 would be the blank line, so second link is on line 2 (after split)
        # Actually, "Line 1: [[target]]\nLine 3: [[target|Display]]" has 2 lines
        assert 2 in backlinks[0].line_numbers
