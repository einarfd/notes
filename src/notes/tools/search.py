"""Search tools for MCP."""

from notes.server import mcp
from notes.services import NoteService


def _get_service() -> NoteService:
    return NoteService()


@mcp.tool()
def search_notes(query: str, limit: int = 10) -> dict[str, str | list[dict[str, str]]]:
    """Search for notes matching a query.

    Args:
        query: The search query (supports full-text search)
        limit: Maximum number of results to return (default: 10, max: 100)

    Returns:
        Dict with query and list of results (path, title, score)
    """
    service = _get_service()
    # Cap limit to prevent excessive results
    limit = min(limit, 100)
    results = service.search_notes(query, limit=limit)

    return {
        "query": query,
        "results": [
            {"path": r["path"], "title": r["title"], "score": r["score"]}
            for r in results
        ],
    }
