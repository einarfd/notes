"""Tag management tools for MCP."""

from botnotes.server import mcp
from botnotes.services import NoteService


def _get_service() -> NoteService:
    return NoteService()


@mcp.tool()
def list_tags() -> dict[str, int]:
    """List all tags used across notes.

    Returns:
        Dict mapping tag names to their note counts
    """
    service = _get_service()
    return service.list_tags()


@mcp.tool()
def find_by_tag(tag: str) -> dict[str, str | list[dict[str, str]]]:
    """Find all notes with a specific tag.

    Args:
        tag: The tag to search for

    Returns:
        Dict with tag and list of matching notes (path, title)
    """
    service = _get_service()
    matching_notes = service.find_by_tag(tag)

    return {
        "tag": tag,
        "notes": [{"path": note.path, "title": note.title} for note in matching_notes],
    }
