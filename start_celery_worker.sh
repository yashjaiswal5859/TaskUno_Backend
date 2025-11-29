#!/bin/bash

# Start Celery worker for processing background tasks
# This script starts both the worker and beat scheduler

echo "Starting Celery worker and beat scheduler..."

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Start Celery worker
celery -A src.celery_app worker --loglevel=info --concurrency=4 &

# Start Celery beat scheduler
celery -A src.celery_app beat --loglevel=info &

echo "Celery worker and beat scheduler started!"
echo "Worker PID: $!"
echo ""
echo "To stop, use: pkill -f 'celery.*worker' && pkill -f 'celery.*beat'"


