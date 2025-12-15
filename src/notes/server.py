"""FastMCP server entry point."""

from fastmcp import FastMCP

mcp = FastMCP("notes")

# Module-level author for version history
_current_author: str | None = None


def get_current_author() -> str | None:
    """Get the current author for version history commits.

    Returns:
        The author name, or None if not set.
    """
    return _current_author


def set_current_author(author: str | None) -> None:
    """Set the current author for version history commits.

    Args:
        author: The author name to use for commits.
    """
    global _current_author
    _current_author = author


# Import tools to register them with the mcp instance
from notes.tools import history, links, notes, search, tags  # noqa: F401, E402


def main() -> None:
    """Run the MCP server."""
    import argparse

    from notes.config import Config

    # Parse --author flag for stdio mode
    parser = argparse.ArgumentParser(description="Notes MCP server")
    parser.add_argument(
        "--author",
        required=True,
        help="Author name for version history commits (required)",
    )
    args, _ = parser.parse_known_args()

    set_current_author(args.author)

    config = Config.load()

    if config.server.transport == "stdio":
        mcp.run()
    else:
        # HTTP mode requires auth
        config.validate_for_http()

        # Configure auth on the server
        from notes.auth import ApiKeyAuthProvider

        mcp._auth = ApiKeyAuthProvider(config.auth.keys)  # type: ignore[attr-defined]

        import asyncio

        asyncio.run(
            mcp.run_http_async(
                transport=config.server.transport,
                host=config.server.host,
                port=config.server.port,
            )
        )


if __name__ == "__main__":
    main()
