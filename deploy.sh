#!/bin/bash

# Load environment variables
source .env

# Start Redis container (if not running)
if ! docker ps | grep -q redis; then
  echo "🔴 Starting Redis container..."
  docker run -d \
    --name redis \
    --restart unless-stopped \
    -p 6379:6379 \
    redis:7-alpine
  echo "✅ Redis started"
else
  echo "✅ Redis already running"
fi

# Start API Gateway
echo "🚀 Starting API Gateway..."
docker run -d \
  --name api-gateway \
  --restart unless-stopped \
  -p 8000:8000 \
  --env-file .env \
  api-gateway:latest

# Start Auth Service
echo "🚀 Starting Auth Service..."
docker run -d \
  --name auth-service \
  --restart unless-stopped \
  -p 8001:8001 \
  --env-file .env \
  auth-service:latest

# Start Organization Service
echo "🚀 Starting Organization Service..."
docker run -d \
  --name organization-service \
  --restart unless-stopped \
  -p 8002:8002 \
  --env-file .env \
  organization-service:latest

# Start Tasks Service
echo "🚀 Starting Tasks Service..."
docker run -d \
  --name tasks-service \
  --restart unless-stopped \
  -p 8003:8003 \
  --env-file .env \
  tasks-service:latest

# Start Projects Service
echo "🚀 Starting Projects Service..."
docker run -d \
  --name projects-service \
  --restart unless-stopped \
  -p 8004:8004 \
  --env-file .env \
  projects-service:latest

# Start Email Service
echo "🚀 Starting Email Service..."
docker run -d \
  --name email-service \
  --restart unless-stopped \
  -p 8005:8005 \
  --env-file .env \
  email-service:latest

echo "✅ All services started!"
echo ""
echo "📊 Container Status:"
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"