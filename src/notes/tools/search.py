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

    Query syntax:
        - Simple text: "python tutorial" (matches either term)
        - Field-specific: "title:python"
        - Boolean: "python AND tutorial", "python OR rust", "+python -beginner"
        - Phrases: '"machine learning"' (exact phrase)
        - Date ranges: "created_at:[2024-01-01 TO 2024-12-31]"

    Date math (supported in date range queries):
        - now: current timestamp
        - now-7d: 7 days ago
        - now+2w: 2 weeks from now
        - 2024-01-01-7d: 7 days before Jan 1, 2024
        - 2024-06-15+1M: 1 month after Jun 15, 2024
        - Duration units: d (days), w (weeks), M (months), y (years)

    Examples:
        - "created_at:[now-7d TO now]" - notes from last 7 days
        - "updated_at:[now-1M TO now]" - notes updated in last month
        - "python AND created_at:[now-1y TO *]" - python notes from last year
        - "title:guide AND tags:python" - python guides

    Args:
        query: Search query using Tantivy query syntax
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
