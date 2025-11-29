"""
Project schemas for request/response validation.
"""
from datetime import date
from typing import Optional
from pydantic import BaseModel, EmailStr


class UserSchema(BaseModel):
    """User schema for project relationships."""
    username: str
    email: EmailStr

    class Config:
        from_attributes = True


class ProjectBase(BaseModel):
    """Base project schema."""
    id: Optional[int] = None
    title: str
    description: str
    created_by_id: Optional[int] = None
    created_by_type: Optional[str] = None

    class Config:
        from_attributes = True


class ProjectUpdate(BaseModel):
    """Project update schema."""
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None

    class Config:
        from_attributes = True


class CreatedBySchema(BaseModel):
    """Schema for created_by information."""
    username: str
    firstName: Optional[str] = None
    lastName: Optional[str] = None

    class Config:
        from_attributes = True


class ProjectList(BaseModel):
    """Project list schema."""
    id: int
    title: str
    description: str
    owner_id: int
    owner: Optional[UserSchema] = None
    createdDate: date
    created_by_id: Optional[int] = None
    created_by: Optional[CreatedBySchema] = None

    class Config:
        from_attributes = True

