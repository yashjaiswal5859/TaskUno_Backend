"""
Task models for the scrum board.
"""
from datetime import datetime
from sqlalchemy.orm import relationship
from sqlalchemy import Column, String, ForeignKey, Text, DateTime, Integer

from common.database.db import Base


class Task(Base):
    """Task model for the scrum board."""
    __tablename__ = "task"

    id = Column(Integer, primary_key=True, autoincrement=True)
    createdDate = Column(DateTime, default=datetime.now)
    dueDate = Column(DateTime, default=datetime.now)
    title = Column(String(50))
    description = Column(Text)
    status = Column(String(50))
    # Store IDs as integers without foreign key constraints (microservices pattern)
    # Validation happens at application level by calling other services
    project_id = Column(Integer, nullable=True)  # References project.id in Projects Service
    assigned_to = Column(Integer, nullable=True)  # References developer.id in Auth Service
    reporting_to = Column(Integer, nullable=True)  # References product_owner.id in Auth Service
    task_logs = relationship("TaskLog", back_populates="task")


class TaskLog(Base):
    """Task log model for tracking task changes."""
    __tablename__ = "task_log"

    id = Column(Integer, primary_key=True, autoincrement=True)
    createdDate = Column(DateTime, default=datetime.now)
    task_id = Column(Integer, ForeignKey("task.id", ondelete="CASCADE"))
    reason = Column(Text, nullable=True)
    old_status = Column(String(50), nullable=True)
    new_status = Column(String(50), nullable=True)
    task = relationship("Task", back_populates="task_logs")

