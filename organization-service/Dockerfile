FROM python:3.11-slim

WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port
EXPOSE 8002

# Run the application with New Relic
CMD ["newrelic-admin", "run-program", "-c", "newrelic.ini", "python3", "-m", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8002"]