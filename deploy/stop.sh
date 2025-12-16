#!/bin/bash
# Stop all botnotes services
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

PID_DIR="$SCRIPT_DIR/pids"

stop_service() {
    local name=$1
    local pid_file="$PID_DIR/$name.pid"

    if [[ ! -f "$pid_file" ]]; then
        echo -e "${YELLOW}$name: no PID file found${NC}"
        return 0
    fi

    local pid=$(cat "$pid_file")
    if kill -0 "$pid" 2>/dev/null; then
        echo "Stopping $name (PID $pid)..."
        kill "$pid"

        # Wait for graceful shutdown
        local count=0
        while kill -0 "$pid" 2>/dev/null && [[ $count -lt 10 ]]; do
            sleep 1
            count=$((count + 1))
        done

        if kill -0 "$pid" 2>/dev/null; then
            echo -e "${YELLOW}$name didn't stop gracefully, forcing...${NC}"
            kill -9 "$pid" 2>/dev/null || true
        fi

        echo -e "${GREEN}$name stopped${NC}"
    else
        echo -e "${YELLOW}$name: process not running${NC}"
    fi

    rm -f "$pid_file"
}

echo "Stopping services..."
echo

# Stop in reverse order
stop_service "caddy"
stop_service "web"
stop_service "mcp"

echo
echo -e "${GREEN}All services stopped.${NC}"
