"""
Pydantic schemas for authentication requests and responses.
"""
from typing import Optional, List
from pydantic import BaseModel, EmailStr


class UserCreate(BaseModel):
    """Schema for user registration."""
    username: str
    email: EmailStr
    firstName: str
    lastName: str
    password: str
    role: Optional[str] = "Product Owner"
    organization: str
    org_id: Optional[int] = None


class UserResponse(BaseModel):
    """Schema for user response."""
    id: int
    username: str
    email: str
    firstName: Optional[str]
    lastName: Optional[str]
    role: Optional[str] = None
    organization_id: Optional[int] = None
    organization_name: Optional[str] = None

    class Config:
        from_attributes = True


class UserUpdate(BaseModel):
    """Schema for user update."""
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    firstName: Optional[str] = None
    lastName: Optional[str] = None
    password: Optional[str] = None


class LoginRequest(BaseModel):
    """Schema for login request."""
    email: str
    password: str
    organization_id: Optional[int] = None
    role: Optional[str] = None


class TokenResponse(BaseModel):
    """Schema for token response."""
    access_token: str
    refresh_token: str
    token_type: str


class TokenData(BaseModel):
    """Schema for token data."""
    email: Optional[str] = None
    id: Optional[int] = None
    role: Optional[str] = None
    org_id: Optional[int] = None


class RefreshTokenRequest(BaseModel):
    """Schema for refresh token request."""
    refresh_token: str


class InviteUserRequest(BaseModel):
    """Schema for inviting a user."""
    email: EmailStr
    firstName: str
    lastName: str
    password: str
    role: str
    org_id: Optional[int] = None


class DeveloperList(BaseModel):
    """Schema for developer list."""
    id: int
    firstName: Optional[str]
    lastName: Optional[str]
    username: str
    email: str

    class Config:
        from_attributes = True


class ProductOwnerList(BaseModel):
    """Schema for product owner list."""
    id: int
    firstName: Optional[str]
    lastName: Optional[str]
    username: str
    email: str

    class Config:
        from_attributes = True



