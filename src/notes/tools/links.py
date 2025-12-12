"""Wiki link and backlink tools for MCP."""

from notes.server import mcp
from notes.services import NoteService


def _get_service() -> NoteService:
    return NoteService()


@mcp.tool()
def get_backlinks(path: str) -> dict:
    """Find all notes that link to a given note path.

    Works even for non-existent paths, which is useful for finding broken links.

    Args:
        path: The path of the note to find backlinks for

    Returns:
        Dict with path, existence status, and list of backlinks
    """
    service = _get_service()

    # Check if the note exists
    note_exists = service.read_note(path) is not None

    # Get backlinks
    backlinks = service.get_backlinks(path)

    return {
        "path": path,
        "exists": note_exists,
        "backlinks": [
            {
                "source_path": bl.source_path,
                "link_count": bl.link_count,
                "line_numbers": bl.line_numbers,
            }
            for bl in backlinks
        ],
    }
