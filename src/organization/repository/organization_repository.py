"""
Repository layer for organization database operations.
"""
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import func

# Import all models to ensure relationships are resolved
import src.models  # noqa: F401

from src.organization.models import Organization


class OrganizationRepository:
    """Repository for organization database operations."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_by_name(self, name: str) -> Optional[Organization]:
        """Get organization by name (case-insensitive)."""
        return self.db.query(Organization).filter(
            func.lower(Organization.name) == func.lower(name.strip())
        ).first()
    
    def create(self, name: str) -> Organization:
        """Create a new organization."""
        new_org = Organization(name=name.strip())
        self.db.add(new_org)
        self.db.commit()
        self.db.refresh(new_org)
        return new_org
    
    def get_by_id(self, org_id: int) -> Optional[Organization]:
        """Get organization by ID."""
        return self.db.query(Organization).filter(Organization.id == org_id).first()
    
    def get_all(self) -> list:
        """Get all organizations."""
        return self.db.query(Organization).order_by(Organization.name).all()

