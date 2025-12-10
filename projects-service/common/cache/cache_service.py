"""
Shared cache service for Redis operations.
"""
import json
from typing import Optional, Any
from common.cache.redis_client import get_redis_client, is_redis_available

ORG_CACHE_TTL = 1800  # 30 minutes


class CacheService:
    """Service for cache operations."""
    
    @staticmethod
    def get(key: str) -> Optional[Any]:
        """Get value from cache."""
        if not is_redis_available():
            return None
        try:
            client = get_redis_client()
            value = client.get(key)
            if value is None:
                return None
            return json.loads(value)
        except Exception as e:
            print(f"[CACHE] Redis GET error for key '{key}': {e}")
            return None
    
    @staticmethod
    def set(key: str, value: Any, ttl: int = ORG_CACHE_TTL) -> bool:
        """Set value in cache with TTL."""
        if not is_redis_available():
            return False
        try:
            client = get_redis_client()
            serialized = json.dumps(value, default=str)
            client.setex(key, ttl, serialized)
            return True
        except Exception as e:
            print(f"[CACHE] Redis SET error for key '{key}': {e}")
            return False
    
    @staticmethod
    def delete(key: str) -> bool:
        """Delete key from cache."""
        if not is_redis_available():
            return False
        try:
            client = get_redis_client()
            client.delete(key)
            return True
        except Exception as e:
            print(f"[CACHE] Redis DELETE error for key '{key}': {e}")
            return False
    
    @staticmethod
    def delete_pattern(pattern: str) -> bool:
        """Delete all keys matching pattern."""
        if not is_redis_available():
            return False
        try:
            client = get_redis_client()
            keys = client.keys(pattern)
            if keys:
                client.delete(*keys)
                print(f"[CACHE] Deleted {len(keys)} key(s) matching pattern '{pattern}'")
            return True
        except Exception as e:
            print(f"[CACHE] Redis DELETE_PATTERN error for '{pattern}': {e}")
            return False
    
    @staticmethod
    def clear_all() -> bool:
        """Clear all keys from Redis cache."""
        if not is_redis_available():
            return False
        try:
            client = get_redis_client()
            keys = client.keys("*")
            if keys:
                deleted_count = client.delete(*keys)
                print(f"[CACHE] Cleared all cache - deleted {deleted_count} key(s)")
                return True
            else:
                print("[CACHE] Cache is already empty")
                return True
        except Exception as e:
            print(f"[CACHE] Redis CLEAR_ALL error: {e}")
            return False


def invalidate_org_cache(organization_id: int):
    """Invalidate all cache entries for an organization."""
    if not is_redis_available():
        return
    
    # Delete specific keys (more efficient than pattern matching)
    keys_to_delete = [
        f"org:{organization_id}:developers",
        f"org:{organization_id}:product_owners",
        f"org:{organization_id}:chart",
        f"org:id:{organization_id}",
    ]
    
    print(f"[CACHE] Invalidating cache for organization {organization_id}...")
    deleted_count = 0
    for key in keys_to_delete:
        if CacheService.delete(key):
            deleted_count += 1
    
    # Also delete org:all cache since organization list might have changed
    CacheService.delete("org:all")
    
    print(f"[CACHE] ✅ Deleted {deleted_count} cache key(s) for organization {organization_id}")

