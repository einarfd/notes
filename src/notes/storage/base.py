"""Abstract storage interface."""

from abc import ABC, abstractmethod

from notes.models.note import Note


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
