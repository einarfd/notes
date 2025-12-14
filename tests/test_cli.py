"""Tests for CLI admin tools."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from notes.cli import (
    auth_add,
    auth_list,
    auth_remove,
    clear_all,
    export_backup,
    import_backup,
    main,
    rebuild_indexes,
    web_clear_password,
    web_set_password,
)


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

    def test_auth_list_command(self):
        """Test that auth list command calls auth_list."""
        with (
            patch("notes.cli.auth_list") as mock_auth_list,
            patch("sys.argv", ["notes-admin", "auth", "list"]),
        ):
            main()
            mock_auth_list.assert_called_once()

    def test_auth_add_command(self):
        """Test that auth add command calls auth_add with name."""
        with (
            patch("notes.cli.auth_add") as mock_auth_add,
            patch("sys.argv", ["notes-admin", "auth", "add", "my-key"]),
        ):
            main()
            mock_auth_add.assert_called_once_with("my-key")

    def test_auth_remove_command(self):
        """Test that auth remove command calls auth_remove with name."""
        with (
            patch("notes.cli.auth_remove") as mock_auth_remove,
            patch("sys.argv", ["notes-admin", "auth", "remove", "my-key"]),
        ):
            main()
            mock_auth_remove.assert_called_once_with("my-key")

    def test_auth_add_requires_name(self):
        """Test that auth add command requires name argument."""
        with patch("sys.argv", ["notes-admin", "auth", "add"]), pytest.raises(SystemExit):
            main()

    def test_auth_remove_requires_name(self):
        """Test that auth remove command requires name argument."""
        with patch("sys.argv", ["notes-admin", "auth", "remove"]), pytest.raises(SystemExit):
            main()


class TestAuthList:
    """Tests for the auth_list function."""

    def test_auth_list_empty(self, capsys: pytest.CaptureFixture[str]):
        """Test auth_list with no keys configured."""
        with patch("notes.cli.Config.load") as mock_load:
            mock_config = MagicMock()
            mock_config.auth.keys = {}
            mock_load.return_value = mock_config

            auth_list()

            captured = capsys.readouterr()
            assert "No API keys configured" in captured.out
            assert "notes-admin auth add" in captured.out

    def test_auth_list_with_keys(self, capsys: pytest.CaptureFixture[str]):
        """Test auth_list shows key names."""
        with patch("notes.cli.Config.load") as mock_load:
            mock_config = MagicMock()
            mock_config.auth.keys = {"key-a": "token-a", "key-b": "token-b"}
            mock_load.return_value = mock_config

            auth_list()

            captured = capsys.readouterr()
            assert "Configured API keys" in captured.out
            assert "key-a" in captured.out
            assert "key-b" in captured.out
            # Should not show tokens
            assert "token-a" not in captured.out
            assert "token-b" not in captured.out


class TestAuthAdd:
    """Tests for the auth_add function."""

    def test_auth_add_creates_key(self, capsys: pytest.CaptureFixture[str]):
        """Test auth_add creates a new key and shows token."""
        with patch("notes.cli.Config.load") as mock_load:
            mock_config = MagicMock()
            mock_config.auth.keys = {}
            mock_load.return_value = mock_config

            auth_add("my-agent")

            # Key should be added
            assert "my-agent" in mock_config.auth.keys
            # Config should be saved
            mock_config.save.assert_called_once()

            captured = capsys.readouterr()
            assert "Added API key 'my-agent'" in captured.out
            assert "Token:" in captured.out

    def test_auth_add_duplicate_fails(self, capsys: pytest.CaptureFixture[str]):
        """Test auth_add fails on duplicate name."""
        with patch("notes.cli.Config.load") as mock_load:
            mock_config = MagicMock()
            mock_config.auth.keys = {"existing-key": "some-token"}
            mock_load.return_value = mock_config

            auth_add("existing-key")

            # Config should not be saved
            mock_config.save.assert_not_called()

            captured = capsys.readouterr()
            assert "Error" in captured.out
            assert "already exists" in captured.out


class TestAuthRemove:
    """Tests for the auth_remove function."""

    def test_auth_remove_key(self, capsys: pytest.CaptureFixture[str]):
        """Test auth_remove removes existing key."""
        with patch("notes.cli.Config.load") as mock_load:
            mock_config = MagicMock()
            mock_config.auth.keys = {"my-key": "my-token"}
            mock_load.return_value = mock_config

            auth_remove("my-key")

            # Key should be removed
            assert "my-key" not in mock_config.auth.keys
            # Config should be saved
            mock_config.save.assert_called_once()

            captured = capsys.readouterr()
            assert "Removed API key 'my-key'" in captured.out

    def test_auth_remove_nonexistent(self, capsys: pytest.CaptureFixture[str]):
        """Test auth_remove fails on nonexistent key."""
        with patch("notes.cli.Config.load") as mock_load:
            mock_config = MagicMock()
            mock_config.auth.keys = {}
            mock_load.return_value = mock_config

            auth_remove("missing-key")

            # Config should not be saved
            mock_config.save.assert_not_called()

            captured = capsys.readouterr()
            assert "Error" in captured.out
            assert "not found" in captured.out


class TestWebSetPassword:
    """Tests for the web_set_password function."""

    def test_web_set_password_with_username(self, capsys: pytest.CaptureFixture[str]):
        """Test setting web password with username provided."""
        with (
            patch("notes.cli.Config.load") as mock_load,
            patch("getpass.getpass", return_value="mypassword"),
        ):
            mock_config = MagicMock()
            mock_config.web.username = None
            mock_config.web.password = None
            mock_load.return_value = mock_config

            web_set_password("admin")

            assert mock_config.web.username == "admin"
            assert mock_config.web.password == "mypassword"
            mock_config.save.assert_called_once()

            captured = capsys.readouterr()
            assert "Web auth configured for user 'admin'" in captured.out

    def test_web_set_password_prompts_for_username(self, capsys: pytest.CaptureFixture[str]):
        """Test setting web password prompts for username when not provided."""
        with (
            patch("notes.cli.Config.load") as mock_load,
            patch("builtins.input", return_value="myuser"),
            patch("getpass.getpass", return_value="mypassword"),
        ):
            mock_config = MagicMock()
            mock_config.web.username = None
            mock_config.web.password = None
            mock_load.return_value = mock_config

            web_set_password(None)

            assert mock_config.web.username == "myuser"
            assert mock_config.web.password == "mypassword"
            mock_config.save.assert_called_once()

    def test_web_set_password_empty_username_rejected(self, capsys: pytest.CaptureFixture[str]):
        """Test empty username is rejected."""
        with (
            patch("notes.cli.Config.load") as mock_load,
            patch("builtins.input", return_value=""),
        ):
            mock_config = MagicMock()
            mock_load.return_value = mock_config

            web_set_password(None)

            mock_config.save.assert_not_called()
            captured = capsys.readouterr()
            assert "Error" in captured.out
            assert "Username cannot be empty" in captured.out

    def test_web_set_password_empty_password_rejected(self, capsys: pytest.CaptureFixture[str]):
        """Test empty password is rejected."""
        with (
            patch("notes.cli.Config.load") as mock_load,
            patch("getpass.getpass", return_value=""),
        ):
            mock_config = MagicMock()
            mock_load.return_value = mock_config

            web_set_password("admin")

            mock_config.save.assert_not_called()
            captured = capsys.readouterr()
            assert "Error" in captured.out
            assert "Password cannot be empty" in captured.out


class TestWebClearPassword:
    """Tests for the web_clear_password function."""

    def test_web_clear_password(self, capsys: pytest.CaptureFixture[str]):
        """Test clearing web password."""
        with patch("notes.cli.Config.load") as mock_load:
            mock_config = MagicMock()
            mock_config.web.username = "admin"
            mock_config.web.password = "secret"
            mock_load.return_value = mock_config

            web_clear_password()

            assert mock_config.web.username is None
            assert mock_config.web.password is None
            mock_config.save.assert_called_once()

            captured = capsys.readouterr()
            assert "Web auth disabled" in captured.out


class TestMainWebCommands:
    """Tests for web commands via main()."""

    def test_web_set_password_command(self):
        """Test that web set-password command calls web_set_password."""
        with (
            patch("notes.cli.web_set_password") as mock_set_pw,
            patch("sys.argv", ["notes-admin", "web", "set-password", "myuser"]),
        ):
            main()
            mock_set_pw.assert_called_once_with("myuser")

    def test_web_set_password_command_no_username(self):
        """Test that web set-password without username passes None."""
        with (
            patch("notes.cli.web_set_password") as mock_set_pw,
            patch("sys.argv", ["notes-admin", "web", "set-password"]),
        ):
            main()
            mock_set_pw.assert_called_once_with(None)

    def test_web_clear_password_command(self):
        """Test that web clear-password command calls web_clear_password."""
        with (
            patch("notes.cli.web_clear_password") as mock_clear_pw,
            patch("sys.argv", ["notes-admin", "web", "clear-password"]),
        ):
            main()
            mock_clear_pw.assert_called_once()

