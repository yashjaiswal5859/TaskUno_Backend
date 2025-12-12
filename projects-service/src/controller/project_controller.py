"""
Controller (API routes) for project endpoints.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, status, Response, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import Column, Integer, String
from common.database.db import get_db, Base

from common.auth.jwt import get_current_user
from src.service.project_service import ProjectService
from src.schemas import ProjectBase, ProjectUpdate, ProjectList, CreatedBySchema

# Minimal user models for querying (shared database)
class ProductOwner(Base):
    """Product Owner model (for querying existing product owners)."""
    __tablename__ = "product_owner"
    __table_args__ = {'extend_existing': True}
    id = Column(Integer, primary_key=True)
    email = Column(String(255))
    firstName = Column(String(50))
    lastName = Column(String(50))

class Developer(Base):
    """Developer model (for querying existing developers)."""
    __tablename__ = "developer"
    __table_args__ = {'extend_existing': True}
    id = Column(Integer, primary_key=True)
    email = Column(String(255))
    firstName = Column(String(50))
    lastName = Column(String(50))

router = APIRouter(tags=["Project"], prefix='/project')


def get_user_by_id(db: Session, user_id: int) -> Optional[dict]:
    """Get user details by ID from ProductOwner or Developer table."""
    # Try ProductOwner first
    po = db.query(ProductOwner).filter(ProductOwner.id == user_id).first()
    if po:
        return {
            "firstName": po.firstName,
            "lastName": po.lastName,
            "email": po.email
        }
    
    # Try Developer
    dev = db.query(Developer).filter(Developer.id == user_id).first()
    if dev:
        return {
            "firstName": dev.firstName,
            "lastName": dev.lastName,
            "email": dev.email
        }
    
    return None


@router.post('/', status_code=status.HTTP_201_CREATED, response_model=ProjectBase)
async def create_new_project(
    request: ProjectBase,
    database: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Create a new project. Only Product Owner can create projects."""
    if current_user.get("role") != 'Product Owner' and current_user.get("role") != 'admin':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only Product Owner can create projects"
        )
    
    if not current_user.get("org_id"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User does not belong to an organization"
        )
    
    project_service = ProjectService(database)
    result = project_service.create_project(
        request, 
        current_user["id"], 
        current_user.get("role", "Product Owner"),
        current_user["org_id"]
    )
    return result


@router.get('/', status_code=status.HTTP_200_OK, response_model=List[ProjectList])
async def project_list(
    database: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get all projects for current user's organization."""
    if not current_user.get("org_id"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User does not belong to an organization"
        )
    
    project_service = ProjectService(database)
    projects = project_service.get_all_projects(current_user["org_id"])
    
    result = []
    for project in projects:
        project_dict = {
            "id": project.id,
            "title": project.title,
            "description": project.description,
            "createdDate": project.createdDate.date() if project.createdDate else None,
            "created_by_id": project.created_by_id,
        }
        
        # Fetch created_by user details
        if project.created_by_id:
            user_info = get_user_by_id(database, project.created_by_id)
            if user_info:
                project_dict["created_by"] = CreatedBySchema(**user_info)
        
        result.append(ProjectList(**project_dict))
    
    return result


@router.get('/{project_id}', status_code=status.HTTP_200_OK, response_model=ProjectBase)
async def get_project_by_id(
    project_id: int,
    database: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get project by ID."""
    if not current_user.get("org_id"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User does not belong to an organization"
        )
    project_service = ProjectService(database)
    return project_service.get_project_by_id(project_id, current_user["org_id"])


@router.delete('/{project_id}', status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
async def delete_project_by_id(
    project_id: int,
    database: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Delete project by ID. Only Product Owner can delete projects."""
    if current_user.get("role") != 'Product Owner' and current_user.get("role") != 'admin':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only Product Owner can delete projects"
        )
    
    if not current_user.get("org_id"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User does not belong to an organization"
        )
    
    project_service = ProjectService(database)
    project_service.delete_project(
        project_id, 
        current_user["id"],
        current_user.get("role", "Product Owner"),
        current_user["org_id"]
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.patch('/{project_id}', status_code=status.HTTP_200_OK, response_model=ProjectBase)
async def update_project_by_id(
    request: ProjectUpdate,
    project_id: int,
    database: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Update project by ID. Only Product Owner can update projects."""
    if current_user.get("role") != 'Product Owner' and current_user.get("role") != 'admin':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only Product Owner can update projects"
        )
    
    if not current_user.get("org_id"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User does not belong to an organization"
        )
    
    project_service = ProjectService(database)
    return project_service.update_project(
        project_id, 
        request, 
        current_user["id"],
        current_user.get("role", "Product Owner"),
        current_user["org_id"]
    )

