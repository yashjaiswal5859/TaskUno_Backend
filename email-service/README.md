# Email Service

Email notification service that consumes task events from Redis queue and sends emails.

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Create `.env` file (copy from `.env.example`):
```bash
cp .env.example .env
```

3. Configure SMTP settings in `.env`:
```bash
# Required SMTP settings
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com          # Sender email
SMTP_PASSWORD=your-app-password          # Sender password (Gmail: use App Password)
SMTP_FROM_EMAIL=noreply@scrummaster.com  # Optional: From email (defaults to SMTP_USER)
SMTP_USE_TLS=true
```

**Important:**
- For Gmail: Use App Password (not regular password)
  - Go to Google Account > Security > 2-Step Verification > App Passwords
  - Generate an app password and use it as `SMTP_PASSWORD`
- For other providers: Update `SMTP_HOST` and `SMTP_PORT` accordingly

4. Start the service:
```bash
./start.sh
```

## How It Works

1. **Producer (Tasks Service)**: When tasks are created/updated/deleted, events are pushed to Redis queue
2. **Consumer (This Service)**: Pulls events from Redis queue using BLPOP (blocking pop)
3. **Email Sending**: Sends emails to both `assigned_to` (developer) and `reporting_to` (product owner)

## Queue Events

The service processes three types of events:
- `task_created`: New task created
- `task_updated`: Task updated
- `task_deleted`: Task deleted

## Email Recipients

- **assigned_to**: Developer assigned to the task
- **reporting_to**: Product Owner reporting to the task

Both receive notifications for all events.

