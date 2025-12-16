"""Note service - business logic layer."""

from dataclasses import dataclass, field
from datetime import datetime

from botnotes.config import Config, get_config
from botnotes.links import BacklinkInfo, BacklinksIndex, extract_links, replace_link_target
from botnotes.models import Note, NoteDiff, NoteVersion
from botnotes.search import SearchIndex
from botnotes.storage import FilesystemStorage, RWFileLock
from botnotes.storage.git_repo import GitRepository


@dataclass
class UpdateResult:
    """Result of an update operation."""

    note: Note
    backlinks_updated: list[str] = field(default_factory=list)
    backlinks_warning: list[BacklinkInfo] = field(default_factory=list)


@dataclass
class DeleteResult:
    """Result of a delete operation."""

    deleted: bool
    backlinks_warning: list[BacklinkInfo] = field(default_factory=list)


@dataclass
class RebuildResult:
    """Result of a rebuild operation."""

    notes_processed: int
    search_index_rebuilt: bool
    backlinks_index_rebuilt: bool


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
        self._git: GitRepository | None = None
        self.__lock: RWFileLock | None = None

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

    @property
    def git(self) -> GitRepository:
        """Get the git repository (lazily initialized)."""
        if self._git is None:
            self._git = GitRepository(self._config.notes_dir)
            self._git.ensure_initialized()
        return self._git

    @property
    def _lock(self) -> RWFileLock:
        """Get the read/write lock (lazily initialized)."""
        if self.__lock is None:
            lock_path = self._config.index_dir / "botnotes.lock"
            self.__lock = RWFileLock(lock_path)
        return self.__lock

    def create_note(
        self,
        path: str,
        title: str,
        content: str,
        tags: list[str] | None = None,
        author: str | None = None,
    ) -> Note:
        """Create a new note.

        Args:
            path: The path/identifier for the note
            title: The title of the note
            content: The markdown content of the note
            tags: Optional list of tags
            author: Optional author name for version history

        Returns:
            The created Note object
        """
        with self._lock.write_lock():
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

            # Commit to git for version history
            self.git.commit_change(path, "create", author=author)

            return note

    def read_note(self, path: str) -> Note | None:
        """Read a note by its path.

        Args:
            path: The path/identifier of the note

        Returns:
            The Note object, or None if not found
        """
        with self._lock.read_lock():
            return self.storage.load(path)

    def update_note(
        self,
        path: str,
        title: str | None = None,
        content: str | None = None,
        tags: list[str] | None = None,
        add_tags: list[str] | None = None,
        remove_tags: list[str] | None = None,
        new_path: str | None = None,
        update_backlinks: bool = True,
        author: str | None = None,
    ) -> UpdateResult | None:
        """Update an existing note.

        Args:
            path: The path/identifier of the note
            title: New title (optional)
            content: New content (optional)
            tags: New tags - replaces all existing tags (optional)
            add_tags: Tags to add to existing tags (optional, mutually exclusive with tags)
            remove_tags: Tags to remove from existing tags (optional, mutually exclusive with tags)
            new_path: New path to move the note to (optional)
            update_backlinks: If moving, whether to update links in other notes (default True)
            author: Optional author name for version history

        Returns:
            UpdateResult with the note and backlink info, or None if not found

        Raises:
            ValueError: If new_path already exists, or if tags is used with add_tags/remove_tags
        """
        # Validate mutually exclusive parameters
        if tags is not None and (add_tags is not None or remove_tags is not None):
            raise ValueError("Cannot use 'tags' with 'add_tags' or 'remove_tags'")

        with self._lock.write_lock():
            note = self.storage.load(path)
            if note is None:
                return None

            if title is not None:
                note.title = title
            if content is not None:
                note.content = content
            if tags is not None:
                note.tags = tags
            elif add_tags is not None or remove_tags is not None:
                # Incremental tag operations
                current_tags = set(note.tags)
                if add_tags:
                    current_tags.update(add_tags)
                if remove_tags:
                    current_tags.difference_update(remove_tags)
                note.tags = sorted(current_tags)

            note.updated_at = datetime.now()

            backlinks_updated: list[str] = []
            backlinks_warning: list[BacklinkInfo] = []

            # Handle move (new_path)
            if new_path is not None and new_path != path:
                # Check that destination doesn't exist
                if self.storage.load(new_path) is not None:
                    raise ValueError(f"Note already exists at '{new_path}'")

                # Get backlinks to the old path
                incoming_backlinks = self.backlinks.get_backlinks(path)

                if update_backlinks and incoming_backlinks:
                    # Update content in all linking notes
                    for bl in incoming_backlinks:
                        source_note = self.storage.load(bl.source_path)
                        if source_note is not None:
                            new_content = replace_link_target(
                                source_note.content, path, new_path
                            )
                            if new_content != source_note.content:
                                source_note.content = new_content
                                source_note.updated_at = datetime.now()
                                self.storage.save(source_note)
                                # Update the source note's links in the index
                                links = extract_links(source_note.content)
                                self.backlinks.update_note_links(bl.source_path, links)
                                backlinks_updated.append(bl.source_path)
                elif incoming_backlinks:
                    # Don't update, but warn about broken links
                    backlinks_warning = incoming_backlinks

                # Delete old file and update indexes
                self.storage.delete(path)
                self.index.remove_note(path)
                self.backlinks.remove_note(path)

                # Update note path and save to new location
                note.path = new_path
                self.storage.save(note)
                self.index.index_note(note)

                # Update backlinks index to point to new path
                links = extract_links(note.content)
                self.backlinks.update_note_links(new_path, links)

                # Commit the move to git
                self.git.commit_change(new_path, "move", author=author)
            else:
                # No move - just save in place
                self.storage.save(note)
                self.index.index_note(note)

                # Update wiki links index if content changed
                if content is not None:
                    links = extract_links(note.content)
                    self.backlinks.update_note_links(path, links)

                # Commit update to git
                self.git.commit_change(path, "update", author=author)

            return UpdateResult(
                note=note,
                backlinks_updated=backlinks_updated,
                backlinks_warning=backlinks_warning,
            )

    def delete_note(self, path: str, author: str | None = None) -> DeleteResult:
        """Delete a note.

        Args:
            path: The path/identifier of the note
            author: Optional author name for version history

        Returns:
            DeleteResult with deleted status and backlink warnings
        """
        with self._lock.write_lock():
            # Get backlinks before deletion to warn about broken links
            backlinks_warning = self.backlinks.get_backlinks(path)

            if self.storage.delete(path):
                self.index.remove_note(path)
                self.backlinks.remove_note(path)
                # Commit deletion to git
                self.git.commit_change(path, "delete", author=author)
                return DeleteResult(deleted=True, backlinks_warning=backlinks_warning)
            return DeleteResult(deleted=False)

    def list_notes(self) -> list[str]:
        """List all note paths.

        Returns:
            List of note paths
        """
        with self._lock.read_lock():
            return self.storage.list_all()

    def list_notes_in_folder(self, folder: str = "") -> dict[str, list[str]]:
        """List notes and subfolders in a specific folder.

        Args:
            folder: Folder path. Empty string = top-level only.

        Returns:
            Dict with 'notes' (direct notes) and 'subfolders' (immediate subfolders).
        """
        with self._lock.read_lock():
            return self.storage.list_by_prefix(folder)

    def search_notes(self, query: str, limit: int = 10) -> list[dict[str, str]]:
        """Search for notes.

        Args:
            query: The search query
            limit: Maximum number of results

        Returns:
            List of search results with path, title, and score
        """
        with self._lock.read_lock():
            return self.index.search(query, limit=limit)

    def list_tags(self) -> dict[str, int]:
        """List all tags with their counts.

        Returns:
            Dictionary mapping tag names to note counts
        """
        with self._lock.read_lock():
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
        with self._lock.read_lock():
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
        with self._lock.read_lock():
            return self.backlinks.get_backlinks(path)

    def rebuild_indexes(self) -> RebuildResult:
        """Rebuild both search and backlinks indexes from all stored notes.

        This is useful when:
        - Index files become corrupted
        - Code changes affect indexing logic
        - Notes were added outside the app

        Returns:
            RebuildResult with number of notes processed and rebuild status
        """
        with self._lock.write_lock():
            # Load all notes from storage
            all_notes: list[Note] = []
            for path in self.storage.list_all():
                note = self.storage.load(path)
                if note:
                    all_notes.append(note)

            # Rebuild both indexes
            self.index.rebuild(all_notes)
            self.backlinks.rebuild(all_notes)

            return RebuildResult(
                notes_processed=len(all_notes),
                search_index_rebuilt=True,
                backlinks_index_rebuilt=True,
            )

    # History methods

    def get_note_history(self, path: str, limit: int = 50) -> list[NoteVersion]:
        """Get version history for a note.

        Args:
            path: The path of the note
            limit: Maximum number of versions to return (default 50)

        Returns:
            List of NoteVersion objects, most recent first
        """
        with self._lock.read_lock():
            return self.git.get_file_history(path, limit=limit)

    def get_note_version(self, path: str, version: str) -> Note | None:
        """Get a specific version of a note.

        Args:
            path: The path of the note
            version: The commit SHA (short or full)

        Returns:
            The Note object at that version, or None if not found
        """
        with self._lock.read_lock():
            content = self.git.get_file_at_version(path, version)
            if content is None:
                return None
            return Note.from_markdown(path, content)

    def diff_note_versions(
        self,
        path: str,
        from_version: str,
        to_version: str,
    ) -> NoteDiff:
        """Get diff between two versions of a note.

        Args:
            path: The path of the note
            from_version: The starting version SHA
            to_version: The ending version SHA

        Returns:
            NoteDiff object with diff information
        """
        with self._lock.read_lock():
            return self.git.diff_versions(path, from_version, to_version)

    def restore_note_version(
        self,
        path: str,
        version: str,
        author: str | None = None,
    ) -> Note | None:
        """Restore a note to a previous version.

        This creates a new commit with the old content, preserving history.

        Args:
            path: The path of the note
            version: The version SHA to restore
            author: Optional author name for the restore commit

        Returns:
            The restored Note object, or None if version not found
        """
        with self._lock.write_lock():
            old_note = self.get_note_version(path, version)
            if old_note is None:
                return None

            # Update the note with old content (creates new commit)
            result = self.update_note(
                path=path,
                title=old_note.title,
                content=old_note.content,
                tags=old_note.tags,
                author=author,
            )

            if result is None:
                return None
            return result.note
