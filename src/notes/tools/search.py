"""Search tools for MCP."""

from notes.config import get_config
from notes.search import SearchIndex
from notes.server import mcp


def _get_index() -> SearchIndex:
    config = get_config()
    config.ensure_dirs()
    return SearchIndex(config.index_dir)


@mcp.tool()
def search_notes(query: str, limit: int = 10) -> str:
    """Search for notes matching a query.

    Args:
        query: The search query (supports full-text search)
        limit: Maximum number of results to return (default: 10)

    Returns:
        Formatted search results with paths, titles, and relevance scores
    """
    index = _get_index()
    results = index.search(query, limit=limit)

    if not results:
        return f"No notes found matching '{query}'"

    output = [f"Search results for '{query}':", ""]
    for result in results:
        output.append(f"  - **{result['title']}** ({result['path']})")
        output.append(f"    Score: {result['score']}")

    return "\n".join(output)
