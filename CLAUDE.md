# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Notes is an AI-friendly note-taking MCP server built with FastMCP. It provides CRUD operations for notes, full-text search via Tantivy, and tag-based organization.

## Commands

```bash
# Install dependencies
uv sync

# Run the MCP server
uv run notes

# Run tests
uv run pytest

# Run a single test
uv run pytest tests/test_storage.py::test_name -v

# Linting
uv run ruff check src tests

# Type checking
uv run mypy src
```

## Architecture

### Core Components

- **`server.py`**: FastMCP entry point - creates the `mcp` instance and `main()` function
- **`config.py`**: Pydantic-based configuration with default paths (`~/.local/notes/`)
- **`models/note.py`**: Note model with YAML frontmatter serialization (`to_markdown`/`from_markdown`)
- **`storage/`**: Abstract `StorageBackend` interface with `FilesystemStorage` implementation
- **`search/tantivy_index.py`**: Full-text search using Tantivy with fields: path, title, content, tags

### MCP Tools

Tools are registered via `@mcp.tool()` decorator on the shared `mcp` instance from `server.py`:

- **`tools/notes.py`**: `create_note`, `read_note`, `update_note`, `delete_note`, `list_notes`
- **`tools/search.py`**: `search_notes` (full-text search with limit)
- **`tools/tags.py`**: `list_tags`, `find_by_tag`

### Data Flow

1. Tool functions get storage/index via helper functions (`_get_storage()`, `_get_index()`)
2. Notes are stored as markdown files with YAML frontmatter at `{notes_dir}/{path}.md`
3. Search index is maintained separately in `index_dir` and updated on create/update/delete

### Testing

Tests use pytest fixtures in `conftest.py` that provide temporary directories for isolated `storage`, `search_index`, and `config` instances.
