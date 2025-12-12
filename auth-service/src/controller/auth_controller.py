"""
Controller (API routes) for authentication endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from typing import List

from common.database.db import get_db
from common.auth.jwt import create_access_token, create_refresh_token, get_current_user, verify_refresh_token
from common.middleware.rate_limiter import limiter
from src.service.auth_service import AuthService
from src.schemas import (
    UserCreate, UserResponse, UserUpdate, LoginRequest, TokenResponse, TokenData, 
    RefreshTokenRequest, InviteUserRequest
)
from src.blacklist import blacklist_token


router = APIRouter(tags=['Auth'], prefix='/auth')


@router.post('/', status_code=status.HTTP_201_CREATED)
@limiter.limit("10/minute")
async def register(
    request: Request,
    user_data: UserCreate,
    db: Session = Depends(get_db)
):
    """Register a new user and return JWT tokens."""
    auth_service = AuthService(db)
    
    if user_data.role != "Product Owner" and user_data.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only Product Owner can register. Developers must be invited by a Product Owner."
        )
    
    try:
        user = auth_service.register_user(user_data)
        user_role = user.role if user.role else "Product Owner"
        org_id = user.organization_id
        
        org_name = None
        if org_id:
            org = auth_service.org_repository.get_by_id(org_id)
            if org:
                org_name = org.name
        
        user.organization_name = org_name
        
        access_token = create_access_token(data={"sub": user.email, "id": user.id, "role": user_role, "org_id": org_id})
        refresh_token = create_refresh_token(data={"sub": user.email, "id": user.id, "role": user_role, "org_id": org_id})
        
        return {
            "tokens": TokenResponse(
                access_token=access_token,
                refresh_token=refresh_token,
                token_type="bearer"
            ),
            "user": user
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        import traceback
        error_detail = f"Registration failed: {str(e)}\n{traceback.format_exc()}"
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_detail
        )


@router.post('/login')
@limiter.limit("10/minute")
async def login(
    request: Request,
    login_data: LoginRequest,
    db: Session = Depends(get_db)
):
    """Login user and return JWT tokens."""
    auth_service = AuthService(db)
    
    user = auth_service.authenticate_user(
        login_data.email, 
        login_data.password,
        organization_id=login_data.organization_id,
        role=login_data.role
    )
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Wrong credentials or user does not exist in the specified organization with the specified role"
        )
    
    user_role = auth_service.get_user_role(user)
    org_id = auth_service.get_organization_id(user)
    
    if login_data.organization_id:
        org_id = login_data.organization_id
    
    org_name = None
    if org_id:
        org = auth_service.org_repository.get_by_id(org_id)
        if org:
            org_name = org.name
    
    access_token = create_access_token(data={"sub": user.email, "id": user.id, "role": user_role, "org_id": org_id})
    refresh_token = create_refresh_token(data={"sub": user.email, "id": user.id, "role": user_role, "org_id": org_id})
    
    user_response = UserResponse(
        id=user.id,
        email=user.email,
        firstName=user.firstName,
        lastName=user.lastName,
        role=user_role,
        organization_id=org_id,
        organization_name=org_name
    )
    
    return {
        "tokens": TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer"
        ),
        "user": user_response
    }


@router.get('/profile', response_model=UserResponse)
@limiter.limit("100/minute")
async def get_profile(
    request: Request,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get current user profile."""
    auth_service = AuthService(db)
    user = auth_service.get_user_by_email(current_user["email"])
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    user_role = auth_service.get_user_role(user)
    org_id = auth_service.get_organization_id(user)
    org_name = None
    
    if org_id:
        org = auth_service.org_repository.get_by_id(org_id)
        if org:
            org_name = org.name
    
    return UserResponse(
        id=user.id,
        email=user.email,
        firstName=user.firstName,
        lastName=user.lastName,
        role=user_role,
        organization_id=org_id,
        organization_name=org_name
    )


@router.patch('/profile', response_model=UserResponse)
@limiter.limit("30/minute")
async def update_profile(
    request: Request,
    update_data: UserUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Update current user profile."""
    auth_service = AuthService(db)
    
    try:
        updated_user = auth_service.update_user_profile(
            current_user["id"],
            current_user.get("role") or "Product Owner",
            update_data
        )
        return updated_user
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update profile: {str(e)}"
        )


@router.post('/refresh', response_model=TokenResponse)
@limiter.limit("30/minute")
async def refresh_token(
    request: Request,
    refresh_data: RefreshTokenRequest,
    db: Session = Depends(get_db)
):
    """Refresh access token using refresh token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid refresh token",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        token_data = verify_refresh_token(refresh_data.refresh_token, credentials_exception)
        auth_service = AuthService(db)
        user = auth_service.get_user_by_email(token_data["email"])
        
        if not user:
            raise credentials_exception
        
        user_role = auth_service.get_user_role(user)
        org_id = auth_service.get_organization_id(user)
        
        access_token = create_access_token(data={"sub": user.email, "id": user.id, "role": user_role, "org_id": org_id})
        refresh_token = create_refresh_token(data={"sub": user.email, "id": user.id, "role": user_role, "org_id": org_id})
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer"
        )
    except HTTPException:
        raise
    except Exception:
        raise credentials_exception


@router.post('/invite', status_code=status.HTTP_201_CREATED, response_model=UserResponse)
@limiter.limit("20/minute")
async def invite_user(
    request: Request,
    invite_data: InviteUserRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Invite a user (Product Owner or Developer)."""
    if current_user.get("role") != 'Product Owner' and current_user.get("role") != 'admin':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only Product Owner can invite users"
        )
    
    if invite_data.role not in ["Product Owner", "Developer"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Role must be either 'Product Owner' or 'Developer'"
        )
    
    auth_service = AuthService(db)
    
    try:
        user = auth_service.invite_user(invite_data, current_user["id"], current_user.get("role"))
        return user
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post('/logout', status_code=status.HTTP_200_OK)
@limiter.limit("30/minute")
async def logout(
    request: Request,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Logout user by blacklisting the current token."""
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]
        blacklist_token(token)
    
    return {"message": "Logged out successfully"}

