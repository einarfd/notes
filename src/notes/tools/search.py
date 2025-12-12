"""Search tools for MCP."""

from notes.server import mcp
from notes.services import NoteService


def _get_service() -> NoteService:
    return NoteService()


@mcp.tool()
def search_notes(query: str, limit: int = 10) -> dict[str, str | list[dict[str, str]]]:
    """Search for notes using full-text search with Tantivy query syntax.

    Schema fields:
        - title: Note title (text, searchable)
        - content: Note body (text, searchable)
        - tags: Space-separated tags (text, searchable)
        - created_at: Creation timestamp (date, searchable)
        - updated_at: Last update timestamp (date, searchable)

    Query syntax examples:
        - Simple text: "python tutorial"
        - Field-specific: "title:python"
        - Boolean: "python AND tutorial", "python OR rust", "python NOT beginner"
        - Phrases: '"machine learning"'
        - Wildcards: "pyth*"
        - Date ranges: "created_at:[2024-01-01T00:00:00Z TO 2024-12-31T23:59:59Z]"
        - Combined: "title:python AND created_at:[2024-01-01T00:00:00Z TO *]"

    Args:
        query: Search query using Tantivy/Lucene-like syntax
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
