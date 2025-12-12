"""Integration tests for MCP tools."""

import pytest
from fastmcp.exceptions import ToolError

from notes.config import Config
from notes.tools.links import get_backlinks
from notes.tools.notes import (
    create_note,
    delete_note,
    list_notes,
    list_notes_in_folder,
    read_note,
    update_note,
)
from notes.tools.search import search_notes
from notes.tools.tags import find_by_tag, list_tags

# Access underlying functions (unwrap from @mcp.tool() decorator)
_create_note = create_note.fn
_read_note = read_note.fn
_get_backlinks = get_backlinks.fn
_update_note = update_note.fn
_delete_note = delete_note.fn
_list_notes = list_notes.fn
_list_notes_in_folder = list_notes_in_folder.fn
_search_notes = search_notes.fn
_list_tags = list_tags.fn
_find_by_tag = find_by_tag.fn


class TestCreateNote:
    """Tests for create_note tool."""

    def test_create_note(self, mock_config: Config):
        """Test creating a note."""
        result = _create_note(
            path="test/note",
            title="Test Note",
            content="Hello world",
            tags=["test", "example"],
        )

        assert "Created note at 'test/note'" in result

    def test_create_note_without_tags(self, mock_config: Config):
        """Test creating a note without tags."""
        result = _create_note(
            path="simple",
            title="Simple Note",
            content="No tags here",
        )

        assert "Created note at 'simple'" in result


class TestReadNote:
    """Tests for read_note tool."""

    def test_read_note(self, mock_config: Config):
        """Test reading a note."""
        _create_note(path="readable", title="Readable", content="Content here")

        result = _read_note("readable")

        assert result["path"] == "readable"
        assert result["title"] == "Readable"
        assert result["content"] == "Content here"
        assert "created_at" in result
        assert "updated_at" in result

    def test_read_note_not_found(self, mock_config: Config):
        """Test reading a nonexistent note raises ToolError."""
        with pytest.raises(ToolError, match="Note not found: 'nonexistent'"):
            _read_note("nonexistent")


class TestUpdateNote:
    """Tests for update_note tool."""

    def test_update_note_title(self, mock_config: Config):
        """Test updating note title."""
        _create_note(path="updatable", title="Original", content="Content")

        result = _update_note("updatable", title="Updated Title")

        assert "Updated note at 'updatable'" in result

        # Verify the update
        read_result = _read_note("updatable")
        assert read_result["title"] == "Updated Title"

    def test_update_note_content(self, mock_config: Config):
        """Test updating note content."""
        _create_note(path="updatable2", title="Title", content="Original content")

        _update_note("updatable2", content="New content")

        read_result = _read_note("updatable2")
        assert read_result["content"] == "New content"

    def test_update_note_tags(self, mock_config: Config):
        """Test updating note tags."""
        _create_note(path="updatable3", title="Title", content="Content", tags=["old"])

        _update_note("updatable3", tags=["new", "tags"])

        read_result = _read_note("updatable3")
        assert read_result["tags"] == ["new", "tags"]

    def test_update_note_add_tags(self, mock_config: Config):
        """Test adding tags to a note."""
        _create_note(path="taggable", title="Note", content="", tags=["existing"])

        _update_note("taggable", add_tags=["new", "another"])

        result = _read_note("taggable")
        assert sorted(result["tags"]) == ["another", "existing", "new"]

    def test_update_note_remove_tags(self, mock_config: Config):
        """Test removing tags from a note."""
        _create_note(path="taggable2", title="Note", content="", tags=["keep", "remove"])

        _update_note("taggable2", remove_tags=["remove"])

        result = _read_note("taggable2")
        assert result["tags"] == ["keep"]

    def test_update_note_add_and_remove_tags(self, mock_config: Config):
        """Test adding and removing tags simultaneously."""
        _create_note(path="taggable3", title="Note", content="", tags=["a", "b"])

        _update_note("taggable3", add_tags=["c"], remove_tags=["a"])

        result = _read_note("taggable3")
        assert sorted(result["tags"]) == ["b", "c"]

    def test_update_note_tags_mutually_exclusive(self, mock_config: Config):
        """Test that tags is mutually exclusive with add_tags/remove_tags."""
        _create_note(path="taggable4", title="Note", content="", tags=["old"])

        with pytest.raises(ToolError, match="Cannot use 'tags' with 'add_tags' or 'remove_tags'"):
            _update_note("taggable4", tags=["new"], add_tags=["extra"])

    def test_update_note_not_found(self, mock_config: Config):
        """Test updating a nonexistent note raises ToolError."""
        with pytest.raises(ToolError, match="Note not found: 'nonexistent'"):
            _update_note("nonexistent", title="New Title")

    def test_update_note_move(self, mock_config: Config):
        """Test moving a note to a new path."""
        _create_note(path="original", title="Note", content="Content")

        result = _update_note("original", new_path="moved")

        assert "Moved note from 'original' to 'moved'" in result
        with pytest.raises(ToolError, match="Note not found"):
            _read_note("original")
        note = _read_note("moved")
        assert note["title"] == "Note"

    def test_update_note_move_with_backlink_updates(self, mock_config: Config):
        """Test moving a note updates backlinks in other notes."""
        _create_note(path="target", title="Target", content="Target content")
        _create_note(path="source", title="Source", content="Link to [[target]]")

        result = _update_note("target", new_path="new-target", update_backlinks=True)

        assert "Moved note from 'target' to 'new-target'" in result
        assert "Updated links in 1 notes" in result
        assert "source" in result

        # Verify the source was updated
        source = _read_note("source")
        assert "[[new-target]]" in source["content"]

    def test_update_note_move_without_backlink_updates(self, mock_config: Config):
        """Test moving a note without updating backlinks shows warning."""
        _create_note(path="target", title="Target", content="Content")
        _create_note(path="source", title="Source", content="Link to [[target]]")

        result = _update_note("target", new_path="new-target", update_backlinks=False)

        assert "Moved note from 'target' to 'new-target'" in result
        assert "Warning:" in result
        assert "source" in result
        assert "broken" in result

        # Verify the source was NOT updated
        source = _read_note("source")
        assert "[[target]]" in source["content"]

    def test_update_note_move_to_existing_raises(self, mock_config: Config):
        """Test moving to an existing path raises ToolError."""
        _create_note(path="note1", title="Note 1", content="Content")
        _create_note(path="note2", title="Note 2", content="Content")

        with pytest.raises(ToolError, match="Note already exists at 'note2'"):
            _update_note("note1", new_path="note2")


class TestDeleteNote:
    """Tests for delete_note tool."""

    def test_delete_note(self, mock_config: Config):
        """Test deleting a note."""
        _create_note(path="deletable", title="Delete Me", content="Bye")

        result = _delete_note("deletable")

        assert "Deleted note at 'deletable'" in result

        # Verify it's gone
        with pytest.raises(ToolError, match="Note not found"):
            _read_note("deletable")

    def test_delete_note_not_found(self, mock_config: Config):
        """Test deleting a nonexistent note raises ToolError."""
        with pytest.raises(ToolError, match="Note not found: 'nonexistent'"):
            _delete_note("nonexistent")


class TestListNotes:
    """Tests for list_notes tool."""

    def test_list_notes_empty(self, mock_config: Config):
        """Test listing notes when none exist."""
        result = _list_notes()

        assert result == []

    def test_list_notes(self, mock_config: Config):
        """Test listing multiple notes."""
        _create_note(path="note1", title="Note 1", content="First")
        _create_note(path="note2", title="Note 2", content="Second")
        _create_note(path="folder/note3", title="Note 3", content="Third")

        result = _list_notes()

        assert "note1" in result
        assert "note2" in result
        assert "folder/note3" in result


class TestSearchNotes:
    """Tests for search_notes tool."""

    def test_search_notes(self, mock_config: Config):
        """Test searching for notes."""
        _create_note(path="python-guide", title="Python Guide", content="Learn Python")
        _create_note(path="rust-guide", title="Rust Guide", content="Learn Rust")

        result = _search_notes("Python")

        assert result["query"] == "Python"
        assert len(result["results"]) == 1
        assert result["results"][0]["title"] == "Python Guide"
        assert result["results"][0]["path"] == "python-guide"

    def test_search_notes_no_results(self, mock_config: Config):
        """Test search with no matching results."""
        _create_note(path="test", title="Test", content="Nothing special")

        result = _search_notes("nonexistent")

        assert result["query"] == "nonexistent"
        assert result["results"] == []

    def test_search_notes_by_content(self, mock_config: Config):
        """Test searching by content."""
        _create_note(path="secret", title="Normal Title", content="Contains secret keyword")

        result = _search_notes("secret")

        assert len(result["results"]) == 1
        assert result["results"][0]["title"] == "Normal Title"


class TestListTags:
    """Tests for list_tags tool."""

    def test_list_tags_empty(self, mock_config: Config):
        """Test listing tags when none exist."""
        result = _list_tags()

        assert result == {}

    def test_list_tags(self, mock_config: Config):
        """Test listing tags with counts."""
        _create_note(path="note1", title="Note 1", content="", tags=["python", "tutorial"])
        _create_note(path="note2", title="Note 2", content="", tags=["python", "guide"])
        _create_note(path="note3", title="Note 3", content="", tags=["rust"])

        result = _list_tags()

        assert result["python"] == 2
        assert result["tutorial"] == 1
        assert result["guide"] == 1
        assert result["rust"] == 1


class TestFindByTag:
    """Tests for find_by_tag tool."""

    def test_find_by_tag(self, mock_config: Config):
        """Test finding notes by tag."""
        _create_note(path="note1", title="Python Basics", content="", tags=["python"])
        _create_note(path="note2", title="Python Advanced", content="", tags=["python"])
        _create_note(path="note3", title="Rust Intro", content="", tags=["rust"])

        result = _find_by_tag("python")

        assert result["tag"] == "python"
        assert len(result["notes"]) == 2
        titles = [n["title"] for n in result["notes"]]
        assert "Python Basics" in titles
        assert "Python Advanced" in titles

    def test_find_by_tag_no_results(self, mock_config: Config):
        """Test finding notes by nonexistent tag."""
        _create_note(path="note1", title="Note", content="", tags=["other"])

        result = _find_by_tag("nonexistent")

        assert result["tag"] == "nonexistent"
        assert result["notes"] == []


class TestListNotesInFolder:
    """Tests for list_notes_in_folder tool."""

    def test_list_notes_in_folder_top_level(self, mock_config: Config):
        """Test listing top-level notes and subfolders."""
        _create_note(path="top1", title="Top 1", content="")
        _create_note(path="top2", title="Top 2", content="")
        _create_note(path="folder/nested", title="Nested", content="")

        result = _list_notes_in_folder("")

        assert result["folder"] == "/"
        assert result["subfolders"] == ["folder"]
        assert sorted(result["notes"]) == ["top1", "top2"]

    def test_list_notes_in_folder(self, mock_config: Config):
        """Test listing notes and subfolders in a specific folder."""
        _create_note(path="top", title="Top", content="")
        _create_note(path="projects/proj1", title="Proj 1", content="")
        _create_note(path="projects/proj2", title="Proj 2", content="")
        _create_note(path="projects/sub/note", title="Sub", content="")
        _create_note(path="other/note", title="Other", content="")

        result = _list_notes_in_folder("projects")

        assert result["folder"] == "projects"
        assert result["subfolders"] == ["projects/sub"]
        assert result["notes"] == ["projects/proj1", "projects/proj2"]
        assert "other/note" not in result["notes"]

    def test_list_notes_in_folder_empty(self, mock_config: Config):
        """Test listing from a folder with no contents."""
        _create_note(path="elsewhere/note", title="Note", content="")

        result = _list_notes_in_folder("nonexistent")

        assert result["folder"] == "nonexistent"
        assert result["subfolders"] == []
        assert result["notes"] == []

    def test_list_notes_in_folder_only_subfolders(self, mock_config: Config):
        """Test listing when folder has only subfolders, no direct notes."""
        _create_note(path="projects/web/note", title="Note", content="")

        result = _list_notes_in_folder("projects")

        assert result["folder"] == "projects"
        assert result["subfolders"] == ["projects/web"]
        assert result["notes"] == []


class TestGetBacklinks:
    """Tests for get_backlinks tool."""

    def test_get_backlinks(self, mock_config: Config):
        """Test finding backlinks to a note."""
        _create_note(path="target", title="Target", content="Target content")
        _create_note(path="source1", title="Source 1", content="Link to [[target]]")
        _create_note(path="source2", title="Source 2", content="Another [[target]] link")

        result = _get_backlinks("target")

        assert result["path"] == "target"
        assert result["exists"] is True
        assert len(result["backlinks"]) == 2
        source_paths = {bl["source_path"] for bl in result["backlinks"]}
        assert source_paths == {"source1", "source2"}

    def test_get_backlinks_no_links(self, mock_config: Config):
        """Test getting backlinks when none exist."""
        _create_note(path="lonely", title="Lonely", content="No one links to me")

        result = _get_backlinks("lonely")

        assert result["path"] == "lonely"
        assert result["exists"] is True
        assert result["backlinks"] == []

    def test_get_backlinks_nonexistent_note(self, mock_config: Config):
        """Test getting backlinks for a non-existent note (broken links)."""
        _create_note(path="source", title="Source", content="Link to [[nonexistent]]")

        result = _get_backlinks("nonexistent")

        assert result["path"] == "nonexistent"
        assert result["exists"] is False
        assert len(result["backlinks"]) == 1
        assert result["backlinks"][0]["source_path"] == "source"

    def test_get_backlinks_with_line_numbers(self, mock_config: Config):
        """Test that line numbers are included in backlinks."""
        _create_note(path="target", title="Target", content="Content")
        _create_note(
            path="source",
            title="Source",
            content="Line 1: [[target]]\nLine 2: text\nLine 3: [[target|Display]]",
        )

        result = _get_backlinks("target")

        assert len(result["backlinks"]) == 1
        bl = result["backlinks"][0]
        assert bl["source_path"] == "source"
        assert bl["link_count"] == 2
        assert 1 in bl["line_numbers"]
        assert 3 in bl["line_numbers"]

    def test_delete_note_shows_backlink_warning(self, mock_config: Config):
        """Test that deleting a note shows backlink warnings."""
        _create_note(path="target", title="Target", content="Target content")
        _create_note(path="source", title="Source", content="Link to [[target]]")

        result = _delete_note("target")

        assert "Deleted note at 'target'" in result
        assert "Warning:" in result
        assert "source" in result
        assert "broken" in result
