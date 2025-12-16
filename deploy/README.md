# BotNotes Deployment

Deploy the BotNotes MCP server and web UI behind HTTPS using Caddy.

## Prerequisites

- **Caddy** - [Install Caddy](https://caddyserver.com/docs/install)
- **uv** - [Install uv](https://docs.astral.sh/uv/getting-started/installation/)
- **Tailscale** (for home servers) - [Install Tailscale](https://tailscale.com/download)

## Quick Start (Tailscale)

For home servers using Tailscale for HTTPS certificates:

```bash
# 1. Configure
cp config.env.example config.env
# Edit config.env if needed (defaults work for most setups)

# 2. Set up API keys for MCP authentication
cd ..
uv run botnotes-admin auth add my-client
# Save the token shown

# 3. Set up Tailscale certificates
cd deploy
./setup-tailscale.sh

# 4. Start services
./start.sh
```

Your services will be available at:
- **Web UI**: `https://your-machine.tailnet.ts.net/`
- **MCP**: `https://your-machine.tailnet.ts.net/mcp`

## Scripts

| Script | Purpose |
|--------|---------|
| `check-prereqs.sh` | Validate all prerequisites |
| `setup-tailscale.sh` | Fetch Tailscale certs and generate Caddyfile |
| `start.sh` | Start MCP server, web server, and Caddy |
| `stop.sh` | Stop all services |

## Configuration

Edit `config.env`:

```bash
# Mode: tailscale or domain
MODE=tailscale

# Service ports (internal)
MCP_PORT=8080
WEB_PORT=3000

# HTTPS port (use 443 for standard, or higher if not root)
HTTPS_PORT=443
```

## MCP Client Configuration

After setup, configure your MCP client.

**VS Code** (v1.102+) - native HTTP support in `.vscode/mcp.json`:

```json
{
  "servers": {
    "botnotes": {
      "type": "http",
      "url": "https://your-machine.tailnet.ts.net/mcp",
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
        "https://your-machine.tailnet.ts.net/mcp",
        "--header",
        "Authorization: Bearer ${AUTH_TOKEN}"
      ],
      "env": {
        "AUTH_TOKEN": "your-api-key-here"
      }
    }
  }
}
```

**Note:** Claude's web UI Connectors (Settings → Connectors) only support OAuth, not bearer tokens.

Get your API key with: `uv run botnotes-admin auth list`

## Web UI Authentication

Optionally protect the web UI with HTTP Basic Auth:

```bash
uv run botnotes-admin web set-password
# Enter username and password when prompted
```

## Logs and PIDs

- Logs: `deploy/logs/`
  - `mcp.log` - MCP server output
  - `web.log` - Web server output
  - `caddy.log` - Caddy output
  - `access.log` - HTTP access log

- PIDs: `deploy/pids/`
  - Used by `stop.sh` for graceful shutdown

## Troubleshooting

### Tailscale certificates fail

Ensure HTTPS certificates are enabled in your Tailscale admin:
https://login.tailscale.com/admin/dns

Look for "HTTPS Certificates" and enable it.

### Port 443 requires root

Either:
1. Run with sudo (not recommended for long-term)
2. Use a higher port in `config.env`: `HTTPS_PORT=8443`
3. Use `setcap` to allow Caddy to bind to low ports:
   ```bash
   sudo setcap cap_net_bind_service=+ep $(which caddy)
   ```

### Services not starting

Check logs:
```bash
tail -f logs/*.log
```

Check prerequisites:
```bash
./check-prereqs.sh
```

### MCP client can't connect

1. Verify the URL is correct (check Tailscale hostname)
2. Verify API key is valid: `uv run botnotes-admin auth list`
3. Test with curl:
   ```bash
   curl -H "Authorization: Bearer YOUR_KEY" https://hostname/mcp
   ```

## Domain Mode (VPS)

For a VPS with a real domain:

1. Edit `config.env`:
   ```bash
   MODE=domain
   DOMAIN=botnotes.example.com
   EMAIL=admin@example.com
   ```

2. Point your domain's DNS to your server's IP

3. Create a simple Caddyfile:
   ```
   botnotes.example.com {
       handle /mcp* {
           reverse_proxy localhost:8080
       }
       handle {
           reverse_proxy localhost:3000
       }
   }
   ```

4. Run `./start.sh` - Caddy will automatically fetch Let's Encrypt certs

## Directory Structure

```
deploy/
├── config.env.example    # Configuration template
├── config.env            # Your configuration (git-ignored)
├── check-prereqs.sh      # Prerequisite checker
├── setup-tailscale.sh    # Tailscale setup
├── start.sh              # Start services
├── stop.sh               # Stop services
├── Caddyfile             # Generated Caddy config
├── Caddyfile.template    # Reference template
├── certs/                # Tailscale certificates
├── logs/                 # Service logs
└── pids/                 # Process ID files
```
