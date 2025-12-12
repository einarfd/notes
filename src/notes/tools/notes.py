"""Note CRUD operations as MCP tools."""

from fastmcp.exceptions import ToolError
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
        raise ToolError(f"Error creating note: {e}") from e
    return f"Created note at '{path}'"


@mcp.tool()
def read_note(path: str) -> dict[str, str | list[str]]:
    """Read a note by its path.

    Args:
        path: The path/identifier of the note to read

    Returns:
        The note data as a dict

    Raises:
        ToolError: If note not found
    """
    service = _get_service()
    note = service.read_note(path)

    if note is None:
        raise ToolError(f"Note not found: '{path}'")

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
        Confirmation message

    Raises:
        ToolError: If note not found or validation error
    """
    service = _get_service()
    try:
        note = service.update_note(path=path, title=title, content=content, tags=tags)
    except (ValidationError, ValueError) as e:
        raise ToolError(f"Error updating note: {e}") from e

    if note is None:
        raise ToolError(f"Note not found: '{path}'")

    return f"Updated note at '{path}'"


@mcp.tool()
def delete_note(path: str) -> str:
    """Delete a note.

    Args:
        path: The path/identifier of the note to delete

    Returns:
        Confirmation message with backlink warnings if applicable

    Raises:
        ToolError: If note not found
    """
    service = _get_service()
    result = service.delete_note(path)

    if not result.deleted:
        raise ToolError(f"Note not found: '{path}'")

    messages = [f"Deleted note at '{path}'"]

    if result.backlinks_warning:
        messages.append(
            f"\nWarning: {len(result.backlinks_warning)} notes have links "
            "that are now broken:"
        )
        for bl in result.backlinks_warning:
            messages.append(f"- {bl.source_path} ({bl.link_count} links)")
        messages.append(
            "\nThese links were not modified. Update or remove them manually if desired."
        )

    return "\n".join(messages)


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
