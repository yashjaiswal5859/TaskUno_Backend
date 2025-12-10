#!/bin/bash

# Email Service Startup Script
echo "📧 Starting Email Service..."

# Set Python path
export PYTHONPATH="$(pwd):$PYTHONPATH"

# Load environment variables if .env exists
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# Set default port if not set
export HOST=${HOST:-0.0.0.0}
export PORT=${PORT:-8005}

# Run the FastAPI service with uvicorn
python3 -m uvicorn src.main:app --host $HOST --port $PORT
