"""
Controller (API routes) for task endpoints.
"""
from typing import List, Optional
from datetime import datetime, date
from fastapi import APIRouter, Depends, status, Response, HTTPException, Request
from sqlalchemy.orm import Session
from sqlalchemy import Column, Integer, String
from common.database.db import get_db, Base

from common.auth.jwt import get_current_user
from src.service.task_service import TaskService
from src.schemas import TaskBase, TaskUpdate, TaskList, TaskLogBase, AssignedToSchema, ReportingToSchema, ProjectSchema
from src.repository.task_repository import Project

# Minimal user models for querying (shared database)
class ProductOwner(Base):
    """Product Owner model (for querying existing product owners)."""
    __tablename__ = "product_owner"
    __table_args__ = {'extend_existing': True}
    id = Column(Integer, primary_key=True)
    username = Column(String(50))
    email = Column(String(255))
    firstName = Column(String(50))
    lastName = Column(String(50))

class Developer(Base):
    """Developer model (for querying existing developers)."""
    __tablename__ = "developer"
    __table_args__ = {'extend_existing': True}
    id = Column(Integer, primary_key=True)
    username = Column(String(50))
    email = Column(String(255))
    firstName = Column(String(50))
    lastName = Column(String(50))

router = APIRouter(tags=["Task"], prefix='/task')


def get_user_by_id(db: Session, user_id: int) -> Optional[dict]:
    """Get user details by ID from ProductOwner or Developer table."""
    # Try ProductOwner first
    po = db.query(ProductOwner).filter(ProductOwner.id == user_id).first()
    if po:
        return {
            "id": po.id,
            "username": po.username,
            "email": po.email,
            "firstName": po.firstName,
            "lastName": po.lastName
        }
    
    # Try Developer
    dev = db.query(Developer).filter(Developer.id == user_id).first()
    if dev:
        return {
            "id": dev.id,
            "username": dev.username,
            "email": dev.email,
            "firstName": dev.firstName,
            "lastName": dev.lastName
        }
    
    return None


def get_developer_by_id(db: Session, developer_id: int) -> Optional[dict]:
    """Get developer details by ID from Developer table only."""
    dev = db.query(Developer).filter(Developer.id == developer_id).first()
    if dev:
        return {
            "id": dev.id,
            "username": dev.username,
            "email": dev.email,
            "firstName": dev.firstName,
            "lastName": dev.lastName
        }
    return None


def get_product_owner_by_id(db: Session, po_id: int) -> Optional[dict]:
    """Get product owner details by ID from ProductOwner table only."""
    po = db.query(ProductOwner).filter(ProductOwner.id == po_id).first()
    if po:
        return {
            "id": po.id,
            "username": po.username,
            "email": po.email,
            "firstName": po.firstName,
            "lastName": po.lastName
        }
    return None


@router.post('/', status_code=status.HTTP_201_CREATED, response_model=TaskBase)
async def create_new_task(
    request: TaskBase,
    http_request: Request,
    database: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Create a new task. Only Product Owner can create tasks."""
    if current_user.get("role") != 'Product Owner' and current_user.get("role") != 'admin':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only Product Owner can create tasks"
        )
    
    if not current_user.get("org_id"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User does not belong to an organization"
        )
    
    # Get token from request
    auth_header = http_request.headers.get("Authorization")
    token = auth_header.split(" ")[1] if auth_header and auth_header.startswith("Bearer ") else ""
    
    task_service = TaskService(database)
    result = await task_service.create_task(
        request, 
        current_user["id"], 
        current_user.get("role", "Product Owner"),
        current_user["org_id"], 
        token
    )
    return result


@router.get('/logs', status_code=status.HTTP_200_OK, response_model=List[TaskLogBase])
async def task_log_list(
    database: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get task logs for current user's organization."""
    if not current_user.get("org_id"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User does not belong to an organization"
        )
    
    task_service = TaskService(database)
    result = task_service.get_task_logs(current_user["org_id"])
    return result


@router.get('/', status_code=status.HTTP_200_OK, response_model=List[TaskList])
async def task_list(
    database: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get all tasks for current user's organization."""
    if not current_user.get("org_id"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User does not belong to an organization"
        )
    
    task_service = TaskService(database)
    tasks = task_service.get_all_tasks(current_user["org_id"])
    
    result = []
    for task in tasks:
        task_dict = {
            "id": task.id,
            "title": task.title,
            "description": task.description,
            "status": task.status,
            "project_id": task.project_id,
            "createdDate": task.createdDate.date() if task.createdDate else None,
            "dueDate": task.dueDate.date() if task.dueDate else None,
            "assigned_to": task.assigned_to,
            "reporting_to": task.reporting_to,
        }
        
        # Fetch project details using project_id
        if task.project_id:
            project = database.query(Project).filter(Project.id == task.project_id).first()
            if project:
                task_dict["project"] = ProjectSchema(id=project.id, title=project.title)
        
        # Fetch assigned_to user details - search in Developer table only
        if task.assigned_to:
            assigned_user_info = get_developer_by_id(database, task.assigned_to)
            if assigned_user_info:
                task_dict["assigned_to_user"] = AssignedToSchema(**assigned_user_info)
        
        # Fetch reporting_to user details - search in ProductOwner table only
        if task.reporting_to:
            reporting_user_info = get_product_owner_by_id(database, task.reporting_to)
            if reporting_user_info:
                task_dict["reporting_to_user"] = ReportingToSchema(**reporting_user_info)
        
        result.append(TaskList(**task_dict))
    
    return result


def _get_task_response(task_id: int, database: Session, current_user: dict) -> TaskList:
    """Helper function to build task response (used by both GET and PATCH)."""
    try:
        task_service = TaskService(database)
        task = task_service.get_task_by_id(task_id, current_user["org_id"])
        
        # Safely convert dates
        created_date = None
        if task.createdDate:
            if isinstance(task.createdDate, datetime):
                created_date = task.createdDate.date()
            elif isinstance(task.createdDate, date):
                created_date = task.createdDate
        
        due_date = None
        if task.dueDate:
            if isinstance(task.dueDate, datetime):
                due_date = task.dueDate.date()
            elif isinstance(task.dueDate, date):
                due_date = task.dueDate
        
        task_dict = {
            "id": task.id,
            "title": task.title,
            "description": task.description,
            "status": task.status,
            "project_id": task.project_id,
            "createdDate": created_date,
            "dueDate": due_date,
            "assigned_to": task.assigned_to,
            "reporting_to": task.reporting_to,
        }
        
        # Fetch project details using project_id
        if task.project_id:
            project = database.query(Project).filter(Project.id == task.project_id).first()
            if project:
                task_dict["project"] = ProjectSchema(id=project.id, title=project.title)
        
        # Fetch assigned_to user details - search in Developer table only
        if task.assigned_to:
            assigned_user_info = get_developer_by_id(database, task.assigned_to)
            if assigned_user_info:
                task_dict["assigned_to_user"] = AssignedToSchema(**assigned_user_info)
        
        # Fetch reporting_to user details - search in ProductOwner table only
        if task.reporting_to:
            reporting_user_info = get_product_owner_by_id(database, task.reporting_to)
            if reporting_user_info:
                task_dict["reporting_to_user"] = ReportingToSchema(**reporting_user_info)
        
        return TaskList(**task_dict)
    except Exception as e:
        import traceback
        error_msg = f"Error in _get_task_response: {str(e)}\n{traceback.format_exc()}"
        print(f"[ERROR] {error_msg}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error building task response: {str(e)}"
        )


@router.get('/{task_id}', status_code=status.HTTP_200_OK, response_model=TaskList)
async def get_task_by_id(
    task_id: int,
    database: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get task by ID."""
    if not current_user.get("org_id"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User does not belong to an organization"
        )
    
    return _get_task_response(task_id, database, current_user)


@router.delete('/{task_id}', status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
async def delete_task_by_id(
    task_id: int,
    database: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Delete task by ID. Only Product Owner can delete tasks."""
    if current_user.get("role") != 'Product Owner' and current_user.get("role") != 'admin':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only Product Owner can delete tasks"
        )
    
    if not current_user.get("org_id"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User does not belong to an organization"
        )
    
    task_service = TaskService(database)
    task_service.delete_task(
        task_id, 
        current_user["id"],
        current_user.get("role", "Product Owner"),
        current_user["org_id"]
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.patch('/{task_id}', status_code=status.HTTP_200_OK)
async def update_task_by_id(
    request: TaskUpdate,
    task_id: int,
    http_request: Request,
    database: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Update task by ID."""
    if not current_user.get("org_id"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User does not belong to an organization"
        )
    
    # Get token from Authorization header
    token = None
    auth_header = http_request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]
    
    task_service = TaskService(database)
    updated_task = await task_service.update_task(
        task_id, 
        request, 
        current_user.get("role", "Developer"), 
        current_user["id"], 
        current_user["org_id"],
        token
    )
    
    # Build response - re-fetch task to get complete data with all relationships
    # This ensures we have the latest data after the update
    return _get_task_response(task_id, database, current_user)

