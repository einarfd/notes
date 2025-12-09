"""FastMCP server entry point."""

from fastmcp import FastMCP

mcp = FastMCP("notes")

# Import tools to register them with the mcp instance
from notes.tools import notes, search, tags  # noqa: F401, E402


def main() -> None:
    """Run the MCP server."""
    mcp.run()


if __name__ == "__main__":
    main()
