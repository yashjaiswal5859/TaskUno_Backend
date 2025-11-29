"""
Repository layer for task database operations.
"""
from typing import Optional, List
from sqlalchemy.orm import Session, joinedload

from src.tasks.models import Task, TaskLog
from src.project.models import Project


class TaskRepository:
    """Repository for task database operations."""

    def __init__(self, db: Session):
        self.db = db

    def create(self, task_data: dict) -> Task:
        """Create a new task."""
        new_task = Task(**task_data)
        self.db.add(new_task)
        self.db.commit()
        self.db.refresh(new_task)
        return new_task

    def get_by_id(self, task_id: int, owner_id: int) -> Optional[Task]:
        """Get task by ID and owner with all relationships."""
        return self.db.query(Task).options(
            joinedload(Task.owner),
            joinedload(Task.project),
            joinedload(Task.assigned_to_user),
            joinedload(Task.created_by_user)
        ).filter(
            Task.id == task_id,
            Task.owner_id == owner_id
        ).first()

    def get_all_by_owner(self, owner_id: int) -> List[Task]:
        """Get all tasks by owner."""
        return self.db.query(Task).options(
            joinedload(Task.owner),
            joinedload(Task.project)
        ).filter(Task.owner_id == owner_id).all()

    def get_all(self) -> List[Task]:
        """Get all tasks."""
        return self.db.query(Task).all()

    def update(self, task: Task, task_data: dict) -> Task:
        """Update task information."""
        for key, value in task_data.items():
            if value is not None:
                setattr(task, key, value)
        self.db.commit()
        self.db.refresh(task)
        return task

    def delete(self, task: Task) -> None:
        """Delete a task."""
        self.db.delete(task)
        self.db.commit()

    def delete_all(self) -> None:
        """Delete all tasks."""
        self.db.query(Task).delete()
        self.db.commit()

    def create_log(self, task_id: int, reason: Optional[str] = None, old_status: Optional[str] = None, new_status: Optional[str] = None) -> TaskLog:
        """Create a task log entry."""
        task_log = TaskLog(
            task_id=task_id,
            reason=reason,
            old_status=old_status,
            new_status=new_status
        )
        self.db.add(task_log)
        self.db.commit()
        self.db.refresh(task_log)
        return task_log

    def get_logs_by_owner(self, owner_id: int) -> List[TaskLog]:
        """Get task logs by owner."""
        return self.db.query(TaskLog).join(Task).filter(
            Task.owner_id == owner_id
        ).all()
    
    def get_all_by_organization_id(self, organization_id: int) -> List[Task]:
        """Get all tasks for an organization (via project)."""
        return self.db.query(Task).options(
            joinedload(Task.owner),
            joinedload(Task.project),
            joinedload(Task.assigned_to_user),
            joinedload(Task.created_by_user)
        ).join(Project).filter(
            Project.organization_id == organization_id
        ).all()
    
    def get_by_id_with_org_check(self, task_id: int, organization_id: int) -> Optional[Task]:
        """Get task by ID, verifying it belongs to the organization."""
        return self.db.query(Task).options(
            joinedload(Task.owner),
            joinedload(Task.project),
            joinedload(Task.assigned_to_user),
            joinedload(Task.created_by_user)
        ).join(Project).filter(
            Task.id == task_id,
            Project.organization_id == organization_id
        ).first()

