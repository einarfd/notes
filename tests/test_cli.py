"""Tests for CLI admin tools."""

import subprocess
import sys
from unittest.mock import MagicMock, patch

import pytest

from notes.cli import main, rebuild_indexes
from notes.config import Config


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

    def test_no_command_shows_error(self):
        """Test that running without command shows error."""
        with patch("sys.argv", ["notes-admin"]), pytest.raises(SystemExit):
            main()

    def test_invalid_command_shows_error(self):
        """Test that invalid command shows error."""
        with patch("sys.argv", ["notes-admin", "invalid"]), pytest.raises(SystemExit):
            main()


class TestCLIIntegration:
    """Integration tests for the CLI."""

    def test_cli_rebuild_command(self, config: Config):
        """Test running notes-admin rebuild as a subprocess."""
        # Run the CLI command
        result = subprocess.run(
            [sys.executable, "-m", "notes.cli", "rebuild"],
            capture_output=True,
            text=True,
            env={"PYTHONPATH": "src"},
        )

        assert result.returncode == 0
        assert "Rebuilding indexes..." in result.stdout
        assert "Done!" in result.stdout
