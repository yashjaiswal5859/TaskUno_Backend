"""
Task models for the scrum board.
"""
from datetime import datetime
from sqlalchemy.orm import relationship
from sqlalchemy import Column, Float, String, ForeignKey, Text, DateTime, Integer

from src.database import Base


class Task(Base):
    """Task model for the scrum board."""
    __tablename__ = "task"

    id = Column(Integer, primary_key=True, autoincrement=True)
    createdDate = Column(DateTime, default=datetime.now)
    dueDate = Column(DateTime, default=datetime.now)
    title = Column(String(50))
    description = Column(Text)
    status = Column(String(50))
    owner_id = Column(Integer, ForeignKey("user.id", ondelete="CASCADE"))  # Keep for backward compatibility
    project_id = Column(Integer, ForeignKey("project.id", ondelete="CASCADE"))
    assigned_to = Column(Integer, ForeignKey("developer.id", ondelete="SET NULL"), nullable=True)
    created_by_id = Column(Integer, ForeignKey("product_owner.id", ondelete="SET NULL"), nullable=False)  # Product Owner ID who created the task
    created_by_type = Column(String(50), default='product_owner')
    task_logs = relationship("TaskLog", back_populates="task")

    owner = relationship("User", back_populates="tasks", lazy="joined")
    project = relationship("Project", back_populates="tasks", lazy="joined")
    assigned_to_user = relationship("Developer", foreign_keys=[assigned_to], lazy="joined")
    created_by_user = relationship("ProductOwner", foreign_keys=[created_by_id], lazy="joined")


class TaskLog(Base):
    """Task log model for tracking task changes."""
    __tablename__ = "task_log"

    id = Column(Integer, primary_key=True, autoincrement=True)
    createdDate = Column(DateTime, default=datetime.now)
    task_id = Column(Integer, ForeignKey("task.id", ondelete="CASCADE"))
    reason = Column(Text, nullable=True)  # Reason for status change
    old_status = Column(String(50), nullable=True)  # Previous status
    new_status = Column(String(50), nullable=True)  # New status
    task = relationship("Task", back_populates="task_logs")

