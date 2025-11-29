"""
Repository layer for user database operations.
"""
from typing import Optional, Union
from sqlalchemy.orm import Session

from src.auth.models import ProductOwner, Developer, User


class AuthRepository:
    """Repository for user database operations."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_by_email(self, email: str) -> Optional[Union[ProductOwner, Developer, User]]:
        """Get user by email - checks ProductOwner, Developer, and legacy User tables."""
        # Check ProductOwner first
        try:
            product_owner = self.db.query(ProductOwner).filter(ProductOwner.email == email).first()
            if product_owner:
                return product_owner
        except Exception:
            pass
        
        # Check Developer
        try:
            developer = self.db.query(Developer).filter(Developer.email == email).first()
            if developer:
                return developer
        except Exception:
            pass
        
        # Check legacy User table for backward compatibility
        try:
            user = self.db.query(User).filter(User.email == email).first()
            if user:
                return user
        except Exception:
            pass
        
        return None
    
    def email_exists_in_organization(self, email: str, organization_id: int) -> bool:
        """Check if email exists in the same organization (ProductOwner or Developer)."""
        # Check ProductOwner in the same organization
        try:
            if self.db.query(ProductOwner).filter(
                ProductOwner.email == email,
                ProductOwner.organization_id == organization_id
            ).first():
                return True
        except Exception:
            pass
        
        # Check Developer in the same organization
        try:
            if self.db.query(Developer).filter(
                Developer.email == email,
                Developer.organization_id == organization_id
            ).first():
                return True
        except Exception:
            pass
        
        return False
    
    def email_exists_anywhere(self, email: str) -> bool:
        """Check if email exists in ANY table (ProductOwner, Developer, or User) - legacy method."""
        # Check ProductOwner
        try:
            if self.db.query(ProductOwner).filter(ProductOwner.email == email).first():
                return True
        except Exception:
            pass
        
        # Check Developer
        try:
            if self.db.query(Developer).filter(Developer.email == email).first():
                return True
        except Exception:
            pass
        
        # Check User table
        try:
            if self.db.query(User).filter(User.email == email).first():
                return True
        except Exception:
            pass
        
        return False
    
    def get_by_id(self, user_id: int, role: str = None) -> Optional[Union[ProductOwner, Developer]]:
        """Get user by ID - checks both tables or specific role."""
        if role == "Product Owner" or role == "admin":
            return self.db.query(ProductOwner).filter(ProductOwner.id == user_id).first()
        elif role == "Developer":
            return self.db.query(Developer).filter(Developer.id == user_id).first()
        else:
            # Try both
            product_owner = self.db.query(ProductOwner).filter(ProductOwner.id == user_id).first()
            if product_owner:
                return product_owner
            return self.db.query(Developer).filter(Developer.id == user_id).first()
    
    def get_all(self) -> list:
        """Get all users from both tables."""
        product_owners = self.db.query(ProductOwner).all()
        developers = self.db.query(Developer).all()
        return list(product_owners) + list(developers)
    
    def create(self, user_data: dict) -> Union[ProductOwner, Developer, User]:
        """Create a new user."""
        """Create a new user."""
        from src.auth.models import ProductOwner, Developer
        from sqlalchemy.exc import OperationalError, ProgrammingError
        
        role = user_data.get("role", "Product Owner")
        
        try:
            if role == "Product Owner" or role == "admin":
                # Try to create ProductOwner
                try:
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
                except (OperationalError, ProgrammingError) as e:
                    # Table doesn't exist - fallback to User table
                    self.db.rollback()
                    # Create in legacy User table (without inviter_id)
                    new_user = User()
                    new_user.username = user_data["username"]
                    new_user.email = user_data["email"]
                    new_user.password = user_data["password"]
                    new_user.firstName = user_data["firstName"]
                    new_user.lastName = user_data["lastName"]
                    new_user.role = "Product Owner"
                    # Don't set inviter_id for User table fallback
                    self.db.add(new_user)
                    try:
                        self.db.commit()
                    except Exception as commit_error:
                        # If commit fails, it might be due to missing columns
                        self.db.rollback()
                        raise ValueError(f"Failed to create user in database. Please run migrations: {str(commit_error)}")
                    self.db.refresh(new_user)
                    return new_user
            else:
                # Try to create Developer
                try:
                    new_user = Developer()
                    new_user.username = user_data["username"]
                    new_user.email = user_data["email"]
                    new_user.password = user_data["password"]
                    new_user.firstName = user_data["firstName"]
                    new_user.lastName = user_data["lastName"]
                    new_user.owner_id = user_data.get("owner_id") or user_data.get("inviter_id")
                    if "organization_id" in user_data:
                        new_user.organization_id = user_data["organization_id"]
                    else:
                        raise ValueError("organization_id is required for Developer")
                    self.db.add(new_user)
                    self.db.commit()
                    self.db.refresh(new_user)
                    return new_user
                except (OperationalError, ProgrammingError) as e:
                    # Table doesn't exist - fallback to User table
                    self.db.rollback()
                    # Create in legacy User table (without inviter_id)
                    new_user = User()
                    new_user.username = user_data["username"]
                    new_user.email = user_data["email"]
                    new_user.password = user_data["password"]
                    new_user.firstName = user_data["firstName"]
                    new_user.lastName = user_data["lastName"]
                    new_user.role = "Developer"
                    # Don't set inviter_id for User table fallback
                    self.db.add(new_user)
                    try:
                        self.db.commit()
                    except Exception as commit_error:
                        # If commit fails, it might be due to missing columns
                        self.db.rollback()
                        raise ValueError(f"Failed to create user in database. Please run migrations: {str(commit_error)}")
                    self.db.refresh(new_user)
                    return new_user
        except Exception as e:
            self.db.rollback()
            raise ValueError(f"Failed to create user: {str(e)}")
    
    def update(self, user: Union[ProductOwner, Developer, User], user_data: dict) -> Union[ProductOwner, Developer, User]:
        """Update user information (works for ProductOwner, Developer, or User)."""
        for key, value in user_data.items():
            if value is not None and hasattr(user, key):
                setattr(user, key, value)
        self.db.commit()
        self.db.refresh(user)
        return user
    
    def delete(self, user: User) -> None:
        """Delete a user."""
        self.db.delete(user)
        self.db.commit()

