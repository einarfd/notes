"""Search tools for MCP."""

from notes.server import mcp
from notes.services import NoteService


def _get_service() -> NoteService:
    return NoteService()


@mcp.tool()
def search_notes(query: str, limit: int = 10) -> str:
    """Search for notes matching a query.

    Args:
        query: The search query (supports full-text search)
        limit: Maximum number of results to return (default: 10, max: 100)

    Returns:
        Formatted search results with paths, titles, and relevance scores
    """
    service = _get_service()
    # Cap limit to prevent excessive results
    limit = min(limit, 100)
    results = service.search_notes(query, limit=limit)

    if not results:
        return f"No notes found matching '{query}'"

    output = [f"Search results for '{query}':", ""]
    for result in results:
        output.append(f"  - **{result['title']}** ({result['path']})")
        output.append(f"    Score: {result['score']}")

    return "\n".join(output)
