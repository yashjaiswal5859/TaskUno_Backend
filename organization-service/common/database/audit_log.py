"""
Audit Log model for tracking all actions across microservices.
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, Index

from common.database.db import Base


class AuditLog(Base):
    """Audit log model for tracking all system actions."""
    __tablename__ = "audit_log"

    id = Column(Integer, primary_key=True, autoincrement=True)
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    organization_id = Column(Integer, nullable=True)  # Organization where action occurred
    employee_id = Column(Integer, nullable=False)  # ID of user who performed action (developer/product_owner)
    role_type = Column(String(50), nullable=False)  # Role: "Product Owner" or "Developer"
    action = Column(String(100), nullable=False)  # Action type: "task_created", "task_updated", "user_invited", etc.
    details = Column(Text, nullable=True)  # Additional details in JSON format or text
    resource_type = Column(String(50), nullable=True)  # Type of resource: "task", "project", "user", etc.
    resource_id = Column(Integer, nullable=True)  # ID of the resource affected

    # Indexes for common queries
    __table_args__ = (
        Index('idx_audit_org_created', 'organization_id', 'created_at'),
        Index('idx_audit_employee', 'employee_id', 'created_at'),
        Index('idx_audit_action', 'action', 'created_at'),
    )

    def __repr__(self):
        return f"<AuditLog(id={self.id}, action='{self.action}', employee_id={self.employee_id}, role='{self.role_type}')>"

