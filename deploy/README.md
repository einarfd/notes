# Notes Deployment

Deploy the Notes MCP server and web UI behind HTTPS using Caddy.

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
uv run notes-admin auth add my-client
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

After setup, configure your MCP client (Claude Desktop, VS Code, etc.):

```json
{
  "mcpServers": {
    "notes": {
      "url": "https://your-machine.tailnet.ts.net/mcp",
      "headers": {
        "Authorization": "Bearer YOUR_API_KEY"
      }
    }
  }
}
```

Get your API key with: `uv run notes-admin auth list`

## Web UI Authentication

Optionally protect the web UI with HTTP Basic Auth:

```bash
uv run notes-admin web set-password
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
2. Verify API key is valid: `uv run notes-admin auth list`
3. Test with curl:
   ```bash
   curl -H "Authorization: Bearer YOUR_KEY" https://hostname/mcp
   ```

## Domain Mode (VPS)

For a VPS with a real domain:

1. Edit `config.env`:
   ```bash
   MODE=domain
   DOMAIN=notes.example.com
   EMAIL=admin@example.com
   ```

2. Point your domain's DNS to your server's IP

3. Create a simple Caddyfile:
   ```
   notes.example.com {
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
