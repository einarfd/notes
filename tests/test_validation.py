"""Tests for input validation and security."""

import pytest
from pydantic import ValidationError

from botnotes.models.note import Note
from botnotes.storage.filesystem import FilesystemStorage


class TestPathSanitization:
    """Test path sanitization in FilesystemStorage."""

    def test_normal_path(self, tmp_path):
        """Normal paths should work."""
        storage = FilesystemStorage(tmp_path)
        result = storage._sanitize_path("my-note")
        assert result == "my-note"

    def test_path_with_subdirectory(self, tmp_path):
        """Paths with subdirectories should work."""
        storage = FilesystemStorage(tmp_path)
        result = storage._sanitize_path("folder/my-note")
        assert result == "folder/my-note"

    def test_absolute_path_stripped(self, tmp_path):
        """Absolute paths should have leading slash stripped."""
        storage = FilesystemStorage(tmp_path)
        result = storage._sanitize_path("/my-note")
        assert result == "my-note"

    def test_absolute_path_etc(self, tmp_path):
        """Absolute paths to system directories should be sanitized."""
        storage = FilesystemStorage(tmp_path)
        # /etc/passwd becomes etc/passwd which is valid within base_dir
        result = storage._sanitize_path("/etc/passwd")
        assert result == "etc/passwd"

    def test_parent_traversal_rejected(self, tmp_path):
        """Parent directory traversal should be rejected."""
        storage = FilesystemStorage(tmp_path)
        with pytest.raises(ValueError, match="Invalid path"):
            storage._sanitize_path("../outside")

    def test_deep_parent_traversal_rejected(self, tmp_path):
        """Deep parent directory traversal should be rejected."""
        storage = FilesystemStorage(tmp_path)
        with pytest.raises(ValueError, match="Invalid path"):
            storage._sanitize_path("foo/../../outside")

    def test_encoded_traversal_rejected(self, tmp_path):
        """Various traversal attempts should be rejected."""
        storage = FilesystemStorage(tmp_path)
        with pytest.raises(ValueError, match="Invalid path"):
            storage._sanitize_path("foo/../../../etc/passwd")

    def test_empty_path_rejected(self, tmp_path):
        """Empty paths should be rejected."""
        storage = FilesystemStorage(tmp_path)
        with pytest.raises(ValueError, match="Path cannot be empty"):
            storage._sanitize_path("")

    def test_whitespace_only_rejected(self, tmp_path):
        """Whitespace-only paths should be rejected."""
        storage = FilesystemStorage(tmp_path)
        with pytest.raises(ValueError, match="Path cannot be empty"):
            storage._sanitize_path("   ")

    def test_slash_only_rejected(self, tmp_path):
        """Slash-only paths should be rejected."""
        storage = FilesystemStorage(tmp_path)
        with pytest.raises(ValueError, match="Path cannot be empty"):
            storage._sanitize_path("/")

    def test_whitespace_stripped(self, tmp_path):
        """Whitespace should be stripped from paths."""
        storage = FilesystemStorage(tmp_path)
        result = storage._sanitize_path("  my-note  ")
        assert result == "my-note"


class TestNotePathValidation:
    """Test path validation in Note model."""

    def test_valid_path(self):
        """Valid paths should work."""
        note = Note(path="my-note", title="Test", content="")
        assert note.path == "my-note"

    def test_path_with_underscores(self):
        """Paths with underscores should work."""
        note = Note(path="my_note_123", title="Test", content="")
        assert note.path == "my_note_123"

    def test_path_with_subdirectory(self):
        """Paths with subdirectories should work."""
        note = Note(path="folder/my-note", title="Test", content="")
        assert note.path == "folder/my-note"

    def test_path_leading_slash_stripped(self):
        """Leading slashes should be stripped."""
        note = Note(path="/my-note", title="Test", content="")
        assert note.path == "my-note"

    def test_path_empty_rejected(self):
        """Empty paths should be rejected."""
        with pytest.raises(ValidationError, match="Path cannot be empty"):
            Note(path="", title="Test", content="")

    def test_path_parent_traversal_rejected(self):
        """Parent traversal in path should be rejected."""
        with pytest.raises(ValidationError, match="cannot contain"):
            Note(path="../etc/passwd", title="Test", content="")

    def test_path_special_chars_rejected(self):
        """Special characters in path should be rejected."""
        with pytest.raises(ValidationError, match="can only contain"):
            Note(path="my note", title="Test", content="")  # space

    def test_path_dot_rejected(self):
        """Dots in path should be rejected."""
        with pytest.raises(ValidationError, match="can only contain"):
            Note(path="my.note", title="Test", content="")


class TestNoteTitleValidation:
    """Test title validation in Note model."""

    def test_valid_title(self):
        """Valid titles should work."""
        note = Note(path="test", title="My Note Title", content="")
        assert note.title == "My Note Title"

    def test_title_whitespace_stripped(self):
        """Whitespace should be stripped from titles."""
        note = Note(path="test", title="  My Title  ", content="")
        assert note.title == "My Title"

    def test_title_empty_rejected(self):
        """Empty titles should be rejected."""
        with pytest.raises(ValidationError, match="Title cannot be empty"):
            Note(path="test", title="", content="")

    def test_title_whitespace_only_rejected(self):
        """Whitespace-only titles should be rejected."""
        with pytest.raises(ValidationError, match="Title cannot be empty"):
            Note(path="test", title="   ", content="")

    def test_title_max_length(self):
        """Titles exceeding 200 characters should be rejected."""
        with pytest.raises(ValidationError, match="cannot exceed 200"):
            Note(path="test", title="x" * 201, content="")

    def test_title_at_max_length(self):
        """Titles at exactly 200 characters should work."""
        note = Note(path="test", title="x" * 200, content="")
        assert len(note.title) == 200


class TestNoteTagsValidation:
    """Test tags validation in Note model."""

    def test_valid_tags(self):
        """Valid tags should work."""
        note = Note(path="test", title="Test", content="", tags=["python", "web"])
        assert note.tags == ["python", "web"]

    def test_tags_with_hyphens(self):
        """Tags with hyphens should work."""
        note = Note(path="test", title="Test", content="", tags=["my-tag"])
        assert note.tags == ["my-tag"]

    def test_tags_with_underscores(self):
        """Tags with underscores should work."""
        note = Note(path="test", title="Test", content="", tags=["my_tag"])
        assert note.tags == ["my_tag"]

    def test_tags_whitespace_stripped(self):
        """Whitespace should be stripped from tags."""
        note = Note(path="test", title="Test", content="", tags=["  python  "])
        assert note.tags == ["python"]

    def test_tags_invalid_filtered_out(self):
        """Invalid tags should be filtered out (not rejected)."""
        note = Note(
            path="test",
            title="Test",
            content="",
            tags=["valid", "in valid", "also/invalid", "ok"],
        )
        assert note.tags == ["valid", "ok"]

    def test_tags_empty_filtered_out(self):
        """Empty tags should be filtered out."""
        note = Note(path="test", title="Test", content="", tags=["", "valid", "  "])
        assert note.tags == ["valid"]
