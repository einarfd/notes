"""Integration tests for MCP tools."""

from notes.config import Config
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
        """Test reading a nonexistent note."""
        result = _read_note("nonexistent")

        assert result == "Note not found: 'nonexistent'"


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

    def test_update_note_not_found(self, mock_config: Config):
        """Test updating a nonexistent note."""
        result = _update_note("nonexistent", title="New Title")

        assert "Note not found: 'nonexistent'" in result


class TestDeleteNote:
    """Tests for delete_note tool."""

    def test_delete_note(self, mock_config: Config):
        """Test deleting a note."""
        _create_note(path="deletable", title="Delete Me", content="Bye")

        result = _delete_note("deletable")

        assert "Deleted note at 'deletable'" in result

        # Verify it's gone
        read_result = _read_note("deletable")
        assert "Note not found" in read_result

    def test_delete_note_not_found(self, mock_config: Config):
        """Test deleting a nonexistent note."""
        result = _delete_note("nonexistent")

        assert "Note not found: 'nonexistent'" in result


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
