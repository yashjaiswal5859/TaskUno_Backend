"""
Service layer for authentication business logic.
"""
from typing import Optional, Union
from sqlalchemy.orm import Session
import sys
import os

# Add paths
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.models import ProductOwner, Developer
from src.repository.auth_repository import AuthRepository, OrganizationRepository
from src.hashing import get_password_hash, verify_password
from src.schemas import UserCreate, UserResponse, UserUpdate
from common.database.audit_service import log_audit
from common.cache.cache_service import invalidate_org_cache


class AuthService:
    """Service for authentication operations."""
    
    def __init__(self, db: Session):
        self.db = db
        self.repository = AuthRepository(db)
        self.org_repository = OrganizationRepository(db)
    
    def register_user(self, user_data: UserCreate) -> UserResponse:
        """Register a new user (Product Owner only)."""
        if user_data.org_id:
            organization = self.org_repository.get_by_id(user_data.org_id)
            if not organization:
                raise ValueError("Organization not found")
        else:
            existing_org = self.org_repository.get_by_name(user_data.organization)
            if existing_org:
                raise ValueError(f"Organization '{user_data.organization}' already exists. Please ask an existing owner to invite you, or use a different organization name.")
            else:
                # Create organization first (will log audit after user is created)
                organization = self.org_repository.create(user_data.organization)
        
        if self.repository.email_exists_in_organization(user_data.email, organization.id):
            raise ValueError("User with this email already exists in this organization. Please use a different email or login with existing credentials.")
        
        hashed_password = get_password_hash(user_data.password)
        role = "Product Owner"
        
        user_dict = {
            "email": user_data.email,
            "password": hashed_password,
            "firstName": user_data.firstName,
            "lastName": user_data.lastName,
            "role": role,
            "organization_id": organization.id
        }
        
        new_user = self.repository.create(user_dict)
        user_role = self.get_user_role(new_user)
        org_id = self.get_organization_id(new_user)
        
        # Log audit entry for organization creation (if organization was just created)
        if not user_data.org_id and organization:
            log_audit(
                db=self.db,
                employee_id=new_user.id,
                role_type=user_role,
                action="organization_created",
                organization_id=organization.id,
                resource_type="organization",
                resource_id=organization.id,
                details={
                    "name": organization.name,
                    "created_during_registration": True
                }
            )
        
        # Log audit entry for user registration
        log_audit(
            db=self.db,
            employee_id=new_user.id,
            role_type=user_role,
            action="user_registered",
            organization_id=org_id,
            resource_type="user",
            resource_id=new_user.id,
            details={
                "email": new_user.email,
                "role": user_role
            }
        )
        
        # Invalidate organization cache when new user is registered
        if org_id:
            invalidate_org_cache(org_id)
        
        return UserResponse(
            id=new_user.id,
            email=new_user.email,
            firstName=new_user.firstName,
            lastName=new_user.lastName,
            role=user_role,
            organization_id=org_id
        )
    
    def authenticate_user(self, email: str, password: str, organization_id: Optional[int] = None, role: Optional[str] = None) -> Optional[Union[ProductOwner, Developer]]:
        """Authenticate a user with email, password, organization_id, and role."""
        if organization_id and role:
            if role == "Product Owner":
                user = self.db.query(ProductOwner).filter(
                    ProductOwner.email == email,
                    ProductOwner.organization_id == organization_id
                ).first()
            elif role == "Developer":
                user = self.db.query(Developer).filter(
                    Developer.email == email,
                    Developer.organization_id == organization_id
                ).first()
            else:
                return None
        else:
            user = self.repository.get_by_email(email)
        
        if not user:
            return None
        
        if not verify_password(password, user.password):
            return None
        
        if organization_id and role:
            user_org_id = self.get_organization_id(user)
            user_role = self.get_user_role(user)
            if user_org_id != organization_id or user_role != role:
                return None
        
        return user
    
    def get_user_by_email(self, email: str) -> Optional[Union[ProductOwner, Developer]]:
        """Get user by email."""
        return self.repository.get_by_email(email)
    
    def get_user_by_id(self, user_id: int, role: str = None) -> Optional[Union[ProductOwner, Developer]]:
        """Get user by ID."""
        return self.repository.get_by_id(user_id, role)
    
    def get_all_users(self) -> list:
        """Get all users."""
        return self.repository.get_all()
    
    def get_user_role(self, user) -> str:
        """Get role of a user based on which table they're in."""
        if isinstance(user, ProductOwner):
            return "Product Owner"
        elif isinstance(user, Developer):
            return "Developer"
        return "Product Owner"
    
    def get_organization_id(self, user) -> Optional[int]:
        """Get organization_id for a user."""
        if isinstance(user, ProductOwner):
            return getattr(user, 'organization_id', None)
        elif isinstance(user, Developer):
            return getattr(user, 'organization_id', None)
        return None
    
    def invite_user(self, invite_data, inviter_id: int, inviter_role: str) -> UserResponse:
        """Invite a user (Product Owner or Developer)."""
        inviter = self.repository.get_by_id(inviter_id, inviter_role)
        if not inviter or not isinstance(inviter, ProductOwner):
            raise ValueError("Only Product Owners can invite users")
        
        if invite_data.org_id:
            org_id = invite_data.org_id
            org = self.org_repository.get_by_id(org_id)
            if not org:
                raise ValueError("Organization not found")
        else:
            org_id = getattr(inviter, 'organization_id', None)
            if not org_id:
                raise ValueError("Inviter must belong to an organization")
        
        if self.repository.email_exists_in_organization(invite_data.email, org_id):
            raise ValueError("User with this email already exists in this organization")
        
        hashed_password = get_password_hash(invite_data.password)
        
        if invite_data.role == "Product Owner":
            user_dict = {
                "email": invite_data.email,
                "password": hashed_password,
                "firstName": invite_data.firstName,
                "lastName": invite_data.lastName,
                "role": "Product Owner",
                "organization_id": org_id
            }
        else:
            user_dict = {
                "email": invite_data.email,
                "password": hashed_password,
                "firstName": invite_data.firstName,
                "lastName": invite_data.lastName,
                "role": "Developer",
                "organization_id": org_id
            }
        
        new_user = self.repository.create(user_dict)
        user_role = self.get_user_role(new_user)
        org_id = self.get_organization_id(new_user)
        
        # Invalidate organization cache when new user is invited
        if org_id:
            invalidate_org_cache(org_id)
        
        # Log audit entry for invitation
        log_audit(
            db=self.db,
            employee_id=inviter_id,
            role_type=inviter_role,
            action="user_invited",
            organization_id=org_id,
            resource_type="user",
            resource_id=new_user.id,
            details={
                "invited_email": new_user.email,
                "invited_role": user_role
            }
        )
        
        return UserResponse(
            id=new_user.id,
            email=new_user.email,
            firstName=new_user.firstName,
            lastName=new_user.lastName,
            role=user_role,
            organization_id=org_id
        )
    
    def update_user_profile(self, user_id: int, user_role: str, update_data: UserUpdate) -> UserResponse:
        """Update user profile information."""
        user = self.repository.get_by_id(user_id, user_role)
        if not user:
            raise ValueError("User not found")
        
        update_dict = update_data.model_dump(exclude_unset=True, exclude_none=True)
        
        if "password" in update_dict and update_dict["password"]:
            update_dict["password"] = get_password_hash(update_dict["password"])
        
        if "email" in update_dict and update_dict["email"] != user.email:
            # Check if email exists in same organization
            org_id = self.get_organization_id(user)
            if org_id and self.repository.email_exists_in_organization(update_dict["email"], org_id):
                raise ValueError("Email already exists in this organization")
        
        # Get old org_id before update to invalidate cache if org changes
        old_org_id = self.get_organization_id(user)
        
        updated_user = self.repository.update(user, update_dict)
        user_role_updated = self.get_user_role(updated_user)
        new_org_id = self.get_organization_id(updated_user)
        
        # Log audit entry
        log_audit(
            db=self.db,
            employee_id=user_id,
            role_type=user_role,
            action="user_profile_updated",
            organization_id=new_org_id or old_org_id,
            resource_type="user",
            resource_id=user_id,
            details={
                "changes": {k: "***" if k == "password" else v for k, v in update_dict.items()},  # Mask password
                "updated_fields": list(update_dict.keys())
            }
        )
        
        # Invalidate cache if organization changed or if user data was updated
        if old_org_id:
            invalidate_org_cache(old_org_id)
        if new_org_id and new_org_id != old_org_id:
            invalidate_org_cache(new_org_id)
        
        org_name = None
        if new_org_id:
            org = self.org_repository.get_by_id(new_org_id)
            if org:
                org_name = org.name
        
        return UserResponse(
            id=updated_user.id,
            email=updated_user.email,
            firstName=updated_user.firstName,
            lastName=updated_user.lastName,
            role=user_role_updated,
            organization_id=org_id,
            organization_name=org_name
        )

