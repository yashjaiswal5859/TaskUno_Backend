#!/bin/bash

# Start Flower for monitoring Celery tasks
# Access at http://localhost:5555

echo "Starting Flower (Celery monitoring)..."

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Start Flower
celery -A src.celery_app flower --port=5555


