"""Tests for backlinks index."""

from pathlib import Path

import pytest

from notes.links.index import BacklinkInfo, BacklinksIndex
from notes.links.parser import WikiLink


@pytest.fixture
def temp_dir(tmp_path: Path) -> Path:
    """Provide a temporary directory."""
    return tmp_path


@pytest.fixture
def index(temp_dir: Path) -> BacklinksIndex:
    """Provide a backlinks index."""
    return BacklinksIndex(temp_dir / "backlinks.json")


class TestBacklinksIndex:
    """Tests for BacklinksIndex."""

    def test_get_backlinks_empty(self, index: BacklinksIndex):
        """Test getting backlinks when none exist."""
        result = index.get_backlinks("nonexistent")

        assert result == []

    def test_update_and_get_backlinks(self, index: BacklinksIndex):
        """Test updating and retrieving backlinks."""
        links = [WikiLink(target_path="target/note", display_text=None, line_number=5)]

        index.update_note_links("source/note", links)
        backlinks = index.get_backlinks("target/note")

        assert len(backlinks) == 1
        assert backlinks[0].source_path == "source/note"
        assert backlinks[0].line_numbers == [5]
        assert backlinks[0].link_count == 1

    def test_multiple_links_to_same_target(self, index: BacklinksIndex):
        """Test multiple links from same source to same target."""
        links = [
            WikiLink(target_path="target", display_text=None, line_number=5),
            WikiLink(target_path="target", display_text="Text", line_number=10),
        ]

        index.update_note_links("source", links)
        backlinks = index.get_backlinks("target")

        assert len(backlinks) == 1
        assert backlinks[0].source_path == "source"
        assert backlinks[0].line_numbers == [5, 10]
        assert backlinks[0].link_count == 2

    def test_multiple_sources_to_same_target(self, index: BacklinksIndex):
        """Test multiple sources linking to the same target."""
        index.update_note_links(
            "source1", [WikiLink(target_path="target", display_text=None, line_number=1)]
        )
        index.update_note_links(
            "source2", [WikiLink(target_path="target", display_text=None, line_number=2)]
        )

        backlinks = index.get_backlinks("target")

        assert len(backlinks) == 2
        sources = {bl.source_path for bl in backlinks}
        assert sources == {"source1", "source2"}

    def test_update_removes_old_links(self, index: BacklinksIndex):
        """Test that updating a note removes its old links."""
        # First update with a link to target-a
        index.update_note_links(
            "source", [WikiLink(target_path="target-a", display_text=None, line_number=1)]
        )
        assert len(index.get_backlinks("target-a")) == 1

        # Update with a link to target-b instead
        index.update_note_links(
            "source", [WikiLink(target_path="target-b", display_text=None, line_number=1)]
        )

        # Old link should be gone
        assert index.get_backlinks("target-a") == []
        assert len(index.get_backlinks("target-b")) == 1

    def test_remove_note_as_source(self, index: BacklinksIndex):
        """Test removing a note removes its outgoing links."""
        index.update_note_links(
            "source", [WikiLink(target_path="target", display_text=None, line_number=1)]
        )
        assert len(index.get_backlinks("target")) == 1

        index.remove_note("source")

        assert index.get_backlinks("target") == []

    def test_remove_note_preserves_other_links(self, index: BacklinksIndex):
        """Test removing a note doesn't affect other sources."""
        index.update_note_links(
            "source1", [WikiLink(target_path="target", display_text=None, line_number=1)]
        )
        index.update_note_links(
            "source2", [WikiLink(target_path="target", display_text=None, line_number=2)]
        )

        index.remove_note("source1")

        backlinks = index.get_backlinks("target")
        assert len(backlinks) == 1
        assert backlinks[0].source_path == "source2"

    def test_rename_target(self, index: BacklinksIndex):
        """Test renaming a target path."""
        index.update_note_links(
            "source", [WikiLink(target_path="old/path", display_text=None, line_number=1)]
        )

        index.rename_target("old/path", "new/path")

        assert index.get_backlinks("old/path") == []
        backlinks = index.get_backlinks("new/path")
        assert len(backlinks) == 1
        assert backlinks[0].source_path == "source"

    def test_rename_nonexistent_target(self, index: BacklinksIndex):
        """Test renaming a target that has no backlinks."""
        # Should not raise an error
        index.rename_target("nonexistent", "new/path")
        assert index.get_backlinks("nonexistent") == []
        assert index.get_backlinks("new/path") == []

    def test_persistence(self, temp_dir: Path):
        """Test that the index is persisted to disk."""
        index1 = BacklinksIndex(temp_dir / "backlinks.json")
        index1.update_note_links(
            "source", [WikiLink(target_path="target", display_text=None, line_number=5)]
        )

        # Create a new index instance from the same file
        index2 = BacklinksIndex(temp_dir / "backlinks.json")
        backlinks = index2.get_backlinks("target")

        assert len(backlinks) == 1
        assert backlinks[0].source_path == "source"
        assert backlinks[0].line_numbers == [5]

    def test_update_empty_links_removes_all(self, index: BacklinksIndex):
        """Test updating with empty links removes all from source."""
        index.update_note_links(
            "source",
            [
                WikiLink(target_path="target-a", display_text=None, line_number=1),
                WikiLink(target_path="target-b", display_text=None, line_number=2),
            ],
        )

        # Update with no links
        index.update_note_links("source", [])

        assert index.get_backlinks("target-a") == []
        assert index.get_backlinks("target-b") == []

    def test_duplicate_line_numbers_deduplicated(self, index: BacklinksIndex):
        """Test that duplicate line numbers are not stored."""
        # Same link appearing twice on same line (edge case)
        links = [
            WikiLink(target_path="target", display_text=None, line_number=5),
            WikiLink(target_path="target", display_text="Text", line_number=5),
        ]

        index.update_note_links("source", links)
        backlinks = index.get_backlinks("target")

        assert len(backlinks) == 1
        # Should only have one line number 5, not duplicated
        assert backlinks[0].line_numbers == [5]


class TestBacklinkInfo:
    """Tests for BacklinkInfo dataclass."""

    def test_link_count(self):
        """Test the link_count property."""
        info = BacklinkInfo(source_path="source", line_numbers=[1, 5, 10])
        assert info.link_count == 3

    def test_link_count_empty(self):
        """Test link_count with no lines."""
        info = BacklinkInfo(source_path="source", line_numbers=[])
        assert info.link_count == 0


class TestBacklinksIndexRebuild:
    """Tests for clear and rebuild functionality."""

    def test_clear_removes_all_backlinks(self, index: BacklinksIndex):
        """Test that clear removes all backlinks from the index."""
        index.update_note_links(
            "source1", [WikiLink(target_path="target1", display_text=None, line_number=1)]
        )
        index.update_note_links(
            "source2", [WikiLink(target_path="target2", display_text=None, line_number=2)]
        )

        # Verify backlinks exist
        assert len(index.get_backlinks("target1")) == 1
        assert len(index.get_backlinks("target2")) == 1

        index.clear()

        # Verify index is empty
        assert index.get_backlinks("target1") == []
        assert index.get_backlinks("target2") == []

    def test_rebuild_reindexes_all_notes(self, index: BacklinksIndex):
        """Test that rebuild reindexes all provided notes."""
        from notes.models import Note

        notes = [
            Note(path="note1", title="Note 1", content="Link to [[target1]]"),
            Note(path="note2", title="Note 2", content="Link to [[target2]]"),
            Note(path="note3", title="Note 3", content="Links to [[target1]] and [[target2]]"),
        ]

        count = index.rebuild(notes)

        assert count == 3
        # target1 is linked from note1 and note3
        assert len(index.get_backlinks("target1")) == 2
        # target2 is linked from note2 and note3
        assert len(index.get_backlinks("target2")) == 2

    def test_rebuild_replaces_existing_index(self, index: BacklinksIndex):
        """Test that rebuild replaces the existing index."""
        from notes.models import Note

        # Create initial backlinks
        index.update_note_links(
            "old-source", [WikiLink(target_path="old-target", display_text=None, line_number=1)]
        )
        assert len(index.get_backlinks("old-target")) == 1

        # Rebuild with different notes
        new_notes = [
            Note(path="new-source", title="New", content="Link to [[new-target]]"),
        ]
        index.rebuild(new_notes)

        # Old backlinks should be gone
        assert index.get_backlinks("old-target") == []
        # New backlinks should exist
        assert len(index.get_backlinks("new-target")) == 1

    def test_rebuild_empty_list(self, index: BacklinksIndex):
        """Test rebuild with empty list clears the index."""
        index.update_note_links(
            "source", [WikiLink(target_path="target", display_text=None, line_number=1)]
        )

        count = index.rebuild([])

        assert count == 0
        assert index.get_backlinks("target") == []

    def test_rebuild_note_without_links(self, index: BacklinksIndex):
        """Test rebuild handles notes without links."""
        from notes.models import Note

        notes = [
            Note(path="no-links", title="No Links", content="Just plain text"),
            Note(path="has-links", title="Has Links", content="Link to [[target]]"),
        ]

        count = index.rebuild(notes)

        assert count == 2
        assert len(index.get_backlinks("target")) == 1
