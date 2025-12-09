"""Filesystem-based storage backend."""

from pathlib import Path

from notes.models.note import Note
from notes.storage.base import StorageBackend


class FilesystemStorage(StorageBackend):
    """Store notes as markdown files on disk."""

    def __init__(self, base_dir: Path) -> None:
        self.base_dir = base_dir
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _path_to_file(self, path: str) -> Path:
        """Convert note path to filesystem path."""
        return self.base_dir / f"{path}.md"

    def save(self, note: Note) -> None:
        """Save a note to disk."""
        file_path = self._path_to_file(note.path)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(note.to_markdown())

    def load(self, path: str) -> Note | None:
        """Load a note from disk."""
        file_path = self._path_to_file(path)
        if not file_path.exists():
            return None
        content = file_path.read_text()
        return Note.from_markdown(path, content)

    def delete(self, path: str) -> bool:
        """Delete a note from disk."""
        file_path = self._path_to_file(path)
        if file_path.exists():
            file_path.unlink()
            return True
        return False

    def list_all(self) -> list[str]:
        """List all note paths."""
        paths = []
        for file_path in self.base_dir.rglob("*.md"):
            rel_path = file_path.relative_to(self.base_dir)
            path = str(rel_path.with_suffix(""))
            paths.append(path)
        return sorted(paths)
