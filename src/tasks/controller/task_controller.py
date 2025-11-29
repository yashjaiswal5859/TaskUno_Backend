"""
Controller (API routes) for task endpoints.
"""
from typing import List
from fastapi import APIRouter, Depends, status, Response, HTTPException
from sqlalchemy.orm import Session

from src.database.db import get_db
from src.tasks.service.task_service import TaskService
from src.tasks.schemas import TaskBase, TaskUpdate, TaskList, TaskLogBase
from src.auth.jwt import get_current_user
from src.auth.schemas import TokenData


router = APIRouter(
    tags=["Task"],
    prefix='/task'
)


@router.post('/', status_code=status.HTTP_201_CREATED, response_model=TaskBase)
async def create_new_task(
    request: TaskBase,
    database: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):
    """Create a new task. Only Product Owner can create tasks."""
    # Check role from JWT token
    if current_user.role != 'Product Owner' and current_user.role != 'admin':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only Product Owner can create tasks"
        )
    
    if not current_user.org_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User does not belong to an organization"
        )
    
    task_service = TaskService(database)
    result = task_service.create_task(request, current_user.id, current_user.org_id)
    return result


@router.get('/', status_code=status.HTTP_200_OK, response_model=List[TaskList])
async def task_list(
    database: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):
    """Get all tasks for current user's organization."""
    if not current_user.org_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User does not belong to an organization"
        )
    
    task_service = TaskService(database)
    tasks = task_service.get_all_tasks(current_user.org_id)
    
    # Convert to TaskList schema
    result = []
    for task in tasks:
        task_dict = {
            "id": task.id,
            "title": task.title,
            "description": task.description,
            "status": task.status,
            "owner_id": task.owner_id,
            "project_id": task.project_id,
            "createdDate": task.createdDate.date() if task.createdDate else None,
            "dueDate": task.dueDate.date() if task.dueDate else None,
            "assigned_to": task.assigned_to,
            "created_by_id": task.created_by_id,
        }
        # Add owner if available
        if task.owner:
            task_dict["owner"] = {
                "username": task.owner.username,
                "email": task.owner.email
            }
        # Add project if available
        if task.project:
            task_dict["project"] = {
                "id": task.project.id,
                "title": task.project.title
            }
        # Add assigned_to_user if available
        if task.assigned_to_user:
            task_dict["assigned_to_user"] = {
                "id": task.assigned_to_user.id,
                "username": task.assigned_to_user.username,
                "firstName": task.assigned_to_user.firstName,
                "lastName": task.assigned_to_user.lastName,
                "email": task.assigned_to_user.email
            }
        # Add created_by if available
        if task.created_by_user:
            task_dict["created_by"] = {
                "username": task.created_by_user.username,
                "firstName": task.created_by_user.firstName,
                "lastName": task.created_by_user.lastName
            }
        result.append(TaskList(**task_dict))
    
    return result


@router.get('/{task_id}', status_code=status.HTTP_200_OK, response_model=TaskList)
async def get_task_by_id(
    task_id: int,
    database: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):
    """Get task by ID with full details including assigned_to and created_by."""
    if not current_user.org_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User does not belong to an organization"
        )
    
    task_service = TaskService(database)
    # Get task with organization check
    task = task_service.repository.get_by_id_with_org_check(task_id, current_user.org_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task Not Found!"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Task does not belong to your organization"
        )
    
    # Convert to TaskList schema with all relationships
    task_dict = {
        "id": task.id,
        "title": task.title,
        "description": task.description,
        "status": task.status,
        "owner_id": task.owner_id,
        "project_id": task.project_id,
        "createdDate": task.createdDate.date() if task.createdDate else None,
        "dueDate": task.dueDate.date() if task.dueDate else None,
        "assigned_to": task.assigned_to,
        "created_by_id": task.created_by_id,
    }
    # Add owner if available
    if task.owner:
        task_dict["owner"] = {
            "username": task.owner.username,
            "email": task.owner.email
        }
    # Add project if available
    if task.project:
        task_dict["project"] = {
            "id": task.project.id,
            "title": task.project.title
        }
    # Add assigned_to_user if available
    if task.assigned_to_user:
        task_dict["assigned_to_user"] = {
            "id": task.assigned_to_user.id,
            "username": task.assigned_to_user.username,
            "firstName": task.assigned_to_user.firstName,
            "lastName": task.assigned_to_user.lastName,
            "email": task.assigned_to_user.email
        }
    # Add created_by if available
    if task.created_by_user:
        task_dict["created_by"] = {
            "username": task.created_by_user.username,
            "firstName": task.created_by_user.firstName,
            "lastName": task.created_by_user.lastName
        }
    
    return TaskList(**task_dict)


@router.delete('/{task_id}', status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
async def delete_task_by_id(
    task_id: int,
    database: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):
    """Delete task by ID. Only Product Owner can delete tasks."""
    # Check role from JWT token
    if current_user.role != 'Product Owner' and current_user.role != 'admin':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only Product Owner can delete tasks"
        )
    
    task_service = TaskService(database)
    task_service.delete_task(task_id, current_user.id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.patch('/{task_id}', status_code=status.HTTP_200_OK, response_model=TaskBase)
async def update_task_by_id(
    request: TaskUpdate,
    task_id: int,
    database: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):
    """Update task by ID. Developers can only update status, Product Owner can update all fields."""
    print(f"\n{'='*60}")
    print(f"[TASK CONTROLLER] ========== PATCH /task/{task_id} ==========")
    print(f"[TASK CONTROLLER] Request received:")
    print(f"[TASK CONTROLLER]   Task ID: {task_id}")
    print(f"[TASK CONTROLLER]   Update Data: {request.model_dump(exclude_unset=True)}")
    print(f"[TASK CONTROLLER]   Current User:")
    print(f"[TASK CONTROLLER]     ID: {current_user.id}")
    print(f"[TASK CONTROLLER]     Email: {current_user.email}")
    print(f"[TASK CONTROLLER]     Role: {current_user.role}")
    print(f"[TASK CONTROLLER]     Org ID: {current_user.org_id}")
    print(f"{'='*60}\n")
    
    if not current_user.org_id:
        print(f"[TASK CONTROLLER] ✗ User does not belong to an organization")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User does not belong to an organization"
        )
    
    task_service = TaskService(database)
    result = task_service.update_task(task_id, request, current_user.role, current_user.id, current_user.org_id)
    
    print(f"[TASK CONTROLLER] ✓ Task update completed, returning response")
    return result


@router.get('/logs', status_code=status.HTTP_200_OK, response_model=List[TaskLogBase])
async def task_log_list(
    database: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):
    """Get task logs for current user."""
    task_service = TaskService(database)
    result = task_service.get_task_logs(current_user.id)
    return result

