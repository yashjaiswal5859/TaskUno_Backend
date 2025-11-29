"""
Service layer for authentication business logic.
"""
from typing import Optional, Union
from sqlalchemy.orm import Session

# Import all models to ensure relationships are resolved
import src.models  # noqa: F401

from src.auth.models import ProductOwner, Developer, User
from src.auth.repository import AuthRepository
from src.organization.repository import OrganizationRepository
from src.auth.hashing import get_password_hash, verify_password
from src.auth.schemas import UserCreate, UserResponse, UserUpdate


class AuthService:
    """Service for authentication operations."""
    
    def __init__(self, db: Session):
        self.db = db
        self.repository = AuthRepository(db)
        self.org_repository = OrganizationRepository(db)
    
    def register_user(self, user_data: UserCreate) -> UserResponse:
        """
        Register a new user (Product Owner only).
        
        Args:
            user_data: User registration data (must include organization name or org_id)
            
        Returns:
            UserResponse with user information
            
        Raises:
            ValueError: If organization already exists or email already exists in the same organization
        """
        # Get or create organization
        if user_data.org_id:
            # Use provided org_id
            organization = self.org_repository.get_by_id(user_data.org_id)
            if not organization:
                raise ValueError("Organization not found")
        else:
            # Check if organization name already exists (case-insensitive)
            existing_org = self.org_repository.get_by_name(user_data.organization)
            if existing_org:
                raise ValueError(f"Organization '{user_data.organization}' already exists. Please ask an existing owner to invite you, or use a different organization name.")
            else:
                # Create new organization
                organization = self.org_repository.create(user_data.organization)
        
        # Check if email already exists in this organization
        if self.repository.email_exists_in_organization(user_data.email, organization.id):
            raise ValueError("User with this email already exists in this organization. Please use a different email or login with existing credentials.")
        
        # Hash password
        hashed_password = get_password_hash(user_data.password)
        
        # Only Product Owner can register
        role = "Product Owner"
        
        # Create user
        user_dict = {
            "username": user_data.username,
            "email": user_data.email,
            "password": hashed_password,
            "firstName": user_data.firstName,
            "lastName": user_data.lastName,
            "role": role,
            "organization_id": organization.id
        }
        
        new_user = self.repository.create(user_dict)
        # Determine role based on which table the user is in
        user_role = self.get_user_role(new_user)
        
        
        return UserResponse(
            id=new_user.id,
            username=new_user.username,
            email=new_user.email,
            firstName=new_user.firstName,
            lastName=new_user.lastName,
            role=user_role,
            organization_id=getattr(new_user, 'organization_id', None)
        )
    
    def authenticate_user(self, email: str, password: str, organization_id: Optional[int] = None, role: Optional[str] = None) -> Optional[Union[ProductOwner, Developer, User]]:
        """
        Authenticate a user with email, password, organization_id, and role.
        
        Args:
            email: User email
            password: User password
            organization_id: Organization ID (optional, required if role is provided)
            role: User role - "Product Owner" or "Developer" (optional)
            
        Returns:
            User object (ProductOwner or Developer) if authentication successful, None otherwise
        """
        # If organization_id and role are provided, check specific user in that org with that role
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
            # Fallback to original behavior - get any user with this email
            user = self.repository.get_by_email(email)
        
        if not user:
            return None
        
        if not verify_password(password, user.password):
            return None
        
        # If organization_id and role were provided, verify they match
        if organization_id and role:
            user_org_id = self.get_organization_id(user)
            user_role = self.get_user_role(user)
            if user_org_id != organization_id or user_role != role:
                return None
        
        return user
    
    def get_user_by_email(self, email: str) -> Optional[Union[ProductOwner, Developer, User]]:
        """Get user by email."""
        return self.repository.get_by_email(email)
    
    def get_user_by_id(self, user_id: int, role: str = None) -> Optional[Union[ProductOwner, Developer, User]]:
        """Get user by ID."""
        return self.repository.get_by_id(user_id, role)
    
    def get_all_users(self) -> list:
        """Get all users."""
        return self.repository.get_all()
    
    def email_exists_anywhere(self, email: str) -> bool:
        """Check if email exists in any table (ProductOwner, Developer, or User)."""
        return self.repository.email_exists_anywhere(email)
    
    def get_user_role(self, user) -> str:
        """Get role of a user based on which table they're in."""
        if isinstance(user, ProductOwner):
            return "Product Owner"
        elif isinstance(user, Developer):
            return "Developer"
        elif isinstance(user, User):
            # Legacy user table - check role field
            return user.role if user.role else "Product Owner"
        return "Product Owner"
    
    def get_organization_id(self, user) -> Optional[int]:
        """Get organization_id for a user."""
        if isinstance(user, ProductOwner):
            return getattr(user, 'organization_id', None)
        elif isinstance(user, Developer):
            # Developer now has organization_id directly
            return getattr(user, 'organization_id', None)
        return None
    
    def invite_user(self, invite_data, inviter_id: int, inviter_role: str) -> UserResponse:
        """
        Invite a user (Product Owner or Developer).
        
        Args:
            invite_data: InviteUserRequest with email, firstName, lastName, password, role, org_id (optional)
            inviter_id: ID of the user doing the invitation (Product Owner)
            inviter_role: Role of the inviter
            
        Returns:
            UserResponse with created user information
        """
        # Get inviter
        inviter = self.repository.get_by_id(inviter_id, inviter_role)
        if not inviter or not isinstance(inviter, ProductOwner):
            raise ValueError("Only Product Owners can invite users")
        
        # Get organization_id - use provided org_id or inviter's org_id
        if invite_data.org_id:
            org_id = invite_data.org_id
            # Verify organization exists
            org = self.org_repository.get_by_id(org_id)
            if not org:
                raise ValueError("Organization not found")
        else:
            # Use inviter's organization_id
            org_id = getattr(inviter, 'organization_id', None)
            if not org_id:
                raise ValueError("Inviter must belong to an organization")
        
        # Check if email already exists in this organization
        if self.repository.email_exists_in_organization(invite_data.email, org_id):
            raise ValueError("User with this email already exists in this organization")
        
        # Hash password
        hashed_password = get_password_hash(invite_data.password)
        username = invite_data.email.split('@')[0]
        
        if invite_data.role == "Product Owner":
            # Create Product Owner in same organization
            user_dict = {
                "username": username,
                "email": invite_data.email,
                "password": hashed_password,
                "firstName": invite_data.firstName,
                "lastName": invite_data.lastName,
                "role": "Product Owner",
                "organization_id": org_id
            }
        else:
            # Create Developer - only link to organization, NOT to owner
            # Developers link to owners only during task assignment, not during registration/invite
            user_dict = {
                "username": username,
                "email": invite_data.email,
                "password": hashed_password,
                "firstName": invite_data.firstName,
                "lastName": invite_data.lastName,
                "role": "Developer",
                "organization_id": org_id  # Developer only belongs to organization
            }
        
        new_user = self.repository.create(user_dict)
        user_role = self.get_user_role(new_user)
        
        return UserResponse(
            id=new_user.id,
            username=new_user.username,
            email=new_user.email,
            firstName=new_user.firstName,
            lastName=new_user.lastName,
            role=user_role,
            organization_id=self.get_organization_id(new_user)
        )
    def update_user_profile(self, user_id: int, user_role: str, update_data: UserUpdate) -> UserResponse:
        """Update user profile information."""
        # Get user by ID and role
        user = self.repository.get_by_id(user_id, user_role)
        if not user:
            raise ValueError("User not found")
        
        # Prepare update dictionary (exclude None values and password if not provided)
        update_dict = update_data.model_dump(exclude_unset=True, exclude_none=True)
        
        # Hash password if provided
        if "password" in update_dict and update_dict["password"]:
            update_dict["password"] = get_password_hash(update_dict["password"])
        
        # Check if email is being changed and if it already exists
        if "email" in update_dict and update_dict["email"] != user.email:
            if self.repository.email_exists_anywhere(update_dict["email"]):
                raise ValueError("Email already exists")
        
        # Update user
        updated_user = self.repository.update(user, update_dict)
        
        # Get updated user role and organization_id
        user_role_updated = self.get_user_role(updated_user)
        org_id = self.get_organization_id(updated_user)
        
        # Get organization name
        org_name = None
        if org_id:
            org = self.org_repository.get_by_id(org_id)
            if org:
                org_name = org.name
        
        return UserResponse(
            id=updated_user.id,
            username=updated_user.username,
            email=updated_user.email,
            firstName=updated_user.firstName,
            lastName=updated_user.lastName,
            role=user_role_updated,
            organization_id=org_id,
            organization_name=org_name
        )

