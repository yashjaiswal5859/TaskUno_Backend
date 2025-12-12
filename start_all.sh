#!/bin/bash

# Master script to start all microservices
# This script starts all services in the background

cd "$(dirname "$0")"

echo "🚀 Starting All Microservices..."
echo ""

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 not found. Please install Python 3."
    exit 1
fi

# Install shared library dependencies
echo -e "${BLUE}📦 Installing shared library dependencies...${NC}"
cd shared
python3 -m pip install -q -r requirements.txt 2>&1 | grep -v "already satisfied" | tail -2
cd ..

# Function to start a service
start_service() {
    local service_name=$1
    local service_dir=$2
    local port=$3
    
    echo -e "${YELLOW}Starting ${service_name}...${NC}"
    cd "$service_dir"
    
    # Install dependencies
    python3 -m pip install -q -r requirements.txt 2>&1 | grep -v "already satisfied" | tail -1
    
    # Start service in background
    export PYTHONPATH="${PYTHONPATH}:$(pwd)/.."
    nohup python3 -m uvicorn src.main:app --host 0.0.0.0 --port "$port" > "../${service_name}.log" 2>&1 &
    local pid=$!
    echo "$pid" > "../${service_name}.pid"
    
    cd ..
    echo -e "${GREEN}✅ ${service_name} started (PID: $pid, Port: $port)${NC}"
    sleep 2
}

# Start all services
start_service "api-gateway" "api-gateway" "8000"
start_service "auth-service" "auth-service" "8001"
start_service "organization-service" "organization-service" "8002"
start_service "tasks-service" "tasks-service" "8003"
start_service "projects-service" "projects-service" "8004"

echo ""
echo -e "${GREEN}✅ All services started!${NC}"
echo ""
echo "Service URLs:"
echo "  🌐 API Gateway:      http://localhost:8000"
echo "  🔐 Auth Service:     http://localhost:8001"
echo "  🏢 Organization:      http://localhost:8002"
echo "  ✅ Tasks Service:     http://localhost:8003"
echo "  📁 Projects Service: http://localhost:8004"
echo ""
echo "API Documentation:"
echo "  📚 Gateway Docs:      http://localhost:8000/docs"
echo ""
echo "Logs are in: *.log files"
echo "PIDs are in: *.pid files"
echo ""
echo "To stop all services, run: ./stop_all.sh"
echo ""


