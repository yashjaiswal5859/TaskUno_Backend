"""
Controller (API routes) for admin endpoints.
"""
from typing import List
from fastapi import APIRouter, Depends, status, Response, HTTPException
from sqlalchemy.orm import Session

from src.database.db import get_db
from src.admin.service.admin_service import AdminService
from src.auth.jwt import get_current_user
from src.auth.schemas import TokenData, UserResponse, UserUpdate
from src.tasks.schemas import TaskBase, TaskUpdate


router = APIRouter(
    tags=['Admin'],
    prefix='/admin'
)


def check_admin(database: Session, current_user: TokenData):
    """Check if current user is admin."""
    from src.auth.models import User
    user = database.query(User).filter(User.email == current_user.email).first()
    if user.role != 'admin':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins are allowed to perform this action"
        )
    return user


@router.get('/users', response_model=List[UserResponse])
async def get_all_users(
    database: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):
    """Get all users (admin only)."""
    check_admin(database, current_user)
    admin_service = AdminService(database)
    users = admin_service.get_all_users()
    return [
        UserResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            firstName=user.firstName,
            lastName=user.lastName
        )
        for user in users
    ]


@router.get('/users/{user_id}', status_code=status.HTTP_200_OK, response_model=UserResponse)
async def get_user_by_id(
    user_id: int,
    database: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):
    """Get user by ID (admin only)."""
    check_admin(database, current_user)
    admin_service = AdminService(database)
    user = admin_service.get_user_by_id(user_id)
    return UserResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        firstName=user.firstName,
        lastName=user.lastName
    )


@router.delete('/users/{user_id}', status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
async def delete_user_by_id(
    user_id: int,
    database: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):
    """Delete user by ID (admin only)."""
    check_admin(database, current_user)
    admin_service = AdminService(database)
    admin_service.delete_user_by_id(user_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.patch('/users/{user_id}', status_code=status.HTTP_200_OK, response_model=UserResponse)
async def update_user_by_id(
    request: UserUpdate,
    user_id: int,
    database: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):
    """Update user by ID (admin only)."""
    check_admin(database, current_user)
    admin_service = AdminService(database)
    user_data = request.model_dump(exclude_unset=True)
    user = admin_service.update_user_by_id(user_id, user_data)
    return UserResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        firstName=user.firstName,
        lastName=user.lastName
    )


@router.get('/tasks', status_code=status.HTTP_200_OK, response_model=List[TaskBase])
async def get_all_tasks(
    database: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):
    """Get all tasks (admin only)."""
    check_admin(database, current_user)
    admin_service = AdminService(database)
    return admin_service.get_all_tasks()


@router.delete('/tasks/delete', status_code=status.HTTP_200_OK)
async def delete_all_tasks(
    database: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):
    """Delete all tasks (admin only)."""
    check_admin(database, current_user)
    admin_service = AdminService(database)
    return admin_service.delete_all_tasks()


@router.get('/tasks/{task_id}', status_code=status.HTTP_200_OK, response_model=TaskBase)
async def get_task_by_id(
    task_id: int,
    database: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):
    """Get task by ID (admin only)."""
    check_admin(database, current_user)
    admin_service = AdminService(database)
    return admin_service.get_task_by_id(task_id)


@router.delete('/tasks/{task_id}', status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
async def delete_task_by_id(
    task_id: int,
    database: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):
    """Delete task by ID (admin only)."""
    check_admin(database, current_user)
    admin_service = AdminService(database)
    admin_service.delete_task_by_id(task_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.patch('/tasks/{task_id}', status_code=status.HTTP_200_OK, response_model=TaskBase)
async def update_task_by_id(
    request: TaskUpdate,
    task_id: int,
    database: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):
    """Update task by ID (admin only)."""
    check_admin(database, current_user)
    admin_service = AdminService(database)
    return admin_service.update_task_by_id(task_id, request)

