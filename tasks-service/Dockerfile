FROM python:3.11-slim

WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port
EXPOSE 8003

# Run the application - with New Relic if license key is set, otherwise without
CMD sh -c 'if [ -n "$NEW_RELIC_LICENSE_KEY" ] && [ -f newrelic.ini ]; then newrelic-admin run-program -c newrelic.ini python3 -m uvicorn src.main:app --host 0.0.0.0 --port 8003; else echo "⚠️  Running without New Relic"; python3 -m uvicorn src.main:app --host 0.0.0.0 --port 8003; fi'