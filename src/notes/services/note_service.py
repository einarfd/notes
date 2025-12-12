"""Note service - business logic layer."""

from dataclasses import dataclass, field
from datetime import datetime

from notes.config import Config, get_config
from notes.links import BacklinkInfo, BacklinksIndex, extract_links
from notes.models import Note
from notes.search import SearchIndex
from notes.storage import FilesystemStorage


@dataclass
class DeleteResult:
    """Result of a delete operation."""

    deleted: bool
    backlinks_warning: list[BacklinkInfo] = field(default_factory=list)


class NoteService:
    """Service layer for note operations.

    Provides a unified interface for note CRUD operations, search, and tag management.
    Can be used by both MCP tools and web API.
    """

    def __init__(self, config: Config | None = None) -> None:
        """Initialize the service.

        Args:
            config: Configuration to use. If None, uses default from get_config().
        """
        self._config = config or get_config()
        self._config.ensure_dirs()
        self._storage: FilesystemStorage | None = None
        self._index: SearchIndex | None = None
        self._backlinks: BacklinksIndex | None = None

    @property
    def storage(self) -> FilesystemStorage:
        """Get the storage backend (lazily initialized)."""
        if self._storage is None:
            self._storage = FilesystemStorage(self._config.notes_dir)
        return self._storage

    @property
    def index(self) -> SearchIndex:
        """Get the search index (lazily initialized)."""
        if self._index is None:
            self._index = SearchIndex(self._config.index_dir)
        return self._index

    @property
    def backlinks(self) -> BacklinksIndex:
        """Get the backlinks index (lazily initialized)."""
        if self._backlinks is None:
            self._backlinks = BacklinksIndex(self._config.index_dir / "backlinks.json")
        return self._backlinks

    def create_note(
        self,
        path: str,
        title: str,
        content: str,
        tags: list[str] | None = None,
    ) -> Note:
        """Create a new note.

        Args:
            path: The path/identifier for the note
            title: The title of the note
            content: The markdown content of the note
            tags: Optional list of tags

        Returns:
            The created Note object
        """
        note = Note(
            path=path,
            title=title,
            content=content,
            tags=tags or [],
        )
        self.storage.save(note)
        self.index.index_note(note)

        # Index wiki links
        links = extract_links(content)
        self.backlinks.update_note_links(path, links)

        return note

    def read_note(self, path: str) -> Note | None:
        """Read a note by its path.

        Args:
            path: The path/identifier of the note

        Returns:
            The Note object, or None if not found
        """
        return self.storage.load(path)

    def update_note(
        self,
        path: str,
        title: str | None = None,
        content: str | None = None,
        tags: list[str] | None = None,
    ) -> Note | None:
        """Update an existing note.

        Args:
            path: The path/identifier of the note
            title: New title (optional)
            content: New content (optional)
            tags: New tags (optional)

        Returns:
            The updated Note object, or None if not found
        """
        note = self.storage.load(path)
        if note is None:
            return None

        if title is not None:
            note.title = title
        if content is not None:
            note.content = content
        if tags is not None:
            note.tags = tags

        note.updated_at = datetime.now()

        self.storage.save(note)
        self.index.index_note(note)

        # Update wiki links index if content changed
        if content is not None:
            links = extract_links(note.content)
            self.backlinks.update_note_links(path, links)

        return note

    def delete_note(self, path: str) -> DeleteResult:
        """Delete a note.

        Args:
            path: The path/identifier of the note

        Returns:
            DeleteResult with deleted status and backlink warnings
        """
        # Get backlinks before deletion to warn about broken links
        backlinks_warning = self.backlinks.get_backlinks(path)

        if self.storage.delete(path):
            self.index.remove_note(path)
            self.backlinks.remove_note(path)
            return DeleteResult(deleted=True, backlinks_warning=backlinks_warning)
        return DeleteResult(deleted=False)

    def list_notes(self) -> list[str]:
        """List all note paths.

        Returns:
            List of note paths
        """
        return self.storage.list_all()

    def list_notes_in_folder(self, folder: str = "") -> dict[str, list[str]]:
        """List notes and subfolders in a specific folder.

        Args:
            folder: Folder path. Empty string = top-level only.

        Returns:
            Dict with 'notes' (direct notes) and 'subfolders' (immediate subfolders).
        """
        return self.storage.list_by_prefix(folder)

    def search_notes(self, query: str, limit: int = 10) -> list[dict[str, str]]:
        """Search for notes.

        Args:
            query: The search query
            limit: Maximum number of results

        Returns:
            List of search results with path, title, and score
        """
        return self.index.search(query, limit=limit)

    def list_tags(self) -> dict[str, int]:
        """List all tags with their counts.

        Returns:
            Dictionary mapping tag names to note counts
        """
        tag_counts: dict[str, int] = {}
        for path in self.storage.list_all():
            note = self.storage.load(path)
            if note:
                for tag in note.tags:
                    tag_counts[tag] = tag_counts.get(tag, 0) + 1
        return tag_counts

    def find_by_tag(self, tag: str) -> list[Note]:
        """Find all notes with a specific tag.

        Args:
            tag: The tag to search for

        Returns:
            List of notes with the specified tag
        """
        matching_notes = []
        for path in self.storage.list_all():
            note = self.storage.load(path)
            if note and tag in note.tags:
                matching_notes.append(note)
        return matching_notes

    def get_backlinks(self, path: str) -> list[BacklinkInfo]:
        """Get all notes that link to the given path.

        Works even for non-existent paths (to find broken links).

        Args:
            path: The path to find backlinks for

        Returns:
            List of BacklinkInfo objects with source_path and line_numbers
        """
        return self.backlinks.get_backlinks(path)
