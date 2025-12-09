"""Note CRUD operations as MCP tools."""

from datetime import datetime

from notes.config import get_config
from notes.models.note import Note
from notes.search import SearchIndex
from notes.server import mcp
from notes.storage import FilesystemStorage


def _get_storage() -> FilesystemStorage:
    config = get_config()
    config.ensure_dirs()
    return FilesystemStorage(config.notes_dir)


def _get_index() -> SearchIndex:
    config = get_config()
    config.ensure_dirs()
    return SearchIndex(config.index_dir)


@mcp.tool()
def create_note(path: str, title: str, content: str, tags: list[str] | None = None) -> str:
    """Create a new note.

    Args:
        path: The path/identifier for the note (e.g., "projects/wiki-ai/design")
        title: The title of the note
        content: The markdown content of the note
        tags: Optional list of tags for categorization

    Returns:
        Confirmation message with the note path
    """
    storage = _get_storage()
    index = _get_index()

    note = Note(
        path=path,
        title=title,
        content=content,
        tags=tags or [],
    )

    storage.save(note)
    index.index_note(note)

    return f"Created note at '{path}'"


@mcp.tool()
def read_note(path: str) -> str:
    """Read a note by its path.

    Args:
        path: The path/identifier of the note to read

    Returns:
        The note content with metadata, or an error message if not found
    """
    storage = _get_storage()
    note = storage.load(path)

    if note is None:
        return f"Note not found: '{path}'"

    return f"""# {note.title}

**Path:** {note.path}
**Tags:** {', '.join(note.tags) if note.tags else 'none'}
**Created:** {note.created_at.isoformat()}
**Updated:** {note.updated_at.isoformat()}

---

{note.content}"""


@mcp.tool()
def update_note(
    path: str,
    title: str | None = None,
    content: str | None = None,
    tags: list[str] | None = None,
) -> str:
    """Update an existing note.

    Args:
        path: The path/identifier of the note to update
        title: New title (optional, keeps existing if not provided)
        content: New content (optional, keeps existing if not provided)
        tags: New tags (optional, keeps existing if not provided)

    Returns:
        Confirmation message or error if note not found
    """
    storage = _get_storage()
    index = _get_index()

    note = storage.load(path)
    if note is None:
        return f"Note not found: '{path}'"

    # Update fields if provided
    if title is not None:
        note.title = title
    if content is not None:
        note.content = content
    if tags is not None:
        note.tags = tags

    note.updated_at = datetime.now()

    storage.save(note)
    index.index_note(note)

    return f"Updated note at '{path}'"


@mcp.tool()
def delete_note(path: str) -> str:
    """Delete a note.

    Args:
        path: The path/identifier of the note to delete

    Returns:
        Confirmation message or error if note not found
    """
    storage = _get_storage()
    index = _get_index()

    if storage.delete(path):
        index.remove_note(path)
        return f"Deleted note at '{path}'"

    return f"Note not found: '{path}'"


@mcp.tool()
def list_notes() -> str:
    """List all notes.

    Returns:
        A formatted list of all note paths
    """
    storage = _get_storage()
    paths = storage.list_all()

    if not paths:
        return "No notes found."

    return "Notes:\n" + "\n".join(f"  - {path}" for path in paths)
