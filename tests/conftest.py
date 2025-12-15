"""Pytest configuration and fixtures."""

import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from notes.config import Config
from notes.search import SearchIndex
from notes.storage import FilesystemStorage


@pytest.fixture
def temp_dir():
    """Provide a temporary directory for tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def storage(temp_dir: Path) -> FilesystemStorage:
    """Provide a filesystem storage instance."""
    return FilesystemStorage(temp_dir / "notes")


@pytest.fixture
def search_index(temp_dir: Path) -> SearchIndex:
    """Provide a search index instance."""
    return SearchIndex(temp_dir / "index")


@pytest.fixture
def config(temp_dir: Path) -> Config:
    """Provide a test configuration."""
    return Config(
        notes_dir=temp_dir / "notes",
        index_dir=temp_dir / "index",
    )


@pytest.fixture
def mock_config(config: Config):
    """Patch _get_service to return NoteService with test configuration for MCP tool tests."""
    from notes.services import NoteService

    def make_test_service() -> NoteService:
        return NoteService(config)

    with (
        patch("notes.tools.notes._get_service", make_test_service),
        patch("notes.tools.search._get_service", make_test_service),
        patch("notes.tools.tags._get_service", make_test_service),
        patch("notes.tools.links._get_service", make_test_service),
        patch("notes.tools.history._get_service", make_test_service),
        patch("notes.server._current_author", "test-author"),
    ):
        yield config
