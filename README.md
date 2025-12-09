# Notes

AI-friendly note-taking solution with MCP integration and web UI.

## Installation

```bash
uv sync
```

## Usage

### MCP Server

Run the MCP server for AI assistants:

```bash
uv run notes
```

### Web UI

Run the web interface:

```bash
uv run notes-web
```

Opens at http://localhost:8000 with:
- Browse and search notes
- Create, edit, and delete notes
- Tag-based organization
- REST API at `/api/*`

## MCP Client Setup

### Claude Desktop

Add to your config file:
- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
- **Linux**: `~/.config/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "notes": {
      "command": "uv",
      "args": ["run", "--directory", "/path/to/notes", "notes"]
    }
  }
}
```

Restart Claude Desktop after saving. You should see the MCP indicator in the input box.

### VS Code

Add to `.vscode/mcp.json` in your workspace or configure globally:

```json
{
  "mcp": {
    "servers": {
      "notes": {
        "command": "uv",
        "args": ["run", "--directory", "/path/to/notes", "notes"]
      }
    }
  }
}
```

Requires VS Code 1.102+ with `chat.mcp.discovery.enabled` setting.

### Cursor

Add via Cursor Settings > MCP, or edit the `mcp.json` file:

```json
{
  "mcpServers": {
    "notes": {
      "command": "uv",
      "args": ["run", "--directory", "/path/to/notes", "notes"]
    }
  }
}
```

### Claude Code

Configure via `/mcp` command in Claude Code, or add to `~/.claude.json`:

```json
{
  "mcpServers": {
    "notes": {
      "command": "uv",
      "args": ["run", "--directory", "/path/to/notes", "notes"]
    }
  }
}
```

### Perplexity (macOS)

Perplexity's Mac app supports local MCP servers (paid subscribers, via Mac App Store).

Open Perplexity → Settings → MCP Servers → Add Server:

```json
{
  "mcpServers": {
    "notes": {
      "command": "uv",
      "args": ["run", "--directory", "/path/to/notes", "notes"]
    }
  }
}
```

## Development

Run tests:

```bash
uv run pytest
```

Run linting:

```bash
uv run ruff check src tests
```

Type checking:

```bash
uv run mypy src
```
