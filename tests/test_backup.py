"""Tests for backup and restore functionality."""

import tarfile
from pathlib import Path

import pytest

from botnotes.backup import clear_notes, export_notes, import_notes


@pytest.fixture
def notes_dir(tmp_path: Path) -> Path:
    """Create a temporary notes directory with test notes."""
    notes = tmp_path / "notes"
    notes.mkdir()

    # Create some test notes
    (notes / "note1.md").write_text("---\ntitle: Note 1\n---\nContent 1")
    (notes / "note2.md").write_text("---\ntitle: Note 2\n---\nContent 2")

    # Create nested notes
    (notes / "projects").mkdir()
    (notes / "projects" / "web.md").write_text("---\ntitle: Web Project\n---\nWeb content")
    (notes / "projects" / "api.md").write_text("---\ntitle: API Project\n---\nAPI content")

    return notes


@pytest.fixture
def empty_notes_dir(tmp_path: Path) -> Path:
    """Create an empty notes directory."""
    notes = tmp_path / "empty_notes"
    notes.mkdir()
    return notes


class TestExportNotes:
    """Tests for export_notes function."""

    def test_export_creates_archive(self, notes_dir: Path, tmp_path: Path) -> None:
        """Test that export creates a tar.gz archive."""
        output = tmp_path / "backup.tar.gz"
        result = export_notes(notes_dir, output)

        assert result.path.exists()
        assert result.path.suffix == ".gz"
        assert result.notes_count == 4

    def test_export_default_filename(self, notes_dir: Path, tmp_path: Path) -> None:
        """Test export with default timestamped filename."""
        import os

        os.chdir(tmp_path)
        result = export_notes(notes_dir)

        assert result.path.exists()
        assert "notes-backup-" in result.path.name
        assert result.path.suffix == ".gz"

    def test_export_archive_contents(self, notes_dir: Path, tmp_path: Path) -> None:
        """Test that archive contains correct files."""
        output = tmp_path / "backup.tar.gz"
        export_notes(notes_dir, output)

        with tarfile.open(output, "r:gz") as tar:
            names = tar.getnames()
            assert "note1.md" in names
            assert "note2.md" in names
            assert "projects/web.md" in names
            assert "projects/api.md" in names

    def test_export_empty_directory(self, empty_notes_dir: Path, tmp_path: Path) -> None:
        """Test export of empty notes directory."""
        output = tmp_path / "backup.tar.gz"
        result = export_notes(empty_notes_dir, output)

        assert result.path.exists()
        assert result.notes_count == 0

    def test_export_adds_extension(self, notes_dir: Path, tmp_path: Path) -> None:
        """Test that .tar.gz extension is added if missing."""
        output = tmp_path / "backup"
        result = export_notes(notes_dir, output)

        assert str(result.path).endswith(".tar.gz")


class TestImportNotes:
    """Tests for import_notes function."""

    def test_import_to_empty_directory(
        self, notes_dir: Path, empty_notes_dir: Path, tmp_path: Path
    ) -> None:
        """Test importing to an empty directory."""
        archive = tmp_path / "backup.tar.gz"
        export_notes(notes_dir, archive)

        result = import_notes(empty_notes_dir, archive)

        assert result.imported_count == 4
        assert result.skipped_count == 0
        assert not result.replaced
        assert (empty_notes_dir / "note1.md").exists()
        assert (empty_notes_dir / "projects" / "web.md").exists()

    def test_import_merge_skips_existing(
        self, notes_dir: Path, tmp_path: Path
    ) -> None:
        """Test that merge mode skips existing files."""
        archive = tmp_path / "backup.tar.gz"
        export_notes(notes_dir, archive)

        # Create a destination with one existing file
        dest = tmp_path / "dest"
        dest.mkdir()
        (dest / "note1.md").write_text("existing content")

        result = import_notes(dest, archive, replace=False)

        assert result.imported_count == 3
        assert result.skipped_count == 1
        # Original content should be preserved
        assert (dest / "note1.md").read_text() == "existing content"

    def test_import_replace_clears_existing(
        self, notes_dir: Path, tmp_path: Path
    ) -> None:
        """Test that replace mode clears existing notes."""
        archive = tmp_path / "backup.tar.gz"
        export_notes(notes_dir, archive)

        # Create a destination with different files
        dest = tmp_path / "dest"
        dest.mkdir()
        (dest / "old_note.md").write_text("old content")
        (dest / "note1.md").write_text("existing content")

        result = import_notes(dest, archive, replace=True)

        assert result.imported_count == 4
        assert result.skipped_count == 0
        assert result.replaced
        # Old note should be gone
        assert not (dest / "old_note.md").exists()
        # New content should be there
        assert "Content 1" in (dest / "note1.md").read_text()

    def test_import_nonexistent_archive(self, empty_notes_dir: Path) -> None:
        """Test error when archive doesn't exist."""
        with pytest.raises(FileNotFoundError):
            import_notes(empty_notes_dir, Path("nonexistent.tar.gz"))

    def test_import_preserves_directory_structure(
        self, notes_dir: Path, empty_notes_dir: Path, tmp_path: Path
    ) -> None:
        """Test that directory structure is preserved."""
        archive = tmp_path / "backup.tar.gz"
        export_notes(notes_dir, archive)

        import_notes(empty_notes_dir, archive)

        assert (empty_notes_dir / "projects").is_dir()
        assert (empty_notes_dir / "projects" / "web.md").exists()
        assert (empty_notes_dir / "projects" / "api.md").exists()


class TestRoundTrip:
    """Tests for export/import round-trip."""

    def test_round_trip_preserves_content(
        self, notes_dir: Path, empty_notes_dir: Path, tmp_path: Path
    ) -> None:
        """Test that export and import preserves note content."""
        archive = tmp_path / "backup.tar.gz"
        export_notes(notes_dir, archive)
        import_notes(empty_notes_dir, archive)

        # Check content is preserved
        original = (notes_dir / "note1.md").read_text()
        imported = (empty_notes_dir / "note1.md").read_text()
        assert original == imported

        original_nested = (notes_dir / "projects" / "web.md").read_text()
        imported_nested = (empty_notes_dir / "projects" / "web.md").read_text()
        assert original_nested == imported_nested


class TestClearNotes:
    """Tests for clear_notes function."""

    def test_clear_deletes_all_notes(self, notes_dir: Path) -> None:
        """Test that clear deletes all markdown files."""
        # Verify notes exist first
        assert len(list(notes_dir.rglob("*.md"))) == 4

        count = clear_notes(notes_dir)

        assert count == 4
        assert len(list(notes_dir.rglob("*.md"))) == 0

    def test_clear_removes_empty_directories(self, notes_dir: Path) -> None:
        """Test that clear removes empty subdirectories."""
        assert (notes_dir / "projects").is_dir()

        clear_notes(notes_dir)

        assert not (notes_dir / "projects").exists()

    def test_clear_empty_directory(self, empty_notes_dir: Path) -> None:
        """Test clearing an empty directory returns 0."""
        count = clear_notes(empty_notes_dir)

        assert count == 0

    def test_clear_preserves_notes_directory(self, notes_dir: Path) -> None:
        """Test that the notes directory itself is preserved."""
        clear_notes(notes_dir)

        assert notes_dir.exists()
        assert notes_dir.is_dir()
