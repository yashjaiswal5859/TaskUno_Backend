"""
Service layer for organization business logic.
"""
from typing import Optional
from sqlalchemy.orm import Session

# Import all models to ensure relationships are resolved
import src.models  # noqa: F401

from src.organization.repository import OrganizationRepository
from src.organization.models import Organization
from src.auth.models import ProductOwner, Developer


class OrganizationService:
    """Service for organization operations."""
    
    def __init__(self, db: Session):
        self.db = db
        self.repository = OrganizationRepository(db)
    
    def get_organization_by_id(self, org_id: int) -> Optional[Organization]:
        """Get organization by ID."""
        return self.repository.get_by_id(org_id)
    
    def get_organization_by_name(self, name: str) -> Optional[Organization]:
        """Get organization by name."""
        return self.repository.get_by_name(name)
    
    def get_all_organizations(self) -> list:
        """Get all organizations."""
        return self.repository.get_all()
    
    def create_organization(self, name: str) -> Organization:
        """Create a new organization."""
        return self.repository.create(name)
    
    def get_developers_by_organization(self, organization_id: int) -> list:
        """Get all developers in an organization."""
        # Get all developers directly by organization_id
        developers = self.db.query(Developer).filter(
            Developer.organization_id == organization_id
        ).all()
        
        return developers
    
    def get_product_owners_by_organization(self, organization_id: int) -> list:
        """Get all product owners in an organization."""
        # Get all Product Owners in the organization
        product_owners = self.db.query(ProductOwner).filter(
            ProductOwner.organization_id == organization_id
        ).all()
        
        return product_owners
    
    def get_organization_chart(self, organization_id: int) -> Optional[dict]:
        """Get organization chart with 3-level structure: Organization -> Product Owners -> Developers."""
        # Get organization
        org = self.repository.get_by_id(organization_id)
        if not org:
            return None
        
        # Get all Product Owners in the organization
        product_owners = self.db.query(ProductOwner).filter(
            ProductOwner.organization_id == organization_id
        ).all()
        
        # Get all Developers in the organization (not linked to specific owners)
        developers = self.db.query(Developer).filter(
            Developer.organization_id == organization_id
        ).all()
        
        # Build chart structure with 3 levels
        chart_data = {
            "organization_id": org.id,
            "organization_name": org.name,
            "product_owners": [
                {
                    "id": po.id,
                    "firstName": po.firstName,
                    "lastName": po.lastName,
                    "username": po.username,
                    "email": po.email
                }
                for po in product_owners
            ],
            "developers": [
                {
                    "id": dev.id,
                    "firstName": dev.firstName,
                    "lastName": dev.lastName,
                    "username": dev.username,
                    "email": dev.email
                }
                for dev in developers
            ]
        }
        
        return chart_data

