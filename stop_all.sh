#!/bin/bash

# Script to stop all microservices

cd "$(dirname "$0")"

echo "🛑 Stopping All Microservices..."
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m' # No Color

# Stop services by PID files
for pid_file in *.pid; do
    if [ -f "$pid_file" ]; then
        service_name="${pid_file%.pid}"
        pid=$(cat "$pid_file")
        
        if ps -p "$pid" > /dev/null 2>&1; then
            kill "$pid" 2>/dev/null
            echo -e "${GREEN}✅ Stopped ${service_name} (PID: $pid)${NC}"
        else
            echo -e "${RED}⚠️  ${service_name} (PID: $pid) not running${NC}"
        fi
        
        rm -f "$pid_file"
    fi
done

# Also kill any remaining uvicorn processes on our ports
for port in 8000 8001 8002 8003 8004; do
    lsof -ti:$port | xargs kill -9 2>/dev/null
done

echo ""
echo "✅ All services stopped!"
echo ""


