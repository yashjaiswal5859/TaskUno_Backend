"""
Repository layer for email queue database operations.
"""
from typing import List
from sqlalchemy.orm import Session

from src.notifications.models import EmailQueue


class EmailRepository:
    """Repository for email queue database operations."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create(self, email_data: dict) -> EmailQueue:
        """Add email to queue."""
        email_queue = EmailQueue(**email_data)
        self.db.add(email_queue)
        self.db.commit()
        self.db.refresh(email_queue)
        return email_queue
    
    def get_pending(self, limit: int = 10) -> List[EmailQueue]:
        """Get pending emails."""
        return self.db.query(EmailQueue).filter(
            EmailQueue.status == 'pending'
        ).limit(limit).all()
    
    def update_status(self, email_id: int, status: str) -> None:
        """Update email status."""
        email = self.db.query(EmailQueue).filter(EmailQueue.id == email_id).first()
        if email:
            email.status = status
            self.db.commit()
            self.db.refresh(email)


