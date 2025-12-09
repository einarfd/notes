"""Storage backends for notes."""

from notes.storage.base import StorageBackend
from notes.storage.filesystem import FilesystemStorage

__all__ = ["StorageBackend", "FilesystemStorage"]
