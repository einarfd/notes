"""Abstract storage interface."""

from abc import ABC, abstractmethod

from botnotes.models.note import Note


class StorageBackend(ABC):
    """Abstract base class for storage backends."""

    @abstractmethod
    def save(self, note: Note) -> None:
        """Save a note."""
        ...

    @abstractmethod
    def load(self, path: str) -> Note | None:
        """Load a note by path."""
        ...

    @abstractmethod
    def delete(self, path: str) -> bool:
        """Delete a note. Returns True if deleted."""
        ...

    @abstractmethod
    def list_all(self) -> list[str]:
        """List all note paths."""
        ...

    @abstractmethod
    def list_by_prefix(self, prefix: str) -> dict[str, list[str]]:
        """List notes and subfolders within a folder.

        Args:
            prefix: Folder path. Empty string = top-level only.

        Returns:
            Dict with 'notes' (direct notes) and 'subfolders' (immediate subfolders).
        """
        ...
