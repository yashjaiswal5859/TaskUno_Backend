"""
Service layer for admin business logic.
"""
from typing import List
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from src.auth.models import User
from src.tasks.models import Task
from src.tasks.schemas import TaskUpdate
from src.tasks.service.task_service import TaskService
from src.auth.service.auth_service import AuthService
from src.auth.hashing import get_password_hash


class AdminService:
    """Service for admin operations."""

    def __init__(self, db: Session):
        self.db = db
        self.auth_service = AuthService(db)
        self.task_service = TaskService(db)

    def get_all_users(self) -> List[User]:
        """Get all users."""
        return self.auth_service.get_all_users()

    def get_user_by_id(self, user_id: int) -> User:
        """Get user by ID."""
        user = self.auth_service.get_user_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User Not Found!"
            )
        return user

    def delete_user_by_id(self, user_id: int) -> None:
        """Delete user by ID."""
        user = self.auth_service.get_user_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User Not Found!"
            )
        self.db.delete(user)
        self.db.commit()

    def update_user_by_id(self, user_id: int, user_data: dict) -> User:
        """Update user by ID."""
        user = self.auth_service.get_user_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User Not Found!"
            )
        for key, value in user_data.items():
            if value is not None:
                if key == "password":
                    # Hash password before storing
                    setattr(user, key, get_password_hash(value))
                else:
                    setattr(user, key, value)
        self.db.commit()
        self.db.refresh(user)
        return user

    def get_all_tasks(self) -> List[Task]:
        """Get all tasks."""
        return self.task_service.get_all_tasks_admin()

    def delete_all_tasks(self) -> dict:
        """Delete all tasks."""
        return self.task_service.delete_all_tasks()

    def get_task_by_id(self, task_id: int) -> Task:
        """Get task by ID."""
        task = self.db.query(Task).filter(Task.id == task_id).first()
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task Not Found!"
            )
        return task

    def delete_task_by_id(self, task_id: int) -> None:
        """Delete task by ID."""
        task = self.db.query(Task).filter(Task.id == task_id).first()
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task Not Found!"
            )
        self.db.delete(task)
        self.db.commit()

    def update_task_by_id(self, task_id: int, task_data: TaskUpdate) -> Task:
        """Update task by ID."""
        return self.task_service.update_task_admin(task_id, task_data, self.db)

