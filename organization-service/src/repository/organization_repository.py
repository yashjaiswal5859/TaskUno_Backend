"""
Repository layer for organization database operations.
"""
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import func

from src.models import Organization
from common.cache.cache_service import CacheService
from common.cache.redis_client import is_redis_available

ORG_CACHE_TTL = 1800


class OrganizationRepository:
    """Repository for organization database operations with Redis caching."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_by_name(self, name: str) -> Optional[Organization]:
        """Get organization by name (case-insensitive) with caching."""
        cache_key = f"org:name:{name.lower().strip()}"
        
        if is_redis_available():
            print(f"[CACHE] Checking Redis for key: {cache_key}")
            cached = CacheService.get(cache_key)
            if cached:
                print(f"[CACHE] ✅ HIT - Organization '{name}' found in Redis")
                # Still query DB to get a properly attached SQLAlchemy object
                org = self.db.query(Organization).filter(Organization.id == cached['id']).first()
                if org:
                    return org
                # If cache says it exists but DB doesn't, cache is stale - clear it
                print(f"[CACHE] ⚠️  Cache hit but DB miss - clearing stale cache")
                CacheService.delete(cache_key)
        else:
            print(f"[CACHE] ⚠️  Redis not available - querying database")
        
        print(f"[DB] Querying database for organization: {name}")
        org = self.db.query(Organization).filter(
            func.lower(Organization.name) == func.lower(name.strip())
        ).first()
        
        if org and is_redis_available():
            print(f"[CACHE] Storing organization '{name}' in Redis (TTL: {ORG_CACHE_TTL}s)")
            CacheService.set(cache_key, {'id': org.id, 'name': org.name}, ttl=ORG_CACHE_TTL)
            print(f"[CACHE] ✅ Stored successfully")
        elif not org:
            print(f"[DB] Organization '{name}' not found in database")
        
        return org
    
    def create(self, name: str) -> Organization:
        """Create a new organization and invalidate cache."""
        print(f"[DB] Creating new organization: {name}")
        new_org = Organization(name=name.strip())
        self.db.add(new_org)
        self.db.commit()
        self.db.refresh(new_org)
        print(f"[DB] ✅ Organization '{name}' created with ID: {new_org.id}")
        
        if is_redis_available():
            print(f"[CACHE] Invalidating all organization cache (pattern: org:*)")
            CacheService.delete_pattern("org:*")
            print(f"[CACHE] ✅ Cache invalidated")
        
        return new_org
    
    def get_by_id(self, org_id: int) -> Optional[Organization]:
        """Get organization by ID with caching."""
        cache_key = f"org:id:{org_id}"
        
        if is_redis_available():
            print(f"[CACHE] Checking Redis for key: {cache_key}")
            cached = CacheService.get(cache_key)
            if cached:
                print(f"[CACHE] ✅ HIT - Organization ID {org_id} found in Redis")
                # Still query DB to get a properly attached SQLAlchemy object
                # Cache is used to avoid the query, but we need the real object for relationships
                org = self.db.query(Organization).filter(Organization.id == org_id).first()
                if org:
                    return org
                # If cache says it exists but DB doesn't, cache is stale - clear it
                print(f"[CACHE] ⚠️  Cache hit but DB miss - clearing stale cache")
                CacheService.delete(cache_key)
        
        print(f"[DB] Querying database for organization ID: {org_id}")
        org = self.db.query(Organization).filter(Organization.id == org_id).first()
        
        if org and is_redis_available():
            print(f"[CACHE] Storing organization ID {org_id} in Redis (TTL: {ORG_CACHE_TTL}s)")
            CacheService.set(cache_key, {'id': org.id, 'name': org.name}, ttl=ORG_CACHE_TTL)
            print(f"[CACHE] ✅ Stored successfully")
        elif not org:
            print(f"[DB] Organization ID {org_id} not found in database")
        
        return org
    
    def get_all(self) -> list:
        """Get all organizations with caching."""
        cache_key = "org:all"
        
        if is_redis_available():
            cached = CacheService.get(cache_key)
            if cached:
                print(f"[CACHE] ✅ HIT - Found {len(cached)} organizations in Redis")
                return [Organization(id=o['id'], name=o['name']) for o in cached]
            else:
                print(f"[CACHE] ❌ MISS - Key not found in Redis")
        
        print(f"[DB] Querying database for all organizations...")
        orgs = self.db.query(Organization).order_by(Organization.name).all()
        print(f"[DB] Found {len(orgs)} organizations in database")
        
        if orgs and is_redis_available():
            print(f"[CACHE] Storing {len(orgs)} organizations in Redis with TTL {ORG_CACHE_TTL}s")
            CacheService.set(cache_key, [{'id': org.id, 'name': org.name} for org in orgs], ttl=ORG_CACHE_TTL)
            print(f"[CACHE] ✅ Stored successfully")
        
        return orgs

