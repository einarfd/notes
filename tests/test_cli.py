"""Tests for CLI admin tools."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from notes.cli import clear_all, export_backup, import_backup, main, rebuild_indexes


class TestRebuildIndexes:
    """Tests for the rebuild_indexes function."""

    def test_rebuild_indexes_output(self, capsys: pytest.CaptureFixture[str]):
        """Test that rebuild_indexes prints progress."""
        with patch("notes.cli.NoteService") as mock_service_class:
            mock_service = MagicMock()
            mock_service.rebuild_indexes.return_value = MagicMock(notes_processed=5)
            mock_service_class.return_value = mock_service

            rebuild_indexes()

            captured = capsys.readouterr()
            assert "Rebuilding indexes..." in captured.out
            assert "Done! Processed 5 notes." in captured.out


class TestExportBackup:
    """Tests for the export_backup function."""

    def test_export_backup_default_output(
        self, capsys: pytest.CaptureFixture[str], tmp_path: Path
    ):
        """Test export with default output path."""
        with patch("notes.cli.get_config") as mock_config, patch(
            "notes.cli.export_notes"
        ) as mock_export:
            mock_config.return_value.notes_dir = tmp_path
            mock_export.return_value = MagicMock(
                notes_count=10, path=tmp_path / "notes-backup.tar.gz"
            )

            export_backup(None)

            mock_export.assert_called_once_with(tmp_path, None)
            captured = capsys.readouterr()
            assert "Exporting notes..." in captured.out
            assert "Done! Exported 10 notes" in captured.out

    def test_export_backup_custom_output(
        self, capsys: pytest.CaptureFixture[str], tmp_path: Path
    ):
        """Test export with custom output path."""
        output = str(tmp_path / "custom.tar.gz")
        with patch("notes.cli.get_config") as mock_config, patch(
            "notes.cli.export_notes"
        ) as mock_export:
            mock_config.return_value.notes_dir = tmp_path
            mock_export.return_value = MagicMock(notes_count=5, path=Path(output))

            export_backup(output)

            mock_export.assert_called_once_with(tmp_path, Path(output))
            captured = capsys.readouterr()
            assert "Exported 5 notes" in captured.out


class TestImportBackup:
    """Tests for the import_backup function."""

    def test_import_backup_merge(
        self, capsys: pytest.CaptureFixture[str], tmp_path: Path
    ):
        """Test import with merge mode."""
        archive = str(tmp_path / "backup.tar.gz")
        with (
            patch("notes.cli.get_config") as mock_config,
            patch("notes.cli.import_notes") as mock_import,
            patch("notes.cli.NoteService") as mock_service_class,
        ):
            mock_config.return_value.notes_dir = tmp_path
            mock_import.return_value = MagicMock(
                imported_count=8, skipped_count=2, replaced=False
            )
            mock_service = MagicMock()
            mock_service.rebuild_indexes.return_value = MagicMock(notes_processed=8)
            mock_service_class.return_value = mock_service

            import_backup(archive, replace=False)

            mock_import.assert_called_once_with(tmp_path, Path(archive), replace=False)
            captured = capsys.readouterr()
            assert "Importing notes (merging" in captured.out
            assert "Imported 8 notes" in captured.out
            assert "Skipped 2 existing notes" in captured.out
            assert "Rebuilding indexes..." in captured.out
            assert "Indexed 8 notes" in captured.out

    def test_import_backup_replace(
        self, capsys: pytest.CaptureFixture[str], tmp_path: Path
    ):
        """Test import with replace mode."""
        archive = str(tmp_path / "backup.tar.gz")
        with (
            patch("notes.cli.get_config") as mock_config,
            patch("notes.cli.import_notes") as mock_import,
            patch("notes.cli.NoteService") as mock_service_class,
        ):
            mock_config.return_value.notes_dir = tmp_path
            mock_import.return_value = MagicMock(
                imported_count=10, skipped_count=0, replaced=True
            )
            mock_service = MagicMock()
            mock_service.rebuild_indexes.return_value = MagicMock(notes_processed=10)
            mock_service_class.return_value = mock_service

            import_backup(archive, replace=True)

            mock_import.assert_called_once_with(tmp_path, Path(archive), replace=True)
            captured = capsys.readouterr()
            assert "Importing notes (replacing" in captured.out
            assert "Imported 10 notes" in captured.out
            assert "Skipped" not in captured.out

    def test_import_backup_no_skipped(
        self, capsys: pytest.CaptureFixture[str], tmp_path: Path
    ):
        """Test that skipped message is not shown when no files skipped."""
        archive = str(tmp_path / "backup.tar.gz")
        with (
            patch("notes.cli.get_config") as mock_config,
            patch("notes.cli.import_notes") as mock_import,
            patch("notes.cli.NoteService") as mock_service_class,
        ):
            mock_config.return_value.notes_dir = tmp_path
            mock_import.return_value = MagicMock(
                imported_count=5, skipped_count=0, replaced=False
            )
            mock_service = MagicMock()
            mock_service.rebuild_indexes.return_value = MagicMock(notes_processed=5)
            mock_service_class.return_value = mock_service

            import_backup(archive, replace=False)

            captured = capsys.readouterr()
            assert "Skipped" not in captured.out


class TestClearAll:
    """Tests for the clear_all function."""

    def test_clear_all_with_force(
        self, capsys: pytest.CaptureFixture[str], tmp_path: Path
    ):
        """Test clear with --force skips confirmation."""
        with (
            patch("notes.cli.get_config") as mock_config,
            patch("notes.cli.clear_notes") as mock_clear,
            patch("notes.cli.NoteService") as mock_service_class,
        ):
            mock_config.return_value.notes_dir = tmp_path
            mock_clear.return_value = 5
            mock_service = MagicMock()
            mock_service_class.return_value = mock_service

            clear_all(force=True)

            mock_clear.assert_called_once_with(tmp_path)
            captured = capsys.readouterr()
            assert "Clearing all notes..." in captured.out
            assert "Deleted 5 notes" in captured.out
            assert "Done!" in captured.out

    def test_clear_all_without_force_confirmed(
        self, capsys: pytest.CaptureFixture[str], tmp_path: Path
    ):
        """Test clear without --force prompts and proceeds on 'yes'."""
        with (
            patch("notes.cli.get_config") as mock_config,
            patch("notes.cli.clear_notes") as mock_clear,
            patch("notes.cli.NoteService") as mock_service_class,
            patch("builtins.input", return_value="yes"),
        ):
            mock_config.return_value.notes_dir = tmp_path
            mock_clear.return_value = 3
            mock_service = MagicMock()
            mock_service_class.return_value = mock_service

            clear_all(force=False)

            mock_clear.assert_called_once()
            captured = capsys.readouterr()
            assert "WARNING" in captured.out
            assert "Deleted 3 notes" in captured.out

    def test_clear_all_without_force_aborted(
        self, capsys: pytest.CaptureFixture[str], tmp_path: Path
    ):
        """Test clear without --force aborts on non-'yes' input."""
        with (
            patch("notes.cli.get_config") as mock_config,
            patch("notes.cli.clear_notes") as mock_clear,
            patch("builtins.input", return_value="no"),
        ):
            mock_config.return_value.notes_dir = tmp_path

            clear_all(force=False)

            mock_clear.assert_not_called()
            captured = capsys.readouterr()
            assert "Aborted" in captured.out


class TestMain:
    """Tests for the main CLI entry point."""

    def test_rebuild_command(self):
        """Test that rebuild command calls rebuild_indexes."""
        with (
            patch("notes.cli.rebuild_indexes") as mock_rebuild,
            patch("sys.argv", ["notes-admin", "rebuild"]),
        ):
            main()
            mock_rebuild.assert_called_once()

    def test_export_command_default(self):
        """Test that export command calls export_backup with no output."""
        with (
            patch("notes.cli.export_backup") as mock_export,
            patch("sys.argv", ["notes-admin", "export"]),
        ):
            main()
            mock_export.assert_called_once_with(None)

    def test_export_command_with_output(self):
        """Test that export command calls export_backup with output path."""
        with (
            patch("notes.cli.export_backup") as mock_export,
            patch("sys.argv", ["notes-admin", "export", "my-backup.tar.gz"]),
        ):
            main()
            mock_export.assert_called_once_with("my-backup.tar.gz")

    def test_import_command(self):
        """Test that import command calls import_backup."""
        with (
            patch("notes.cli.import_backup") as mock_import,
            patch("sys.argv", ["notes-admin", "import", "backup.tar.gz"]),
        ):
            main()
            mock_import.assert_called_once_with("backup.tar.gz", False)

    def test_import_command_with_replace(self):
        """Test that import --replace calls import_backup with replace=True."""
        with (
            patch("notes.cli.import_backup") as mock_import,
            patch("sys.argv", ["notes-admin", "import", "backup.tar.gz", "--replace"]),
        ):
            main()
            mock_import.assert_called_once_with("backup.tar.gz", True)

    def test_import_command_requires_archive(self):
        """Test that import command requires archive argument."""
        with patch("sys.argv", ["notes-admin", "import"]), pytest.raises(SystemExit):
            main()

    def test_clear_command(self):
        """Test that clear command calls clear_all without force."""
        with (
            patch("notes.cli.clear_all") as mock_clear,
            patch("sys.argv", ["notes-admin", "clear"]),
        ):
            main()
            mock_clear.assert_called_once_with(False)

    def test_clear_command_with_force(self):
        """Test that clear --force calls clear_all with force=True."""
        with (
            patch("notes.cli.clear_all") as mock_clear,
            patch("sys.argv", ["notes-admin", "clear", "--force"]),
        ):
            main()
            mock_clear.assert_called_once_with(True)

    def test_no_command_shows_error(self):
        """Test that running without command shows error."""
        with patch("sys.argv", ["notes-admin"]), pytest.raises(SystemExit):
            main()

    def test_invalid_command_shows_error(self):
        """Test that invalid command shows error."""
        with patch("sys.argv", ["notes-admin", "invalid"]), pytest.raises(SystemExit):
            main()


