"""Configuration management."""

from pathlib import Path

from pydantic import BaseModel


class Config(BaseModel):
    """Application configuration."""

    notes_dir: Path = Path.home() / ".local" / "notes" / "notes"
    index_dir: Path = Path.home() / ".local" / "notes" / "index"

    def ensure_dirs(self) -> None:
        """Create data directories if they don't exist."""
        self.notes_dir.mkdir(parents=True, exist_ok=True)
        self.index_dir.mkdir(parents=True, exist_ok=True)


def get_config() -> Config:
    """Get the application configuration."""
    return Config()
