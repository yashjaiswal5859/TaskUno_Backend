#!/bin/bash

# Load environment variables
source .env

# Create Docker network if it doesn't exist
if ! docker network ls | grep -q taskuno-network; then
  echo "🌐 Creating Docker network..."
  docker network create taskuno-network
  echo "✅ Network created"
else
  echo "✅ Network already exists"
fi

# Start Redis container (if not running)
if ! docker ps | grep -q redis; then
  echo "🔴 Starting Redis container..."
  docker run -d \
    --name redis \
    --restart unless-stopped \
    --network taskuno-network \
    -p 6379:6379 \
    --memory="64m" \
    --memory-swap="128m" \
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
  --network taskuno-network \
  -p 8000:8000 \
  --env-file .env \
  --memory="75m" \
  --memory-reservation="50m" \
  --memory-swap="100m" \
  -e MALLOC_TRIM_THRESHOLD_=65536 \
  -e PYTHONDONTWRITEBYTECODE=1 \
  api-gateway:latest

# Start Auth Service
echo "🚀 Starting Auth Service..."
docker run -d \
  --name auth-service \
  --restart unless-stopped \
  --network taskuno-network \
  -p 8001:8001 \
  --env-file .env \
  --memory="75m" \
  --memory-reservation="50m" \
  --memory-swap="100m" \
  -e MALLOC_TRIM_THRESHOLD_=65536 \
  -e PYTHONDONTWRITEBYTECODE=1 \
  auth-service:latest

# Start Organization Service
echo "🚀 Starting Organization Service..."
docker run -d \
  --name organization-service \
  --restart unless-stopped \
  --network taskuno-network \
  -p 8002:8002 \
  --env-file .env \
  --memory="75m" \
  --memory-reservation="50m" \
  --memory-swap="100m" \
  -e MALLOC_TRIM_THRESHOLD_=65536 \
  -e PYTHONDONTWRITEBYTECODE=1 \
  organization-service:latest

# Start Tasks Service
echo "🚀 Starting Tasks Service..."
docker run -d \
  --name tasks-service \
  --restart unless-stopped \
  --network taskuno-network \
  -p 8003:8003 \
  --env-file .env \
  --memory="75m" \
  --memory-reservation="50m" \
  --memory-swap="100m" \
  -e MALLOC_TRIM_THRESHOLD_=65536 \
  -e PYTHONDONTWRITEBYTECODE=1 \
  tasks-service:latest

# Start Projects Service
echo "🚀 Starting Projects Service..."
docker run -d \
  --name projects-service \
  --restart unless-stopped \
  --network taskuno-network \
  -p 8004:8004 \
  --env-file .env \
  --memory="75m" \
  --memory-reservation="50m" \
  --memory-swap="100m" \
  -e MALLOC_TRIM_THRESHOLD_=65536 \
  -e PYTHONDONTWRITEBYTECODE=1 \
  projects-service:latest

# Start Email Service
echo "🚀 Starting Email Service..."
docker run -d \
  --name email-service \
  --restart unless-stopped \
  --network taskuno-network \
  -p 8005:8005 \
  --env-file .env \
  --memory="75m" \
  --memory-reservation="50m" \
  --memory-swap="100m" \
  -e MALLOC_TRIM_THRESHOLD_=65536 \
  -e PYTHONDONTWRITEBYTECODE=1 \
  email-service:latest

# NOTE: New Relic infra agent removed to save ~128MB RAM on 1GB EC2.
# Use CloudWatch logs (configured via awslogs driver) for monitoring.

echo "✅ All services started!"
echo ""
echo "📊 Container Status:"
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
