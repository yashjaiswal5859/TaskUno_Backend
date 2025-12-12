"""
Controller (API routes) for organization endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from typing import List

from common.database.db import get_db
from common.auth.jwt import get_current_user
from common.middleware.rate_limiter import limiter
from src.service.organization_service import OrganizationService
from src.schemas import (
    OrganizationBase, OrganizationChartResponse, DeveloperList, ProductOwnerList
)

router = APIRouter(tags=['Organization'], prefix='/organization')


@router.get('', response_model=List[OrganizationBase])
@limiter.limit("100/minute")
async def get_all_organizations(
    request: Request,
    db: Session = Depends(get_db)
):
    """Get all organizations (public endpoint for registration)."""
    org_service = OrganizationService(db)
    organizations = org_service.get_all_organizations()
    return [OrganizationBase(id=org.id, name=org.name) for org in organizations]


@router.get('/developers', response_model=List[DeveloperList])
@limiter.limit("100/minute")
async def get_developers_by_organization(
    request: Request,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get all developers in the current user's organization."""
    try:
        org_service = OrganizationService(db)
        
        org_id = current_user.get("org_id")
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
                email=dev.email
            )
            for dev in developers
        ]
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_detail = f"Failed to get developers: {str(e)}\n{traceback.format_exc()}"
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_detail
        )


@router.get('/product-owners', response_model=List[ProductOwnerList])
@limiter.limit("100/minute")
async def get_product_owners_by_organization(
    request: Request,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get all Product Owners in the current user's organization."""
    org_service = OrganizationService(db)
    
    org_id = current_user.get("org_id")
    if not org_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User does not belong to an organization"
        )
    
    product_owners = org_service.get_product_owners_by_organization(org_id)
    
    return [
        ProductOwnerList(
            id=po.id,
            firstName=po.firstName,
            lastName=po.lastName,
            email=po.email
        )
        for po in product_owners
    ]


@router.get('/chart', response_model=OrganizationChartResponse)
@limiter.limit("100/minute")
async def get_organization_chart(
    request: Request,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get organization chart showing Product Owners and their Developers."""
    try:
        org_service = OrganizationService(db)
        
        # Get org_id from JWT token - this is the source of truth
        org_id = current_user.get("org_id")
        user_id = current_user.get("id")
        user_email = current_user.get("sub")
        
        print(f"[DEBUG] Current user ID: {user_id}, Email: {user_email}")
        print(f"[DEBUG] Organization ID from JWT token: {org_id} (type: {type(org_id)})")
        
        if not org_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User does not belong to an organization"
            )
        
        # Convert to int if it's a string
        if isinstance(org_id, str):
            try:
                org_id = int(org_id)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid organization ID format: {org_id}"
                )
        
        # Verify the user actually belongs to this organization
        # This prevents users from accessing other organizations' data
        # Import the models from the service
        from src.service.organization_service import ProductOwner, Developer
        
        user_is_po = db.query(ProductOwner).filter(
            ProductOwner.id == user_id,
            ProductOwner.organization_id == org_id
        ).first()
        user_is_dev = db.query(Developer).filter(
            Developer.id == user_id,
            Developer.organization_id == org_id
        ).first()
        
        if not user_is_po and not user_is_dev:
            print(f"[SECURITY] User {user_id} does not belong to organization {org_id}")
            # Check what organization the user actually belongs to
            actual_po = db.query(ProductOwner).filter(ProductOwner.id == user_id).first()
            actual_dev = db.query(Developer).filter(Developer.id == user_id).first()
            actual_org_id = None
            if actual_po:
                actual_org_id = actual_po.organization_id
            elif actual_dev:
                actual_org_id = actual_dev.organization_id
            
            if actual_org_id and actual_org_id != org_id:
                print(f"[SECURITY] User {user_id} belongs to organization {actual_org_id}, not {org_id}")
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"JWT token has incorrect organization ID. You belong to organization {actual_org_id}, not {org_id}"
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You do not belong to this organization"
                )
        
        print(f"[DEBUG] User {user_id} verified to belong to organization {org_id}")
        
        chart_data = org_service.get_organization_chart(org_id)
        if not chart_data:
            # Try to get organization to see if it exists
            org = org_service.repository.get_by_id(org_id)
            if not org:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Organization with ID {org_id} not found in database"
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Organization {org_id} exists but chart data could not be generated"
                )
        
        return chart_data
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_detail = f"Failed to get organization chart: {str(e)}\n{traceback.format_exc()}"
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_detail
        )

