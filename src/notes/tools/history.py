"""Version history tools for MCP."""

from fastmcp.exceptions import ToolError

from notes.server import get_current_author, mcp
from notes.services import NoteService


def _get_service() -> NoteService:
    return NoteService()


@mcp.tool()
def get_note_history(path: str, limit: int = 50) -> list[dict[str, str]]:
    """Get version history for a note.

    Args:
        path: The path of the note
        limit: Maximum number of versions to return (default 50, max 100)

    Returns:
        List of version objects with version (SHA), timestamp, author, and message
    """
    service = _get_service()
    limit = min(limit, 100)  # Cap at 100

    versions = service.get_note_history(path, limit=limit)

    return [
        {
            "version": v.commit_sha,
            "timestamp": v.timestamp.isoformat(),
            "author": v.author,
            "message": v.message,
        }
        for v in versions
    ]


@mcp.tool()
def get_note_version(path: str, version: str) -> dict[str, str | list[str]]:
    """Read a specific version of a note.

    Args:
        path: The path of the note
        version: The commit SHA (short or full)

    Returns:
        The note data at that version

    Raises:
        ToolError: If note or version not found
    """
    service = _get_service()
    note = service.get_note_version(path, version)

    if note is None:
        raise ToolError(f"Version '{version}' not found for note '{path}'")

    return {
        "path": note.path,
        "title": note.title,
        "content": note.content,
        "tags": note.tags,
        "version": version,
        "created_at": note.created_at.isoformat(),
        "updated_at": note.updated_at.isoformat(),
    }


@mcp.tool()
def diff_note_versions(path: str, from_version: str, to_version: str) -> dict[str, str | int]:
    """Show diff between two versions of a note.

    Args:
        path: The path of the note
        from_version: Starting version (commit SHA)
        to_version: Ending version (commit SHA)

    Returns:
        Diff information with unified diff text and change counts
    """
    service = _get_service()
    diff = service.diff_note_versions(path, from_version, to_version)

    return {
        "path": diff.path,
        "from_version": diff.from_version,
        "to_version": diff.to_version,
        "diff": diff.diff_text,
        "additions": diff.additions,
        "deletions": diff.deletions,
    }


@mcp.tool()
def restore_note_version(path: str, version: str) -> str:
    """Restore a note to a previous version.

    This creates a new commit with the old content, preserving all history.
    The previous versions remain accessible.

    Args:
        path: The path of the note
        version: The version SHA to restore

    Returns:
        Confirmation message

    Raises:
        ToolError: If note or version not found
    """
    service = _get_service()
    author = get_current_author()

    result = service.restore_note_version(path, version, author=author)

    if result is None:
        raise ToolError(f"Version '{version}' not found for note '{path}'")

    return f"Restored note '{path}' to version {version}"
