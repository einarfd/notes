# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

> **Maintenance Note**: Keep this file updated when adding new commands, components, or architectural changes.

## Project Overview

BotNotes is an AI-friendly note-taking application with both MCP server and web UI. It provides CRUD operations for notes, full-text search via Tantivy, and tag-based organization.

## Commands

```bash
# Install dependencies
uv sync

# Run the MCP server
uv run botnotes

# Run the web UI
uv run botnotes-web
uv run botnotes-web --port 3000  # custom port
uv run botnotes-web --host 127.0.0.1  # localhost only

# Run all checks (ruff, mypy, pytest)
uv run nox -s check

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
└─ Shared: Config, Models, Storage, Search, Git
```

### Core Components

- **`config.py`**: Pydantic-based configuration with default paths (`~/.local/botnotes/`)
- **`models/note.py`**: Note model with YAML frontmatter serialization and Pydantic validators (path, title, tags)
- **`models/version.py`**: NoteVersion and NoteDiff dataclasses for version history
- **`storage/`**: Abstract `StorageBackend` interface with `FilesystemStorage` implementation
- **`storage/git_repo.py`**: Git repository manager for version history (uses subprocess)
- **`search/tantivy_index.py`**: Full-text search using Tantivy (path field uses raw tokenizer for exact matching)

### Service Layer

- **`services/note_service.py`**: Central business logic shared by MCP and web
  - Accepts optional `Config` for dependency injection in tests
  - Methods: `create_note`, `read_note`, `update_note`, `delete_note`, `list_notes`, `search_notes`, `list_tags`, `find_by_tag`
  - History methods: `get_note_history`, `get_note_version`, `diff_note_versions`, `restore_note_version`

### MCP Server

- **`server.py`**: FastMCP entry point, imports tools to register them, requires `--author` flag
- **`tools/`**: MCP tools that delegate to `NoteService`
  - `tools/notes.py`: CRUD operations
  - `tools/search.py`: Full-text search
  - `tools/tags.py`: Tag listing and filtering
  - `tools/links.py`: Backlink queries
  - `tools/history.py`: Version history operations (get_note_history, get_note_version, diff_note_versions, restore_note_version)

### Web Server

- **`web/app.py`**: FastAPI app with static files and routers
- **`web/routes.py`**: REST API endpoints (`/api/*`)
- **`web/views.py`**: HTML endpoints with Jinja2 templates
- **`web/templates/`**: HTML templates using htmx
- **`web/static/`**: JavaScript and CSS

### Testing

- `tests/conftest.py`: Fixtures for temp directories and `mock_config` that patches `_get_service()`
- `tests/test_storage.py`: FilesystemStorage tests
- `tests/test_search.py`: Tantivy search index tests
- `tests/test_tools.py`: Note model serialization tests
- `tests/test_service.py`: NoteService unit tests (including history methods)
- `tests/test_mcp_tools.py`: MCP tool integration tests (including history tools)
- `tests/test_web.py`: REST API and HTML view tests (including history endpoints)
- `tests/test_validation.py`: Input validation and security tests
- `tests/test_git_repo.py`: GitRepository unit tests
- `tests/test_cli.py`: Admin CLI tests (including init-git command)
