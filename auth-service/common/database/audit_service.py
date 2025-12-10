"""
Audit service for logging all actions across microservices.
"""
from datetime import datetime
from sqlalchemy.orm import Session
from typing import Optional
import json

from common.database.audit_log import AuditLog


def log_audit(
    db: Session,
    employee_id: int,
    role_type: str,
    action: str,
    organization_id: Optional[int] = None,
    resource_type: Optional[str] = None,
    resource_id: Optional[int] = None,
    details: Optional[dict] = None
) -> AuditLog:
    """
    Create an audit log entry.
    
    Args:
        db: Database session
        employee_id: ID of user performing action (developer/product_owner)
        role_type: Role of user ("Product Owner" or "Developer")
        action: Action type (e.g., "task_created", "task_updated", "user_invited")
        organization_id: Organization where action occurred
        resource_type: Type of resource affected (e.g., "task", "project", "user")
        resource_id: ID of resource affected
        details: Additional details as dictionary (will be JSON serialized)
    
    Returns:
        Created AuditLog entry
    """
    audit_entry = AuditLog(
        organization_id=organization_id,
        employee_id=employee_id,
        role_type=role_type,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        details=json.dumps(details) if details else None,
        created_at=datetime.now()
    )
    db.add(audit_entry)
    db.commit()
    db.refresh(audit_entry)
    return audit_entry

