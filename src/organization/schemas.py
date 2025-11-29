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


class OrganizationChartResponse(BaseModel):
    """Schema for organization chart response - 3 level structure."""
    organization_id: int
    organization_name: str
    product_owners: List[dict]  # List of all Product Owners in organization
    developers: List[dict]  # List of all Developers in organization

    class Config:
        from_attributes = True

