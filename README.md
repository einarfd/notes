# BotNotes

AI-friendly note-taking solution with MCP integration and web UI.

## Installation

```bash
uv sync
```

## Quick Start

### MCP Server (Local)

Run the MCP server for AI assistants (stdio mode, no config needed):

```bash
uv run botnotes
```

Then configure your MCP client (see [Client Setup](#mcp-client-setup-local) below).

### Web UI

Run the web interface for browsing and editing notes:

```bash
uv run botnotes-web
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
    "botnotes": {
      "command": "uv",
      "args": ["run", "--directory", "/path/to/botnotes", "botnotes", "--author", "claude"]
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
      "botnotes": {
        "command": "uv",
        "args": ["run", "--directory", "/path/to/botnotes", "botnotes", "--author", "vscode"]
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
    "botnotes": {
      "command": "uv",
      "args": ["run", "--directory", "/path/to/botnotes", "botnotes", "--author", "cursor"]
    }
  }
}
```

### Claude Code

Configure via `/mcp` command, or add to `~/.claude.json`:

```json
{
  "mcpServers": {
    "botnotes": {
      "command": "uv",
      "args": ["run", "--directory", "/path/to/botnotes", "botnotes", "--author", "claude-code"]
    }
  }
}
```

### Perplexity (macOS)

Open Perplexity → Settings → MCP Servers → Add Server:

```json
{
  "mcpServers": {
    "botnotes": {
      "command": "uv",
      "args": ["run", "--directory", "/path/to/botnotes", "botnotes", "--author", "perplexity"]
    }
  }
}
```

## HTTP Mode (Remote Access)

For remote MCP access over HTTPS with bearer token authentication.

### 1. Add an API Key

```bash
uv run botnotes-admin auth add my-agent
```

This generates a secure token and displays it once. Save it for client configuration.

### 2. Run HTTP Server

```bash
uv run botnotes-admin serve
uv run botnotes-admin serve --host 0.0.0.0 --port 9000  # custom bind
```

### 3. Configure Reverse Proxy (HTTPS)

Use Caddy, nginx, or similar for TLS termination. Caddy example:

```
botnotes.example.com {
    reverse_proxy localhost:8080
}
```

### 4. Configure MCP Client

**VS Code** (v1.102+) - native HTTP support in `.vscode/mcp.json`:

```json
{
  "servers": {
    "botnotes": {
      "type": "http",
      "url": "https://botnotes.example.com/mcp",
      "headers": {
        "Authorization": "Bearer ${input:botnotes-api-key}"
      }
    }
  },
  "inputs": [
    {
      "type": "promptString",
      "id": "botnotes-api-key",
      "description": "BotNotes API Key",
      "password": true
    }
  ]
}
```

**Claude Desktop / Cursor** - requires [mcp-remote](https://github.com/geelen/mcp-remote) proxy:

```json
{
  "mcpServers": {
    "botnotes": {
      "command": "npx",
      "args": [
        "mcp-remote",
        "https://botnotes.example.com/mcp",
        "--header",
        "Authorization: Bearer ${AUTH_TOKEN}"
      ],
      "env": {
        "AUTH_TOKEN": "your-secret-token-here"
      }
    }
  }
}
```

**Note:** Claude's web UI Connectors (Settings → Connectors) only support OAuth, not bearer tokens.

### Deployment Scripts

For home servers, the `deploy/` directory contains helper scripts to run both MCP and web servers behind Caddy with HTTPS (using Tailscale certificates):

```bash
cd deploy
cp config.env.example config.env
./setup-tailscale.sh
./start.sh
```

See [deploy/README.md](deploy/README.md) for full documentation.

## Version History

BotNotes supports git-based version history for all changes. Every note operation (create, update, delete) is tracked in a git repository with full history preserved.

### Features

- **View history**: See all changes to a note with timestamps and authors
- **View old versions**: Read any previous version of a note
- **Compare versions**: Diff between any two versions
- **Restore versions**: Restore a note to any previous version (creates a new commit)

### Author Tracking

- **MCP (stdio)**: Requires `--author` flag (see client setup above)
- **Web UI**: Uses authenticated username, or "web" if auth is disabled

### Migrating Existing Notes

To enable version history for existing notes:

```bash
uv run botnotes-admin init-git
```

This initializes a git repository and commits all existing notes.

## Admin CLI

Command-line tools for administration:

```bash
# Initialize version history for existing notes
uv run botnotes-admin init-git

# Manage API keys for MCP HTTP mode
uv run botnotes-admin auth list              # List configured keys
uv run botnotes-admin auth add <name>        # Generate and add new key
uv run botnotes-admin auth remove <name>     # Remove a key

# Manage web UI authentication
uv run botnotes-admin web set-password           # Set username and password
uv run botnotes-admin web set-password admin     # Set password for user 'admin'
uv run botnotes-admin web clear-password         # Disable web authentication

# Rebuild search and backlinks indexes
uv run botnotes-admin rebuild

# Export all notes to backup archive
uv run botnotes-admin export                    # → botnotes-backup-YYYY-MM-DD.tar.gz
uv run botnotes-admin export backup.tar.gz      # custom filename

# Import notes from backup archive
uv run botnotes-admin import backup.tar.gz              # merge with existing
uv run botnotes-admin import backup.tar.gz --replace    # replace all notes

# Delete all notes
uv run botnotes-admin clear              # prompts for confirmation
uv run botnotes-admin clear --force      # skip confirmation
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
