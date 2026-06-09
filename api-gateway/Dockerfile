# Memory limit: 120MB (set via --memory flag in docker run or mem_limit in docker-compose)
# For 1GB RAM system: 6 services @ 120MB each + Redis 64MB + New Relic 128MB = ~872MB total
FROM python:3.11-slim

WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port
EXPOSE 8000

# Run the application - with New Relic if license key is set, otherwise without
CMD sh -c '\
  if [ -n "$NEW_RELIC_LICENSE_KEY" ] && [ -f newrelic.ini ]; then \
    echo "✅ Starting app with New Relic (initialized in code)..."; \
  else \
    echo "⚠️  Starting app WITHOUT New Relic..."; \
  fi; \
  exec uvicorn src.main:app --host 0.0.0.0 --port 8000 --workers 1 --limit-max-requests 1000 --backlog 64'