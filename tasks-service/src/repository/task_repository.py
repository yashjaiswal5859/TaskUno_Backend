"""
Repository layer for task database operations.
"""
from typing import Optional, List
from sqlalchemy.orm import Session, joinedload

from src.models import Task, TaskLog

# Minimal Project model for querying (shared database)
# Note: This is a read-only model for querying projects from Projects Service
# No foreign key constraints in microservices architecture
from sqlalchemy import Column, Integer, String
from common.database.db import Base

class Project(Base):
    """Project model (for querying existing projects)."""
    __tablename__ = "project"
    __table_args__ = {'extend_existing': True}  # Allow redefinition if needed
    id = Column(Integer, primary_key=True)
    title = Column(String(50))
    organization_id = Column(Integer, nullable=True)  # No FK constraint - microservices pattern


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

    def get_by_id(self, task_id: int) -> Optional[Task]:
        """Get task by ID."""
        return self.db.query(Task).filter(Task.id == task_id).first()

    def get_all(self) -> List[Task]:
        """Get all tasks."""
        return self.db.query(Task).all()

    def update(self, task: Task, task_data: dict) -> Task:
        """Update task information."""
        for key, value in task_data.items():
            if value is not None:
                try:
                    setattr(task, key, value)
                except Exception as e:
                    raise ValueError(f"Error setting {key} to {value}: {str(e)}")
        try:
            self.db.commit()
            self.db.refresh(task)
        except Exception as e:
            self.db.rollback()
            raise ValueError(f"Error committing task update: {str(e)}")
        return task

    def delete(self, task: Task) -> None:
        """Delete a task."""
        self.db.delete(task)
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

    def get_logs_by_organization(self, organization_id: int) -> List[TaskLog]:
        """Get task logs for an organization (via project)."""
        # Get project IDs for this organization first
        project_ids = [p.id for p in self.db.query(Project.id).filter(Project.organization_id == organization_id).all()]
        if not project_ids:
            return []
        # Then get task logs for tasks in those projects
        return self.db.query(TaskLog).join(Task).filter(
            Task.project_id.in_(project_ids)
        ).all()
    
    def get_all_by_organization_id(self, organization_id: int) -> List[Task]:
        """Get all tasks for an organization (via project)."""
        try:
            # Step 1: Get all projects for this organization
            projects = self.db.query(Project).filter(Project.organization_id == organization_id).all()
            print(f"[DEBUG] Found {len(projects)} projects for organization_id={organization_id}")
            
            if not projects:
                print(f"[DEBUG] No projects found for organization_id={organization_id}")
                return []
            
            # Step 2: Extract project IDs
            project_ids = [p.id for p in projects]
            print(f"[DEBUG] Project IDs: {project_ids}")
            
            # Step 3: Get all tasks for those projects
            tasks = self.db.query(Task).filter(Task.project_id.in_(project_ids)).all()
            print(f"[DEBUG] Found {len(tasks)} tasks for projects {project_ids}")
            
            return tasks
        except Exception as e:
            print(f"[ERROR] Error getting tasks for organization_id={organization_id}: {str(e)}")
            import traceback
            traceback.print_exc()
            return []
    
    def get_by_id_with_org_check(self, task_id: int, organization_id: int) -> Optional[Task]:
        """Get task by ID, verifying it belongs to the organization."""
        task = self.db.query(Task).filter(Task.id == task_id).first()
        if not task:
            return None
        # Verify project belongs to organization
        project = self.db.query(Project).filter(Project.id == task.project_id, Project.organization_id == organization_id).first()
        if not project:
            return None
        return task

