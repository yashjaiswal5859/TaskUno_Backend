"""
Task schemas for request/response validation.
"""
from datetime import date
from typing import Optional
from pydantic import BaseModel


class ProjectSchema(BaseModel):
    """Project schema for task relationships."""
    id: int
    title: str

    class Config:
        from_attributes = True


class TaskBase(BaseModel):
    """Base task schema."""
    id: Optional[int] = None
    title: str
    description: str
    status: str
    project_id: int
    project: Optional[ProjectSchema] = None
    dueDate: Optional[date] = None
    assigned_to: int  # Required: must assign to a developer
    reporting_to: int  # Required: must report to a product owner

    class Config:
        from_attributes = True


class TaskUpdate(BaseModel):
    """Task update schema."""
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    project_id: Optional[int] = None
    dueDate: Optional[date] = None
    assigned_to: Optional[int] = None
    reporting_to: Optional[int] = None
    status_change_reason: Optional[str] = None

    class Config:
        from_attributes = True


class UserSchema(BaseModel):
    """User schema for task relationships."""
    username: str
    email: str

    class Config:
        from_attributes = True


class CreatedBySchema(BaseModel):
    """Schema for created_by information."""
    id: int
    username: str
    firstName: Optional[str] = None
    lastName: Optional[str] = None
    email: str

    class Config:
        from_attributes = True


class AssignedToSchema(BaseModel):
    """Schema for assigned_to developer information."""
    id: int
    username: str
    firstName: Optional[str] = None
    lastName: Optional[str] = None
    email: str

    class Config:
        from_attributes = True


class ReportingToSchema(BaseModel):
    """Schema for reporting_to product owner information."""
    id: int
    username: str
    firstName: Optional[str] = None
    lastName: Optional[str] = None
    email: str

    class Config:
        from_attributes = True


class TaskList(BaseModel):
    """Task list schema."""
    id: int
    title: str
    description: str
    status: str
    project_id: int
    project: Optional[ProjectSchema] = None
    createdDate: Optional[date] = None
    dueDate: Optional[date] = None
    assigned_to: Optional[int] = None
    assigned_to_user: Optional[AssignedToSchema] = None
    reporting_to: Optional[int] = None
    reporting_to_user: Optional[ReportingToSchema] = None

    class Config:
        from_attributes = True


class TaskLogBase(BaseModel):
    """Task log schema."""
    id: int
    createdDate: date
    task_id: int
    reason: Optional[str] = None
    old_status: Optional[str] = None
    new_status: Optional[str] = None
    task: Optional[TaskBase] = None

    class Config:
        from_attributes = True


