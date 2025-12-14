# Notes

AI-friendly note-taking solution with MCP integration and web UI.

## Installation

```bash
uv sync
```

## Quick Start

### MCP Server (Local)

Run the MCP server for AI assistants (stdio mode, no config needed):

```bash
uv run notes
```

Then configure your MCP client (see [Client Setup](#mcp-client-setup-local) below).

### Web UI

Run the web interface for browsing and editing notes:

```bash
uv run notes-web
```

Opens at http://localhost:3000 with:
- Browse and search notes
- Create, edit, and delete notes
- Tag-based organization
- REST API at `/api/*`

Options: `--port 3000`, `--host 127.0.0.1`, `--no-reload`

## MCP Client Setup (Local)

Configure your AI assistant to connect to the local MCP server.

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

Restart Claude Desktop after saving.

### VS Code

Add to `.vscode/mcp.json` in your workspace:

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

Add via Cursor Settings > MCP, or edit `mcp.json`:

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

Configure via `/mcp` command, or add to `~/.claude.json`:

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

## HTTP Mode (Remote Access)

For remote MCP access over HTTPS with bearer token authentication.

### 1. Add an API Key

```bash
uv run notes-admin auth add my-agent
```

This generates a secure token and displays it once. Save it for client configuration.

### 2. Run HTTP Server

```bash
uv run notes-admin serve
uv run notes-admin serve --host 0.0.0.0 --port 9000  # custom bind
```

### 3. Configure Reverse Proxy (HTTPS)

Use Caddy, nginx, or similar for TLS termination. Caddy example:

```
notes.example.com {
    reverse_proxy localhost:8080
}
```

### 4. Configure MCP Client

```json
{
  "mcpServers": {
    "notes": {
      "url": "https://notes.example.com/mcp",
      "headers": {
        "Authorization": "Bearer your-secret-token-here"
      }
    }
  }
}
```

### Deployment Scripts

For home servers, the `deploy/` directory contains helper scripts to run both MCP and web servers behind Caddy with HTTPS (using Tailscale certificates):

```bash
cd deploy
cp config.env.example config.env
./setup-tailscale.sh
./start.sh
```

See [deploy/README.md](deploy/README.md) for full documentation.

## Admin CLI

Command-line tools for administration:

```bash
# Manage API keys for MCP HTTP mode
uv run notes-admin auth list              # List configured keys
uv run notes-admin auth add <name>        # Generate and add new key
uv run notes-admin auth remove <name>     # Remove a key

# Manage web UI authentication
uv run notes-admin web set-password           # Set username and password
uv run notes-admin web set-password admin     # Set password for user 'admin'
uv run notes-admin web clear-password         # Disable web authentication

# Rebuild search and backlinks indexes
uv run notes-admin rebuild

# Export all notes to backup archive
uv run notes-admin export                    # → notes-backup-YYYY-MM-DD.tar.gz
uv run notes-admin export backup.tar.gz      # custom filename

# Import notes from backup archive
uv run notes-admin import backup.tar.gz              # merge with existing
uv run notes-admin import backup.tar.gz --replace    # replace all notes

# Delete all notes
uv run notes-admin clear              # prompts for confirmation
uv run notes-admin clear --force      # skip confirmation
```

## Development

Run all checks (ruff, mypy, pytest):

```bash
uv run nox -s check
```

Or run individually:

```bash
uv run pytest              # tests
uv run ruff check src tests # linting
uv run mypy src             # type checking
```
