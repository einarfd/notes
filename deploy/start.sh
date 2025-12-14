#!/bin/bash
# Start all notes services
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="${PROJECT_DIR:-$(dirname "$SCRIPT_DIR")}"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Handle --restart flag
if [[ "${1:-}" == "--restart" || "${1:-}" == "-r" ]]; then
    echo "Stopping existing services first..."
    "$SCRIPT_DIR/stop.sh" 2>/dev/null || true
    echo
fi

# Check if port is in use
port_in_use() {
    local port=$1
    if command -v ss &> /dev/null; then
        ss -tuln 2>/dev/null | grep -q ":$port "
    elif command -v netstat &> /dev/null; then
        netstat -tuln 2>/dev/null | grep -q ":$port "
    else
        # Fallback: try to connect
        (echo >/dev/tcp/127.0.0.1/$port) 2>/dev/null
    fi
}

check_port_available() {
    local name=$1
    local port=$2
    if port_in_use "$port"; then
        echo -e "${RED}Error: Port $port is already in use ($name)${NC}"
        echo "  Run ./stop.sh first, or use: ./start.sh --restart"
        return 1
    fi
    return 0
}

# Load config
if [[ ! -f "$SCRIPT_DIR/config.env" ]]; then
    echo -e "${RED}Error: config.env not found${NC}"
    exit 1
fi
source "$SCRIPT_DIR/config.env"

# Defaults
MCP_PORT="${MCP_PORT:-8080}"
WEB_PORT="${WEB_PORT:-3000}"
PID_DIR="$SCRIPT_DIR/pids"
LOG_DIR="$SCRIPT_DIR/logs"

# Create directories
mkdir -p "$PID_DIR" "$LOG_DIR"

# Check if already running
check_running() {
    local name=$1
    local pid_file="$PID_DIR/$name.pid"
    if [[ -f "$pid_file" ]]; then
        local pid=$(cat "$pid_file")
        if kill -0 "$pid" 2>/dev/null; then
            echo -e "${YELLOW}$name already running (PID $pid)${NC}"
            return 0
        else
            rm -f "$pid_file"
        fi
    fi
    return 1
}

# Run prerequisite checks
echo "Running prerequisite checks..."
if ! "$SCRIPT_DIR/check-prereqs.sh"; then
    echo -e "${RED}Prerequisite checks failed. Fix errors before starting.${NC}"
    exit 1
fi
echo

# Check Caddyfile exists
if [[ ! -f "$SCRIPT_DIR/Caddyfile" ]]; then
    echo -e "${RED}Error: Caddyfile not found${NC}"
    echo "Run setup first: ./setup-tailscale.sh"
    exit 1
fi

# Check ports are available before starting
echo "Checking port availability..."
check_port_available "MCP server" "$MCP_PORT" || exit 1
check_port_available "Web server" "$WEB_PORT" || exit 1
check_port_available "Caddy admin" "2019" || exit 1
echo -e "${GREEN}All ports available${NC}"
echo

# Start MCP HTTP server
echo "Starting MCP HTTP server on port $MCP_PORT..."
if ! check_running "mcp"; then
    cd "$PROJECT_DIR"
    nohup uv run notes-admin serve --host 127.0.0.1 --port "$MCP_PORT" \
        > "$LOG_DIR/mcp.log" 2>&1 &
    echo $! > "$PID_DIR/mcp.pid"
    echo -e "${GREEN}MCP server started (PID $(cat "$PID_DIR/mcp.pid"))${NC}"
fi

# Start Web server
echo "Starting Web server on port $WEB_PORT..."
if ! check_running "web"; then
    cd "$PROJECT_DIR"
    nohup uv run notes-web --host 127.0.0.1 --port "$WEB_PORT" --no-reload \
        > "$LOG_DIR/web.log" 2>&1 &
    echo $! > "$PID_DIR/web.pid"
    echo -e "${GREEN}Web server started (PID $(cat "$PID_DIR/web.pid"))${NC}"
fi

# Wait a moment for services to start
sleep 2

# Check services are responding
echo
echo "Checking services..."

check_service() {
    local name=$1
    local port=$2
    if curl -sf -o /dev/null "http://127.0.0.1:$port/health"; then
        echo -e "${GREEN}✓ $name responding on port $port${NC}"
        return 0
    else
        echo -e "${RED}✗ $name not responding on port $port${NC}"
        return 1
    fi
}

check_service "MCP" "$MCP_PORT" || true
check_service "Web" "$WEB_PORT" || true

# Start Caddy
echo
echo "Starting Caddy..."
if ! check_running "caddy"; then
    cd "$SCRIPT_DIR"
    nohup caddy run --config "$SCRIPT_DIR/Caddyfile" \
        > "$LOG_DIR/caddy.log" 2>&1 &
    echo $! > "$PID_DIR/caddy.pid"
    echo -e "${GREEN}Caddy started (PID $(cat "$PID_DIR/caddy.pid"))${NC}"
fi

# Final status
echo
echo "========================================"
echo -e "${GREEN}All services started!${NC}"
echo "========================================"

# Extract hostname from Caddyfile comment
SERVICE_HOST=$(grep '^# Hostname:' "$SCRIPT_DIR/Caddyfile" | sed 's/^# Hostname: *//')
if [[ -n "$SERVICE_HOST" ]]; then
    echo
    echo "Service URLs:"
    echo "  Web UI: https://$SERVICE_HOST/"
    echo "  MCP:    https://$SERVICE_HOST/mcp"
fi

echo
echo "Logs: $LOG_DIR/"
echo "PIDs: $PID_DIR/"
echo
echo "To stop: ./stop.sh"
echo "To view logs: tail -f $LOG_DIR/*.log"
