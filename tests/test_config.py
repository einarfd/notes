"""Tests for configuration module."""

from pathlib import Path

import pytest

from botnotes.config import AuthConfig, Config, ServerConfig


class TestServerConfig:
    """Tests for ServerConfig."""

    def test_default_values(self) -> None:
        """Default values are set correctly."""
        config = ServerConfig()
        assert config.host == "127.0.0.1"
        assert config.port == 8080
        assert config.transport == "stdio"

    def test_custom_values(self) -> None:
        """Custom values are accepted."""
        config = ServerConfig(host="0.0.0.0", port=9000, transport="http")
        assert config.host == "0.0.0.0"
        assert config.port == 9000
        assert config.transport == "http"

    def test_invalid_transport(self) -> None:
        """Invalid transport raises error."""
        with pytest.raises(ValueError):
            ServerConfig(transport="invalid")  # type: ignore[arg-type]


class TestAuthConfig:
    """Tests for AuthConfig."""

    def test_default_empty_keys(self) -> None:
        """Default keys dict is empty."""
        config = AuthConfig()
        assert config.keys == {}

    def test_custom_keys(self) -> None:
        """Custom keys are accepted."""
        config = AuthConfig(keys={"test": "token123"})
        assert config.keys == {"test": "token123"}


class TestConfig:
    """Tests for Config."""

    def test_default_paths(self) -> None:
        """Default paths point to ~/.local/notes/."""
        config = Config()
        assert "notes" in str(config.notes_dir)
        assert "index" in str(config.index_dir)

    def test_nested_configs_have_defaults(self) -> None:
        """Nested ServerConfig and AuthConfig have defaults."""
        config = Config()
        assert config.server.transport == "stdio"
        assert config.auth.keys == {}

    def test_validate_for_http_fails_without_keys(self) -> None:
        """validate_for_http raises without API keys."""
        config = Config()
        with pytest.raises(ValueError, match="requires authentication"):
            config.validate_for_http()

    def test_validate_for_http_passes_with_keys(self) -> None:
        """validate_for_http passes with API keys."""
        config = Config(auth=AuthConfig(keys={"test": "token"}))
        config.validate_for_http()  # Should not raise

    def test_load_from_nonexistent_file(self, tmp_path: Path) -> None:
        """Loading from nonexistent file returns defaults."""
        config = Config.load(tmp_path / "nonexistent.toml")
        assert config.server.transport == "stdio"

    def test_load_from_toml_file(self, tmp_path: Path) -> None:
        """Loading from TOML file works correctly."""
        config_file = tmp_path / "config.toml"
        config_file.write_text("""
[server]
host = "0.0.0.0"
port = 9000
transport = "http"

[auth.keys]
test-client = "secret-token"
""")

        config = Config.load(config_file)
        assert config.server.host == "0.0.0.0"
        assert config.server.port == 9000
        assert config.server.transport == "http"
        assert config.auth.keys == {"test-client": "secret-token"}

    def test_load_partial_config(self, tmp_path: Path) -> None:
        """Loading partial config uses defaults for missing values."""
        config_file = tmp_path / "config.toml"
        config_file.write_text("""
[server]
port = 3000
""")

        config = Config.load(config_file)
        # Custom value
        assert config.server.port == 3000
        # Defaults
        assert config.server.host == "127.0.0.1"
        assert config.server.transport == "stdio"
        assert config.auth.keys == {}

    def test_ensure_dirs_creates_directories(self, tmp_path: Path) -> None:
        """ensure_dirs creates data directories."""
        config = Config(
            notes_dir=tmp_path / "notes",
            index_dir=tmp_path / "index",
        )
        assert not config.notes_dir.exists()
        assert not config.index_dir.exists()

        config.ensure_dirs()

        assert config.notes_dir.exists()
        assert config.index_dir.exists()
