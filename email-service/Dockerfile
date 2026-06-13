# Memory limit: 120MB (set via --memory flag in docker run or mem_limit in docker-compose)
FROM python:3.11-slim

WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port
EXPOSE 8005

# Run the application
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8005", "--workers", "1", "--backlog", "64"]
