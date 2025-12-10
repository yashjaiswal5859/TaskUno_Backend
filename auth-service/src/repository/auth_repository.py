"""
Repository layer for user database operations.
"""
from typing import Optional, Union
from sqlalchemy.orm import Session
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from src.models import ProductOwner, Developer, Organization


class OrganizationRepository:
    """Simple organization repository for auth service."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_by_name(self, name: str) -> Optional[Organization]:
        """Get organization by name (case-insensitive)."""
        from sqlalchemy import func
        return self.db.query(Organization).filter(
            func.lower(Organization.name) == func.lower(name.strip())
        ).first()
    
    def get_by_id(self, org_id: int) -> Optional[Organization]:
        """Get organization by ID."""
        return self.db.query(Organization).filter(Organization.id == org_id).first()
    
    def create(self, name: str) -> Organization:
        """Create a new organization."""
        new_org = Organization(name=name.strip())
        self.db.add(new_org)
        self.db.commit()
        self.db.refresh(new_org)
        return new_org


class AuthRepository:
    """Repository for user database operations."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_by_email(self, email: str) -> Optional[Union[ProductOwner, Developer]]:
        """Get user by email - checks ProductOwner and Developer tables."""
        try:
            product_owner = self.db.query(ProductOwner).filter(ProductOwner.email == email).first()
            if product_owner:
                return product_owner
        except Exception:
            pass
        
        try:
            developer = self.db.query(Developer).filter(Developer.email == email).first()
            if developer:
                return developer
        except Exception:
            pass
        
        return None
    
    def email_exists_in_organization(self, email: str, organization_id: int) -> bool:
        """Check if email exists in the same organization."""
        try:
            if self.db.query(ProductOwner).filter(
                ProductOwner.email == email,
                ProductOwner.organization_id == organization_id
            ).first():
                return True
        except Exception:
            pass
        
        try:
            if self.db.query(Developer).filter(
                Developer.email == email,
                Developer.organization_id == organization_id
            ).first():
                return True
        except Exception:
            pass
        
        return False
    
    def get_by_id(self, user_id: int, role: str = None) -> Optional[Union[ProductOwner, Developer]]:
        """Get user by ID."""
        if role == "Product Owner" or role == "admin":
            return self.db.query(ProductOwner).filter(ProductOwner.id == user_id).first()
        elif role == "Developer":
            return self.db.query(Developer).filter(Developer.id == user_id).first()
        else:
            product_owner = self.db.query(ProductOwner).filter(ProductOwner.id == user_id).first()
            if product_owner:
                return product_owner
            return self.db.query(Developer).filter(Developer.id == user_id).first()
    
    def create(self, user_data: dict) -> Union[ProductOwner, Developer]:
        """Create a new user."""
        from sqlalchemy.exc import OperationalError, ProgrammingError
        
        role = user_data.get("role", "Product Owner")
        
        try:
            if role == "Product Owner" or role == "admin":
                new_user = ProductOwner()
                new_user.username = user_data["username"]
                new_user.email = user_data["email"]
                new_user.password = user_data["password"]
                new_user.firstName = user_data["firstName"]
                new_user.lastName = user_data["lastName"]
                if "organization_id" in user_data:
                    new_user.organization_id = user_data["organization_id"]
                else:
                    raise ValueError("organization_id is required for ProductOwner")
                self.db.add(new_user)
                self.db.commit()
                self.db.refresh(new_user)
                return new_user
            else:
                new_user = Developer()
                new_user.username = user_data["username"]
                new_user.email = user_data["email"]
                new_user.password = user_data["password"]
                new_user.firstName = user_data["firstName"]
                new_user.lastName = user_data["lastName"]
                if "organization_id" in user_data:
                    new_user.organization_id = user_data["organization_id"]
                else:
                    raise ValueError("organization_id is required for Developer")
                self.db.add(new_user)
                self.db.commit()
                self.db.refresh(new_user)
                return new_user
        except Exception as e:
            self.db.rollback()
            raise ValueError(f"Failed to create user: {str(e)}")
    
    def update(self, user: Union[ProductOwner, Developer], user_data: dict) -> Union[ProductOwner, Developer]:
        """Update user information."""
        for key, value in user_data.items():
            if value is not None and hasattr(user, key):
                setattr(user, key, value)
        self.db.commit()
        self.db.refresh(user)
        return user

