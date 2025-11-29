"""
Celery tasks for email processing.
"""
from celery import Task
from sqlalchemy.orm import Session
from src.celery_app import celery_app
from src.database.db import SessionLocal
from src.notifications.service.email_service import EmailService
from src.notifications.repository.email_repository import EmailRepository
from src.notifications.models import EmailQueue


class DatabaseTask(Task):
    """Custom task class that provides database session."""
    
    _db: Session = None
    
    @property
    def db(self):
        if self._db is None:
            self._db = SessionLocal()
        return self._db
    
    def after_return(self, *args, **kwargs):
        """Close database session after task completion."""
        if self._db is not None:
            self._db.close()
            self._db = None


@celery_app.task(base=DatabaseTask, bind=True, max_retries=3)
def send_email_task(self, email_id: int):
    """
    Celery task to send an email.
    
    Args:
        email_id: ID of the email queue entry to send
    """
    try:
        email_service = EmailService(self.db)
        
        # Get email from queue
        email_queue_item = self.db.query(EmailQueue).filter(
            EmailQueue.id == email_id
        ).first()
        
        if not email_queue_item:
            return {"status": "error", "message": f"Email {email_id} not found"}
        
        if email_queue_item.status != "pending":
            return {"status": "skipped", "message": f"Email {email_id} already processed"}
        
        # Send email
        success = email_service.send_email(email_queue_item)
        
        if success:
            return {"status": "success", "email_id": email_id}
        else:
            # Retry if failed
            raise Exception(f"Failed to send email {email_id}")
            
    except Exception as exc:
        # Retry with exponential backoff
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))


@celery_app.task(base=DatabaseTask, bind=True)
def process_email_queue(self, limit: int = 10):
    """
    Celery task to process pending emails from the queue.
    This is called periodically by Celery Beat.
    
    Args:
        limit: Maximum number of emails to process per run
    """
    try:
        email_service = EmailService(self.db)
        email_repo = EmailRepository(self.db)
        
        # Get pending emails
        pending_emails = email_repo.get_pending(limit)
        
        results = []
        for email in pending_emails:
            # Queue individual email sending task
            send_email_task.delay(email.id)
            results.append(email.id)
        
        return {
            "status": "success",
            "queued_emails": len(results),
            "email_ids": results
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }


@celery_app.task(base=DatabaseTask, bind=True)
def send_email_async(self, to_email: str, subject: str, body: str):
    """
    Queue an email to be sent asynchronously.
    
    Args:
        to_email: Recipient email address
        subject: Email subject
        body: Email body
        
    Returns:
        Email queue ID
    """
    try:
        email_service = EmailService(self.db)
        # Queue email without Celery (to avoid recursion)
        email_queue_item = email_service.queue_email(to_email, subject, body, use_celery=False)
        
        # Queue the email sending task
        send_email_task.delay(email_queue_item.id)
        
        return {
            "status": "queued",
            "email_id": email_queue_item.id
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }

