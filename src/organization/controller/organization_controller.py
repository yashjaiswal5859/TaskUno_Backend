"""
Controller (API routes) for organization endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from src.database.db import get_db
from src.organization.service import OrganizationService
from src.organization.schemas import (
    OrganizationBase, OrganizationChartResponse
)
from src.auth.jwt import get_current_user, TokenData
from src.auth.schemas import DeveloperList, ProductOwnerList

router = APIRouter(tags=['Organization'], prefix='/organization')


@router.get('', response_model=List[OrganizationBase])
async def get_all_organizations(
    db: Session = Depends(get_db)
):
    """
    Get all organizations (public endpoint for registration).
    
    Returns:
        List of all organizations
    """
    org_service = OrganizationService(db)
    organizations = org_service.get_all_organizations()
    return [OrganizationBase(id=org.id, name=org.name) for org in organizations]


@router.get('/developers', response_model=List[DeveloperList])
async def get_developers_by_organization(
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):
    """
    Get all developers in the current user's organization.
    Used for task assignment dropdown.
    
    Returns:
        List of developers
    """
    org_service = OrganizationService(db)
    
    # Get user's organization_id
    org_id = current_user.org_id
    if not org_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User does not belong to an organization"
        )
    
    developers = org_service.get_developers_by_organization(org_id)
    
    return [
        DeveloperList(
            id=dev.id,
            firstName=dev.firstName,
            lastName=dev.lastName,
            username=dev.username,
            email=dev.email
        )
        for dev in developers
    ]


@router.get('/product-owners', response_model=List[ProductOwnerList])
async def get_product_owners_by_organization(
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):
    """
    Get all Product Owners in the current user's organization.
    Used for task created_by dropdown.
    
    Returns:
        List of Product Owners
    """
    org_service = OrganizationService(db)
    
    # Get user's organization_id
    org_id = current_user.org_id
    if not org_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User does not belong to an organization"
        )
    
    # Get all Product Owners in the organization
    product_owners = org_service.get_product_owners_by_organization(org_id)
    
    return [
        ProductOwnerList(
            id=po.id,
            firstName=po.firstName,
            lastName=po.lastName,
            username=po.username,
            email=po.email
        )
        for po in product_owners
    ]


@router.get('/chart', response_model=OrganizationChartResponse)
async def get_organization_chart(
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):
    """
    Get organization chart showing Product Owners and their Developers.
    
    Returns:
        Organization chart with hierarchy
    """
    org_service = OrganizationService(db)
    
    # Get user's organization_id
    org_id = current_user.org_id
    if not org_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User does not belong to an organization"
        )
    
    chart_data = org_service.get_organization_chart(org_id)
    if not chart_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found"
        )
    
    return chart_data

