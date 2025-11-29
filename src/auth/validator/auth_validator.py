"""
Validation utilities for authentication.
"""
from typing import Optional
from sqlalchemy.orm import Session

from src.auth.models import User
from src.auth.repository.auth_repository import AuthRepository


class AuthValidator:
    """Validator for authentication operations."""
    
    def __init__(self, db: Session):
        self.repository = AuthRepository(db)
    
    def validate_email_exists(self, email: str) -> Optional[User]:
        """
        Check if email already exists in database.
        
        Args:
            email: Email to check
            
        Returns:
            User object if exists, None otherwise
        """
        return self.repository.get_by_email(email)
    
    def validate_email_not_exists(self, email: str) -> bool:
        """
        Validate that email does not exist.
        
        Args:
            email: Email to validate
            
        Returns:
            True if email doesn't exist, False otherwise
        """
        user = self.repository.get_by_email(email)
        return user is None
    
    def validate_user_exists(self, user_id: int) -> Optional[User]:
        """
        Validate that user exists by ID.
        
        Args:
            user_id: User ID to validate
            
        Returns:
            User object if exists, None otherwise
        """
        return self.repository.get_by_id(user_id)

