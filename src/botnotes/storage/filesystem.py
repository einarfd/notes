"""Filesystem-based storage backend."""

from pathlib import Path

from botnotes.models.note import Note
from botnotes.storage.base import StorageBackend


class FilesystemStorage(StorageBackend):
    """Store notes as markdown files on disk."""

    def __init__(self, base_dir: Path) -> None:
        self.base_dir = base_dir
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _sanitize_path(self, path: str) -> str:
        """Sanitize path to prevent directory traversal.

        Raises:
            ValueError: If path is empty or attempts directory traversal.
        """
        clean = path.strip().lstrip("/")
        if not clean:
            raise ValueError("Path cannot be empty")

        # Resolve and verify within base_dir
        resolved = (self.base_dir / f"{clean}.md").resolve()
        if not resolved.is_relative_to(self.base_dir.resolve()):
            raise ValueError(f"Invalid path: {path}")

        return clean

    def _path_to_file(self, path: str) -> Path:
        """Convert note path to filesystem path."""
        clean = self._sanitize_path(path)
        return self.base_dir / f"{clean}.md"

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

    def list_by_prefix(self, prefix: str) -> dict[str, list[str]]:
        """List notes and subfolders within a folder.

        Args:
            prefix: Folder path. Empty string = top-level only.

        Returns:
            Dict with 'notes' (direct notes) and 'subfolders' (immediate subfolders).
        """
        prefix = prefix.strip().strip("/")
        paths = self.list_all()

        notes = []
        subfolders_set: set[str] = set()

        if not prefix:
            # Top-level
            for p in paths:
                if "/" not in p:
                    notes.append(p)
                else:
                    subfolders_set.add(p.split("/")[0])
        else:
            prefix_slash = prefix + "/"
            for p in paths:
                if p.startswith(prefix_slash):
                    remainder = p[len(prefix_slash):]
                    if "/" not in remainder:
                        notes.append(p)
                    else:
                        subfolders_set.add(prefix_slash + remainder.split("/")[0])
            # Also include note at exactly the prefix path (e.g., "projects" note)
            if prefix in paths:
                notes.append(prefix)

        return {"notes": sorted(notes), "subfolders": sorted(subfolders_set)}
