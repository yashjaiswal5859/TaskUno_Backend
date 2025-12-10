"""
Service layer for project business logic.
"""
from typing import List
from datetime import datetime
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.models import Project
from src.repository.project_repository import ProjectRepository
from src.schemas import ProjectBase, ProjectUpdate
from common.database.audit_service import log_audit


class ProjectService:
    """Service for project operations."""

    def __init__(self, db: Session):
        self.repository = ProjectRepository(db)

    def create_project(self, project_data: ProjectBase, employee_id: int, role_type: str, organization_id: int) -> Project:
        """Create a new project."""
        project_dict = {
            "title": project_data.title,
            "description": project_data.description,
            "organization_id": organization_id,
            "created_by_id": employee_id,
            "createdDate": datetime.now()
        }
        new_project = self.repository.create(project_dict)
        
        # Log audit entry
        log_audit(
            db=self.repository.db,
            employee_id=employee_id,
            role_type=role_type,
            action="project_created",
            organization_id=organization_id,
            resource_type="project",
            resource_id=new_project.id,
            details={
                "title": project_data.title,
                "description": project_data.description
            }
        )
        
        return new_project

    def get_project_by_id(self, project_id: int, organization_id: int) -> Project:
        """Get project by ID."""
        project = self.repository.get_by_id_with_org_check(project_id, organization_id)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project Not Found!"
            )
        return project

    def get_all_projects(self, organization_id: int) -> List[Project]:
        """Get all projects for organization."""
        return self.repository.get_all_by_organization_id(organization_id)

    def update_project(self, project_id: int, project_data: ProjectUpdate, employee_id: int, role_type: str, organization_id: int) -> Project:
        """Update a project."""
        project = self.repository.get_by_id_with_org_check(project_id, organization_id)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project Not Found!"
            )
        
        update_dict = project_data.model_dump(exclude_unset=True)
        updated_project = self.repository.update(project, update_dict)
        
        # Log audit entry
        log_audit(
            db=self.repository.db,
            employee_id=employee_id,
            role_type=role_type,
            action="project_updated",
            organization_id=organization_id,
            resource_type="project",
            resource_id=project_id,
            details={"changes": update_dict}
        )
        
        return updated_project

    def delete_project(self, project_id: int, employee_id: int, role_type: str, organization_id: int) -> None:
        """Delete a project."""
        project = self.repository.get_by_id_with_org_check(project_id, organization_id)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project Not Found!"
            )
        
        # Log audit entry before deletion
        log_audit(
            db=self.repository.db,
            employee_id=employee_id,
            role_type=role_type,
            action="project_deleted",
            organization_id=organization_id,
            resource_type="project",
            resource_id=project_id,
            details={
                "title": project.title
            }
        )
        
        self.repository.delete(project)


