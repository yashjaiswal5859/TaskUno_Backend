#!/bin/bash

# Start Backend Server

cd "$(dirname "$0")"

echo "🚀 Starting Fastapi-scrum-master Backend..."
echo ""

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 not found. Please install Python 3."
    exit 1
fi

# Install dependencies if needed
echo "📦 Checking dependencies..."
python3 -m pip install -q -r requirements.txt 2>&1 | grep -v "already satisfied" | tail -2

# Start the server
echo ""
echo "✅ Starting FastAPI server on http://localhost:8001"
echo "📚 API Documentation: http://localhost:8001/docs"
echo "🔧 Alternative docs: http://localhost:8001/redoc"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

python3 -m uvicorn src.main:app --reload --host 0.0.0.0 --port 8001


