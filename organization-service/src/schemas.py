"""
Pydantic schemas for organization requests and responses.
"""
from typing import List
from pydantic import BaseModel


class OrganizationBase(BaseModel):
    """Schema for organization."""
    id: int
    name: str

    class Config:
        from_attributes = True


class OrganizationCreate(BaseModel):
    """Schema for creating an organization."""
    name: str


class OrganizationUpdate(BaseModel):
    """Schema for updating an organization."""
    name: str


class DeveloperList(BaseModel):
    """Schema for developer list."""
    id: int
    firstName: str
    lastName: str
    email: str

    class Config:
        from_attributes = True


class ProductOwnerList(BaseModel):
    """Schema for product owner list."""
    id: int
    firstName: str
    lastName: str
    email: str

    class Config:
        from_attributes = True


class OrganizationChartResponse(BaseModel):
    """Schema for organization chart response."""
    organization_id: int
    organization_name: str
    product_owners: List[dict]
    developers: List[dict]

    class Config:
        from_attributes = True



