"""
Notification models for email queue.
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime

from src.database import Base


class EmailQueue(Base):
    """Email queue model for async email sending."""
    __tablename__ = "email_queue"

    id = Column(Integer, primary_key=True, autoincrement=True)
    to_email = Column(String(255), nullable=False)
    subject = Column(String(255), nullable=False)
    body = Column(Text, nullable=False)
    status = Column(String(50), default='pending')  # pending, sent, failed
    created_at = Column(DateTime, default=datetime.now)
    sent_at = Column(DateTime, nullable=True)
    retry_count = Column(Integer, default=0)
