"""Note CRUD operations as MCP tools."""

from pydantic import ValidationError

from notes.server import mcp
from notes.services import NoteService


def _get_service() -> NoteService:
    return NoteService()


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
    service = _get_service()
    try:
        service.create_note(path=path, title=title, content=content, tags=tags)
    except (ValidationError, ValueError) as e:
        return f"Error creating note: {e}"
    return f"Created note at '{path}'"


@mcp.tool()
def read_note(path: str) -> dict[str, str | list[str]] | str:
    """Read a note by its path.

    Args:
        path: The path/identifier of the note to read

    Returns:
        The note data as a dict, or an error message if not found
    """
    service = _get_service()
    note = service.read_note(path)

    if note is None:
        return f"Note not found: '{path}'"

    return {
        "path": note.path,
        "title": note.title,
        "content": note.content,
        "tags": note.tags,
        "created_at": note.created_at.isoformat(),
        "updated_at": note.updated_at.isoformat(),
    }


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
    service = _get_service()
    try:
        note = service.update_note(path=path, title=title, content=content, tags=tags)
    except (ValidationError, ValueError) as e:
        return f"Error updating note: {e}"

    if note is None:
        return f"Note not found: '{path}'"

    return f"Updated note at '{path}'"


@mcp.tool()
def delete_note(path: str) -> str:
    """Delete a note.

    Args:
        path: The path/identifier of the note to delete

    Returns:
        Confirmation message or error if note not found
    """
    service = _get_service()

    if service.delete_note(path):
        return f"Deleted note at '{path}'"

    return f"Note not found: '{path}'"


@mcp.tool()
def list_notes() -> list[str]:
    """List all notes.

    Returns:
        List of all note paths
    """
    service = _get_service()
    return service.list_notes()


@mcp.tool()
def list_notes_in_folder(folder_path: str = "") -> dict[str, str | list[str]]:
    """List notes and subfolders in a specific folder.

    Args:
        folder_path: The folder path to list (e.g., "projects" or "projects/myproject").
                     Empty string lists only top-level contents.

    Returns:
        Dict with folder path, subfolders list, and notes list
    """
    service = _get_service()
    contents = service.list_notes_in_folder(folder_path)

    return {
        "folder": folder_path or "/",
        "subfolders": contents["subfolders"],
        "notes": contents["notes"],
    }
