"""
Controller (API routes) for project endpoints.
"""
from typing import List
from fastapi import APIRouter, Depends, status, Response
from sqlalchemy.orm import Session

from src.database.db import get_db
from src.project.service.project_service import ProjectService
from src.project.schemas import ProjectBase, ProjectUpdate, ProjectList
from src.auth.jwt import get_current_user
from src.auth.schemas import TokenData


router = APIRouter(
    tags=["Project"],
    prefix='/project'
)


@router.post('/', status_code=status.HTTP_201_CREATED, response_model=ProjectBase)
async def create_new_project(
    request: ProjectBase,
    database: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):
    """Create a new project. Only Product Owner can create projects."""
    # Check role from JWT token
    if current_user.role != 'Product Owner' and current_user.role != 'admin':
        from fastapi import HTTPException
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only Product Owner can create projects"
        )
    
    if not current_user.org_id:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User does not belong to an organization"
        )
    
    project_service = ProjectService(database)
    result = project_service.create_project(request, current_user.id, current_user.org_id)
    return result


@router.get('/', status_code=status.HTTP_200_OK, response_model=List[ProjectList])
async def project_list(
    database: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):
    """Get all projects for current user's organization."""
    if not current_user.org_id:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User does not belong to an organization"
        )
    
    project_service = ProjectService(database)
    projects = project_service.get_all_projects(current_user.org_id)
    
    # Convert to ProjectList schema
    result = []
    for project in projects:
        project_dict = {
            "id": project.id,
            "title": project.title,
            "description": project.description,
            "owner_id": project.owner_id,
            "createdDate": project.createdDate.date() if project.createdDate else None,
            "created_by_id": project.created_by_id,
        }
        # Add owner if available
        if project.owner:
            project_dict["owner"] = {
                "username": project.owner.username,
                "email": project.owner.email
            }
        # Add created_by if available
        if project.created_by:
            project_dict["created_by"] = {
                "username": project.created_by.username,
                "firstName": project.created_by.firstName,
                "lastName": project.created_by.lastName
            }
        result.append(ProjectList(**project_dict))
    
    return result


@router.get('/{project_id}', status_code=status.HTTP_200_OK, response_model=ProjectBase)
async def get_project_by_id(
    project_id: int,
    database: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):
    """Get project by ID."""
    project_service = ProjectService(database)
    return project_service.get_project_by_id(project_id, current_user.id)


@router.delete('/{project_id}', status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
async def delete_project_by_id(
    project_id: int,
    database: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):
    """Delete project by ID. Only Product Owner can delete projects."""
    # Check role from JWT token
    if current_user.role != 'Product Owner' and current_user.role != 'admin':
        from fastapi import HTTPException
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only Product Owner can delete projects"
        )
    
    project_service = ProjectService(database)
    project_service.delete_project(project_id, current_user.id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.patch('/{project_id}', status_code=status.HTTP_200_OK, response_model=ProjectBase)
async def update_project_by_id(
    request: ProjectUpdate,
    project_id: int,
    database: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):
    """Update project by ID. Only Product Owner can update projects."""
    # Check role from JWT token
    if current_user.role != 'Product Owner' and current_user.role != 'admin':
        from fastapi import HTTPException
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only Product Owner can update projects"
        )
    
    if not current_user.org_id:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User does not belong to an organization"
        )
    
    project_service = ProjectService(database)
    return project_service.update_project(project_id, request, current_user.org_id)

