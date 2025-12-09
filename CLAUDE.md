# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Notes is an AI-friendly note-taking application with both MCP server and web UI. It provides CRUD operations for notes, full-text search via Tantivy, and tag-based organization.

## Commands

```bash
# Install dependencies
uv sync

# Run the MCP server
uv run notes

# Run the web UI
uv run notes-web

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

```
┌─ MCP Server (server.py)
│  └─ Tools (tools/*) ────────┐
│                              ▼
├─ Web Server (web/app.py)    NoteService (services/note_service.py)
│  └─ Routes + Views ─────────┘       │
│                                      ▼
└─ Shared: Config, Models, Storage, Search
```

### Core Components

- **`config.py`**: Pydantic-based configuration with default paths (`~/.local/notes/`)
- **`models/note.py`**: Note model with YAML frontmatter serialization
- **`storage/`**: Abstract `StorageBackend` interface with `FilesystemStorage` implementation
- **`search/tantivy_index.py`**: Full-text search using Tantivy (path field uses raw tokenizer for exact matching)

### Service Layer

- **`services/note_service.py`**: Central business logic shared by MCP and web
  - Accepts optional `Config` for dependency injection in tests
  - Methods: `create_note`, `read_note`, `update_note`, `delete_note`, `list_notes`, `search_notes`, `list_tags`, `find_by_tag`

### MCP Server

- **`server.py`**: FastMCP entry point, imports tools to register them
- **`tools/`**: MCP tools that delegate to `NoteService`

### Web Server

- **`web/app.py`**: FastAPI app with static files and routers
- **`web/routes.py`**: REST API endpoints (`/api/*`)
- **`web/views.py`**: HTML endpoints with Jinja2 templates
- **`web/templates/`**: HTML templates using htmx
- **`web/static/`**: JavaScript and CSS

### Testing

- `tests/conftest.py`: Fixtures for temp directories and `mock_config` that patches `_get_service()`
- `tests/test_mcp_tools.py`: Integration tests for MCP tools
- `tests/test_service.py`: Unit tests for NoteService
- `tests/test_web.py`: API endpoint tests using FastAPI TestClient
