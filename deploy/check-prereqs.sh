#!/bin/bash
# Check prerequisites for notes deployment
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="${PROJECT_DIR:-$(dirname "$SCRIPT_DIR")}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

errors=0

log_ok() {
    echo -e "${GREEN}✓${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}⚠${NC} $1"
}

log_error() {
    echo -e "${RED}✗${NC} $1"
    errors=$((errors + 1))
}

echo "Checking prerequisites..."
echo

# Load config if exists
if [[ -f "$SCRIPT_DIR/config.env" ]]; then
    source "$SCRIPT_DIR/config.env"
    log_ok "Config file found"
else
    log_error "Config file not found: $SCRIPT_DIR/config.env"
    echo "  Run: cp config.env.example config.env"
fi

MODE="${MODE:-tailscale}"

# Check Caddy
if command -v caddy &> /dev/null; then
    version=$(caddy version 2>/dev/null | head -1 || echo "unknown")
    log_ok "Caddy installed ($version)"

    # Check if Caddy can bind to privileged ports (if needed)
    HTTPS_PORT="${HTTPS_PORT:-443}"
    if [[ "$HTTPS_PORT" -lt 1024 ]]; then
        caddy_path=$(which caddy)
        if command -v getcap &> /dev/null; then
            if getcap "$caddy_path" 2>/dev/null | grep -q 'cap_net_bind_service'; then
                log_ok "Caddy can bind to port $HTTPS_PORT"
            else
                log_warn "Caddy may not be able to bind to port $HTTPS_PORT"
                echo "  Fix with: sudo setcap 'cap_net_bind_service=+ep' $caddy_path"
            fi
        else
            log_warn "Cannot check Caddy capabilities (getcap not found)"
        fi
    fi
else
    log_error "Caddy not found"
    echo "  Install: https://caddyserver.com/docs/install"
fi

# Check uv (Python package manager)
if command -v uv &> /dev/null; then
    version=$(uv --version 2>/dev/null || echo "unknown")
    log_ok "uv installed ($version)"
else
    log_error "uv not found"
    echo "  Install: https://docs.astral.sh/uv/getting-started/installation/"
fi

# Check project directory
if [[ -f "$PROJECT_DIR/pyproject.toml" ]]; then
    log_ok "Project directory found: $PROJECT_DIR"
else
    log_error "Project not found at: $PROJECT_DIR"
    echo "  Set PROJECT_DIR in config.env"
fi

# Check notes config exists with auth
NOTES_CONFIG="$HOME/.local/notes/config.toml"
if [[ -f "$NOTES_CONFIG" ]]; then
    if grep -q '\[auth.keys\]' "$NOTES_CONFIG" 2>/dev/null; then
        log_ok "Notes config with API keys found"
    else
        log_warn "Notes config exists but no API keys configured"
        echo "  Run: uv run notes-admin auth add <name>"
    fi
else
    log_warn "Notes config not found: $NOTES_CONFIG"
    echo "  MCP HTTP mode requires API keys. Run: uv run notes-admin auth add <name>"
fi

# Mode-specific checks
echo
echo "Mode: $MODE"

if [[ "$MODE" == "tailscale" ]]; then
    # Check Tailscale
    if command -v tailscale &> /dev/null; then
        log_ok "Tailscale installed"

        # Check if Tailscale is running
        if tailscale status &> /dev/null; then
            # Try to get hostname
            hostname=$(tailscale cert 2>&1 | grep -o '[a-zA-Z0-9-]*\.[a-zA-Z0-9-]*\.ts\.net' | head -1)
            if [[ -z "$hostname" ]]; then
                hostname=$(tailscale status --self --json 2>/dev/null | sed -n 's/.*"DNSName":"\([^"]*\)".*/\1/p' | sed 's/\.$//')
            fi
            if [[ -n "$hostname" ]]; then
                log_ok "Tailscale connected: $hostname"
            else
                log_ok "Tailscale connected (hostname will be detected during setup)"
            fi
        else
            log_error "Tailscale not connected"
            echo "  Run: tailscale up"
        fi
    else
        log_error "Tailscale not found"
        echo "  Install: https://tailscale.com/download"
    fi

elif [[ "$MODE" == "domain" ]]; then
    # Check domain is set
    if [[ -n "$DOMAIN" ]]; then
        log_ok "Domain configured: $DOMAIN"

        # Check DNS resolution
        if host "$DOMAIN" &> /dev/null; then
            resolved_ip=$(host "$DOMAIN" | grep "has address" | head -1 | awk '{print $4}')
            log_ok "DNS resolves to: $resolved_ip"
        else
            log_warn "DNS lookup failed for $DOMAIN"
            echo "  Ensure DNS is configured correctly"
        fi
    else
        log_error "DOMAIN not set in config.env"
    fi
else
    log_error "Unknown MODE: $MODE (use 'tailscale' or 'domain')"
fi

# Summary
echo
if [[ $errors -eq 0 ]]; then
    echo -e "${GREEN}All prerequisites satisfied!${NC}"
    exit 0
else
    echo -e "${RED}Found $errors error(s). Please fix before continuing.${NC}"
    exit 1
fi
