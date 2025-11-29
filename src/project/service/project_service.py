"""
Service layer for project business logic.
"""
from typing import List
from datetime import datetime
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from src.project.models import Project
from src.project.repository.project_repository import ProjectRepository
from src.project.schemas import ProjectBase, ProjectUpdate


class ProjectService:
    """Service for project operations."""

    def __init__(self, db: Session):
        self.repository = ProjectRepository(db)

    def create_project(self, project_data: ProjectBase, created_by_id: int, organization_id: int) -> Project:
        """Create a new project. Only Product Owner can create projects."""
        project_dict = {
            "title": project_data.title,
            "description": project_data.description,
            "owner_id": created_by_id,
            "organization_id": organization_id,
            "created_by_id": created_by_id,
            "created_by_type": "product_owner",
            "createdDate": datetime.now()
        }
        return self.repository.create(project_dict)

    def get_project_by_id(self, project_id: int, owner_id: int) -> Project:
        """Get project by ID."""
        project = self.repository.get_by_id(project_id, owner_id)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project Not Found!"
            )
        return project

    def get_all_projects(self, organization_id: int) -> List[Project]:
        """Get all projects for organization."""
        return self.repository.get_all_by_organization_id(organization_id)

    def update_project(self, project_id: int, project_data: ProjectUpdate, organization_id: int) -> Project:
        """Update a project. Only Product Owner can update projects."""
        project = self.repository.get_by_id_with_org_check(project_id, organization_id)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project Not Found!"
            )
        
        update_dict = project_data.model_dump(exclude_unset=True)
        return self.repository.update(project, update_dict)

    def delete_project(self, project_id: int, owner_id: int) -> None:
        """Delete a project."""
        project = self.repository.get_by_id(project_id, owner_id)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project Not Found!"
            )
        self.repository.delete(project)

