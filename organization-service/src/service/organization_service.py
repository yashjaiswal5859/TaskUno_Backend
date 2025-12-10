"""
Service layer for organization business logic.
"""
from typing import Optional
from sqlalchemy.orm import Session

from src.models import Organization
from src.repository.organization_repository import OrganizationRepository
from common.cache.cache_service import CacheService
from common.cache.redis_client import is_redis_available
from common.database.audit_service import log_audit

# Minimal user models for querying (shared database)
# Note: These are read-only models for querying users from Auth Service's tables
# No foreign key constraints in microservices architecture
from sqlalchemy import Column, Integer, String
from common.database.db import Base

class ProductOwner(Base):
    """Product Owner model (for querying existing product owners)."""
    __tablename__ = "product_owner"
    __table_args__ = {'extend_existing': True}  # Allow redefinition if needed
    id = Column(Integer, primary_key=True)
    username = Column(String(50))
    email = Column(String(255))
    firstName = Column(String(50))
    lastName = Column(String(50))
    password = Column(String(255))  # Include for table structure match, but won't be used
    organization_id = Column(Integer, nullable=True)  # No FK constraint - microservices pattern

class Developer(Base):
    """Developer model (for querying existing developers)."""
    __tablename__ = "developer"
    __table_args__ = {'extend_existing': True}  # Allow redefinition if needed
    id = Column(Integer, primary_key=True)
    username = Column(String(50))
    email = Column(String(255))
    firstName = Column(String(50))
    lastName = Column(String(50))
    password = Column(String(255))  # Include for table structure match, but won't be used
    organization_id = Column(Integer, nullable=True)  # No FK constraint - microservices pattern

ORG_CACHE_TTL = 1800
USER_LIST_CACHE_TTL = 1800
CHART_CACHE_TTL = 1800


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
    
    def create_organization(self, name: str, creator_id: int = None, creator_role: str = None) -> Organization:
        """Create a new organization."""
        new_org = self.repository.create(name)
        
        # Log audit entry if creator information is provided
        if creator_id and creator_role:
            log_audit(
                db=self.db,
                employee_id=creator_id,
                role_type=creator_role,
                action="organization_created",
                organization_id=new_org.id,
                resource_type="organization",
                resource_id=new_org.id,
                details={
                    "name": new_org.name
                }
            )
        
        return new_org
    
    def get_developers_by_organization(self, organization_id: int) -> list:
        """Get all developers in an organization with caching."""
        cache_key = f"org:{organization_id}:developers"
        
        if is_redis_available():
            print(f"[CACHE] Checking Redis for key: {cache_key}")
            cached = CacheService.get(cache_key)
            if cached:
                print(f"[CACHE] ✅ HIT - Found {len(cached)} developers in Redis for org {organization_id}")
                return [
                    Developer(
                        id=d['id'],
                        firstName=d.get('firstName'),
                        lastName=d.get('lastName'),
                        username=d['username'],
                        email=d['email'],
                        organization_id=organization_id
                    )
                    for d in cached
                ]
            else:
                print(f"[CACHE] ❌ MISS - Developers not in Redis for org {organization_id}")
        else:
            print(f"[CACHE] ⚠️  Redis not available - querying database")
        
        print(f"[DB] Querying database for developers in organization {organization_id}")
        developers = self.db.query(Developer).filter(
            Developer.organization_id == organization_id
        ).all()
        print(f"[DB] Found {len(developers)} developers in database")
        
        if developers and is_redis_available():
            print(f"[CACHE] Storing {len(developers)} developers in Redis (TTL: {USER_LIST_CACHE_TTL}s)")
            CacheService.set(cache_key, [
                {
                    'id': dev.id,
                    'firstName': dev.firstName,
                    'lastName': dev.lastName,
                    'username': dev.username,
                    'email': dev.email
                }
                for dev in developers
            ], ttl=USER_LIST_CACHE_TTL)
            print(f"[CACHE] ✅ Stored successfully")
        
        return developers
    
    def get_product_owners_by_organization(self, organization_id: int) -> list:
        """Get all product owners in an organization with caching."""
        cache_key = f"org:{organization_id}:product_owners"
        
        if is_redis_available():
            print(f"[CACHE] Checking Redis for key: {cache_key}")
            cached = CacheService.get(cache_key)
            if cached:
                print(f"[CACHE] ✅ HIT - Found {len(cached)} product owners in Redis for org {organization_id}")
                return [
                    ProductOwner(
                        id=po['id'],
                        firstName=po.get('firstName'),
                        lastName=po.get('lastName'),
                        username=po['username'],
                        email=po['email'],
                        organization_id=organization_id
                    )
                    for po in cached
                ]
            else:
                print(f"[CACHE] ❌ MISS - Product owners not in Redis for org {organization_id}")
        else:
            print(f"[CACHE] ⚠️  Redis not available - querying database")
        
        print(f"[DB] Querying database for product owners in organization {organization_id}")
        product_owners = self.db.query(ProductOwner).filter(
            ProductOwner.organization_id == organization_id
        ).all()
        print(f"[DB] Found {len(product_owners)} product owners in database")
        
        if product_owners and is_redis_available():
            print(f"[CACHE] Storing {len(product_owners)} product owners in Redis (TTL: {USER_LIST_CACHE_TTL}s)")
            CacheService.set(cache_key, [
                {
                    'id': po.id,
                    'firstName': po.firstName,
                    'lastName': po.lastName,
                    'username': po.username,
                    'email': po.email
                }
                for po in product_owners
            ], ttl=USER_LIST_CACHE_TTL)
            print(f"[CACHE] ✅ Stored successfully")
        
        return product_owners
    
    def get_organization_chart(self, organization_id: int) -> Optional[dict]:
        """Get organization chart with 3-level structure."""
        cache_key = f"org:{organization_id}:chart"
        
        if is_redis_available():
            print(f"[CACHE] Checking Redis for key: {cache_key}")
            cached = CacheService.get(cache_key)
            if cached:
                print(f"[CACHE] ✅ HIT - Organization chart found in Redis for org {organization_id}")
                return cached
            else:
                print(f"[CACHE] ❌ MISS - Organization chart not in Redis for org {organization_id}")
        else:
            print(f"[CACHE] ⚠️  Redis not available - querying database")
        
        print(f"[DB] Querying database for organization chart (org {organization_id})")
        org = self.repository.get_by_id(organization_id)
        if not org:
            print(f"[DB] Organization {organization_id} not found")
            return None
        
        product_owners = self.db.query(ProductOwner).filter(
            ProductOwner.organization_id == organization_id
        ).all()
        
        developers = self.db.query(Developer).filter(
            Developer.organization_id == organization_id
        ).all()
        
        print(f"[DB] Found {len(product_owners)} product owners and {len(developers)} developers")
        
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
        
        if is_redis_available():
            print(f"[CACHE] Storing organization chart in Redis (TTL: {CHART_CACHE_TTL}s)")
            CacheService.set(cache_key, chart_data, ttl=CHART_CACHE_TTL)
            print(f"[CACHE] ✅ Stored successfully")
        
        return chart_data
    
    def get_developer_by_id(self, developer_id: int, organization_id: int) -> Optional[Developer]:
        """Get developer by ID from cache or database."""
        if is_redis_available():
            cache_key = f"org:{organization_id}:developers"
            print(f"[CACHE] Checking Redis for developer ID {developer_id} in org {organization_id}")
            cached = CacheService.get(cache_key)
            if cached:
                for dev_data in cached:
                    if dev_data['id'] == developer_id:
                        print(f"[CACHE] ✅ HIT - Developer ID {developer_id} found in Redis cache")
                        return Developer(
                            id=dev_data['id'],
                            firstName=dev_data.get('firstName'),
                            lastName=dev_data.get('lastName'),
                            username=dev_data['username'],
                            email=dev_data['email'],
                            organization_id=organization_id
                        )
        
        print(f"[DB] Querying database for developer ID {developer_id} in org {organization_id}")
        developer = self.db.query(Developer).filter(
            Developer.id == developer_id,
            Developer.organization_id == organization_id
        ).first()
        
        return developer
    
    def get_product_owner_by_id(self, po_id: int, organization_id: int) -> Optional[ProductOwner]:
        """Get product owner by ID from cache or database."""
        if is_redis_available():
            cache_key = f"org:{organization_id}:product_owners"
            print(f"[CACHE] Checking Redis for product owner ID {po_id} in org {organization_id}")
            cached = CacheService.get(cache_key)
            if cached:
                for po_data in cached:
                    if po_data['id'] == po_id:
                        print(f"[CACHE] ✅ HIT - Product Owner ID {po_id} found in Redis cache")
                        return ProductOwner(
                            id=po_data['id'],
                            firstName=po_data.get('firstName'),
                            lastName=po_data.get('lastName'),
                            username=po_data['username'],
                            email=po_data['email'],
                            organization_id=organization_id
                        )
        
        print(f"[DB] Querying database for product owner ID {po_id} in org {organization_id}")
        product_owner = self.db.query(ProductOwner).filter(
            ProductOwner.id == po_id,
            ProductOwner.organization_id == organization_id
        ).first()
        
        return product_owner

