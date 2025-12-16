"""Configuration management."""

import tomllib
from pathlib import Path
from typing import Any, Literal

import tomli_w
from pydantic import BaseModel


class ServerConfig(BaseModel):
    """Server configuration."""

    host: str = "127.0.0.1"
    port: int = 8080
    transport: Literal["stdio", "http", "sse"] = "stdio"


class AuthConfig(BaseModel):
    """Authentication configuration."""

    keys: dict[str, str] = {}  # name -> token


class WebConfig(BaseModel):
    """Web UI configuration."""

    username: str | None = None
    password: str | None = None


class Config(BaseModel):
    """Application configuration."""

    notes_dir: Path = Path.home() / ".local" / "botnotes" / "notes"
    index_dir: Path = Path.home() / ".local" / "botnotes" / "index"
    server: ServerConfig = ServerConfig()
    auth: AuthConfig = AuthConfig()
    web: WebConfig = WebConfig()

    def ensure_dirs(self) -> None:
        """Create data directories if they don't exist."""
        self.notes_dir.mkdir(parents=True, exist_ok=True)
        self.index_dir.mkdir(parents=True, exist_ok=True)

    def validate_for_http(self) -> None:
        """Validate config for HTTP mode. Raises if auth not configured."""
        if not self.auth.keys:
            raise ValueError(
                "HTTP mode requires authentication. "
                "Add API keys to [auth.keys] in config.toml"
            )

    @classmethod
    def load(cls, path: Path | None = None) -> Config:
        """Load config from TOML file.

        Args:
            path: Path to config file. Defaults to ~/.local/botnotes/config.toml

        Returns:
            Config loaded from file, or default config if file doesn't exist.
        """
        path = path or Path.home() / ".local" / "botnotes" / "config.toml"
        if path.exists():
            with open(path, "rb") as f:
                data = tomllib.load(f)
            return cls.model_validate(data)
        return cls()

    def save(self, path: Path | None = None) -> None:
        """Save config to TOML file.

        Args:
            path: Path to config file. Defaults to ~/.local/botnotes/config.toml
        """
        path = path or Path.home() / ".local" / "botnotes" / "config.toml"
        path.parent.mkdir(parents=True, exist_ok=True)

        # Build TOML-serializable dict, excluding defaults
        data: dict[str, Any] = {}

        # Only include non-default server settings
        server_data: dict[str, Any] = {}
        default_server = ServerConfig()
        if self.server.host != default_server.host:
            server_data["host"] = self.server.host
        if self.server.port != default_server.port:
            server_data["port"] = self.server.port
        if self.server.transport != default_server.transport:
            server_data["transport"] = self.server.transport
        if server_data:
            data["server"] = server_data

        # Include auth keys if any
        if self.auth.keys:
            data["auth"] = {"keys": self.auth.keys}

        # Include web auth if configured
        if self.web.username and self.web.password:
            data["web"] = {
                "username": self.web.username,
                "password": self.web.password,
            }

        with open(path, "wb") as f:
            tomli_w.dump(data, f)


def get_config() -> Config:
    """Get the application configuration."""
    return Config.load()
