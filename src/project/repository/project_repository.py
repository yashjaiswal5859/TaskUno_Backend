"""
Repository layer for project database operations.
"""
from typing import Optional, List
from sqlalchemy.orm import Session, joinedload

from src.project.models import Project


class ProjectRepository:
    """Repository for project database operations."""

    def __init__(self, db: Session):
        self.db = db

    def create(self, project_data: dict) -> Project:
        """Create a new project."""
        new_project = Project(**project_data)
        self.db.add(new_project)
        self.db.commit()
        self.db.refresh(new_project)
        return new_project

    def get_by_id(self, project_id: int, owner_id: int) -> Optional[Project]:
        """Get project by ID and owner."""
        return self.db.query(Project).options(
            joinedload(Project.owner)
        ).filter(
            Project.id == project_id,
            Project.owner_id == owner_id
        ).first()

    def get_all_by_owner(self, owner_id: int) -> List[Project]:
        """Get all projects by owner."""
        return self.db.query(Project).options(
            joinedload(Project.owner)
        ).filter(Project.owner_id == owner_id).all()

    def update(self, project: Project, project_data: dict) -> Project:
        """Update project information."""
        for key, value in project_data.items():
            if value is not None:
                setattr(project, key, value)
        self.db.commit()
        self.db.refresh(project)
        return project

    def delete(self, project: Project) -> None:
        """Delete a project."""
        self.db.delete(project)
        self.db.commit()
    
    def get_all_by_organization_id(self, organization_id: int) -> List[Project]:
        """Get all projects for an organization."""
        return self.db.query(Project).options(
            joinedload(Project.owner),
            joinedload(Project.organization),
            joinedload(Project.created_by)
        ).filter(Project.organization_id == organization_id).all()
    
    def get_by_id_with_org_check(self, project_id: int, organization_id: int) -> Optional[Project]:
        """Get project by ID, verifying it belongs to the organization."""
        return self.db.query(Project).options(
            joinedload(Project.owner),
            joinedload(Project.organization),
            joinedload(Project.created_by)
        ).filter(
            Project.id == project_id,
            Project.organization_id == organization_id
        ).first()

