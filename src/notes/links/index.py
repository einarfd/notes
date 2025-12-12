"""Backlinks index for tracking note relationships."""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from notes.links.parser import WikiLink
    from notes.models import Note


@dataclass
class BacklinkInfo:
    """Information about a backlink."""

    source_path: str
    line_numbers: list[int]

    @property
    def link_count(self) -> int:
        """Return the number of links from this source."""
        return len(self.line_numbers)


class BacklinksIndex:
    """Index for tracking which notes link to which other notes.

    Storage format (JSON):
    {
        "version": 1,
        "links": {
            "target/path": {
                "source/path1": [line1, line2],
                "source/path2": [line3]
            }
        }
    }
    """

    VERSION = 1

    def __init__(self, index_path: Path) -> None:
        """Initialize the backlinks index.

        Args:
            index_path: Path to the JSON index file
        """
        self.index_path = index_path
        self._links: dict[str, dict[str, list[int]]] = {}
        self._loaded = False

    def _ensure_loaded(self) -> None:
        """Lazily load the index from disk."""
        if self._loaded:
            return

        if self.index_path.exists():
            try:
                data = json.loads(self.index_path.read_text())
                if data.get("version") == self.VERSION:
                    self._links = data.get("links", {})
            except (json.JSONDecodeError, OSError):
                # If the file is corrupted, start fresh
                self._links = {}

        self._loaded = True

    def _save(self) -> None:
        """Save the index to disk."""
        self.index_path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "version": self.VERSION,
            "links": self._links,
        }
        self.index_path.write_text(json.dumps(data, indent=2))

    def update_note_links(self, source_path: str, links: list[WikiLink]) -> None:
        """Update the index when a note's links change.

        This removes all old links from source_path and adds the new ones.

        Args:
            source_path: The path of the note that was updated
            links: List of WikiLink objects extracted from the note's content
        """
        self._ensure_loaded()

        # Remove all existing links from this source
        for target_path in list(self._links.keys()):
            if source_path in self._links[target_path]:
                del self._links[target_path][source_path]
                # Clean up empty targets
                if not self._links[target_path]:
                    del self._links[target_path]

        # Add new links
        for link in links:
            if link.target_path not in self._links:
                self._links[link.target_path] = {}
            if source_path not in self._links[link.target_path]:
                self._links[link.target_path][source_path] = []
            # Avoid duplicate line numbers
            if link.line_number not in self._links[link.target_path][source_path]:
                self._links[link.target_path][source_path].append(link.line_number)

        self._save()

    def remove_note(self, path: str) -> None:
        """Remove all links from a deleted note.

        Args:
            path: The path of the note being deleted
        """
        self._ensure_loaded()

        # Remove as source (links FROM this note)
        for target_path in list(self._links.keys()):
            if path in self._links[target_path]:
                del self._links[target_path][path]
                if not self._links[target_path]:
                    del self._links[target_path]

        self._save()

    def get_backlinks(self, target_path: str) -> list[BacklinkInfo]:
        """Get all notes that link to the given path.

        Works even for non-existent paths (to find broken links).

        Args:
            target_path: The path to find backlinks for

        Returns:
            List of BacklinkInfo objects
        """
        self._ensure_loaded()

        if target_path not in self._links:
            return []

        return [
            BacklinkInfo(source_path=source, line_numbers=sorted(lines))
            for source, lines in self._links[target_path].items()
        ]

    def rename_target(self, old_path: str, new_path: str) -> None:
        """Update the index when a note is moved.

        This moves the backlinks entry from old_path to new_path.
        Note: This does NOT update the actual links in other notes.

        Args:
            old_path: The old path of the moved note
            new_path: The new path of the moved note
        """
        self._ensure_loaded()

        if old_path in self._links:
            self._links[new_path] = self._links.pop(old_path)

        self._save()

    def clear(self) -> None:
        """Clear all backlinks from the index."""
        self._ensure_loaded()
        self._links = {}
        self._save()

    def rebuild(self, notes: list[Note]) -> int:
        """Rebuild the backlinks index from a list of notes.

        Args:
            notes: List of notes to process for links

        Returns:
            Number of notes processed
        """
        from notes.links.parser import extract_links

        self.clear()
        for note in notes:
            links = extract_links(note.content)
            if links:
                self.update_note_links(note.path, links)
        return len(notes)
