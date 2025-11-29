# Celery + Redis Setup Guide

## Overview

This application uses **Celery** with **Redis** for asynchronous task processing, specifically for:
- Email notifications
- Future real-time notifications (WebSocket/SSE ready)

## Prerequisites

1. **Redis Server** must be running
2. Install dependencies: `pip install -r requirements.txt`

## Installation

### 1. Install Redis

**macOS:**
```bash
brew install redis
brew services start redis
```

**Linux:**
```bash
sudo apt-get install redis-server
sudo systemctl start redis
```

**Docker:**
```bash
docker run -d -p 6379:6379 redis:latest
```

### 2. Install Python Dependencies

```bash
cd backend
pip install -r requirements.txt
```

## Configuration

Add to your `.env` file:

```env
# Redis Configuration
REDIS_URL=redis://localhost:6379/0

# Email Configuration (optional - for actual email sending)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM_EMAIL=noreply@yourapp.com
SMTP_USE_TLS=True
```

## Running Celery

### Start Celery Worker

```bash
cd backend
./start_celery_worker.sh
```

Or manually:
```bash
# Start worker
celery -A src.celery_app worker --loglevel=info --concurrency=4

# Start beat scheduler (in another terminal)
celery -A src.celery_app beat --loglevel=info
```

### Monitor with Flower

```bash
cd backend
./start_celery_flower.sh
```

Then visit: http://localhost:5555

## How It Works

### Email Flow

1. **Task Status Change** → Developer updates task status
2. **Queue Email** → `EmailService.queue_email()` stores email in database
3. **Celery Task** → `send_email_async` task is queued in Redis
4. **Worker Processes** → Celery worker picks up task
5. **Send Email** → `send_email_task` sends email via SMTP
6. **Update Status** → Email status updated in database

### Periodic Tasks

- **Email Queue Processor**: Runs every 60 seconds to process pending emails
- Configured in `src/celery_app.py` → `beat_schedule`

## Future: Notifications

The structure is ready for WebSocket/SSE notifications:

- `src/notifications/tasks/notification_tasks.py` - Notification tasks
- `send_notification()` - Send to individual user
- `broadcast_notification()` - Broadcast to organization

## Troubleshooting

### Redis Connection Error

```bash
# Check if Redis is running
redis-cli ping
# Should return: PONG
```

### Celery Worker Not Starting

```bash
# Check Redis connection
redis-cli -h localhost -p 6379

# Check Celery configuration
celery -A src.celery_app inspect active
```

### Email Not Sending

1. Check SMTP configuration in `.env`
2. Check email queue in database: `SELECT * FROM email_queue WHERE status='pending';`
3. Check Celery worker logs
4. Check Flower dashboard for failed tasks

## Production Considerations

1. **Use Supervisor/systemd** to manage Celery processes
2. **Configure Redis persistence** for reliability
3. **Use Redis Sentinel** for high availability
4. **Monitor with Flower** or similar tools
5. **Set up email service** (SendGrid, AWS SES, etc.) instead of SMTP


