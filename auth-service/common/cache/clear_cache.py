"""
Utility to clear all Redis cache.
"""
from common.cache.redis_client import get_redis_client, is_redis_available


def clear_all_cache():
    """Clear all keys from Redis cache."""
    if not is_redis_available():
        print("❌ Redis is not available")
        return False
    
    try:
        client = get_redis_client()
        # Get all keys
        keys = client.keys("*")
        
        if not keys:
            print("✅ Cache is already empty")
            return True
        
        # Delete all keys
        deleted_count = client.delete(*keys)
        print(f"✅ Deleted {deleted_count} cache key(s)")
        return True
    except Exception as e:
        print(f"❌ Error clearing cache: {e}")
        return False


if __name__ == "__main__":
    print("🧹 Clearing all Redis cache...")
    clear_all_cache()

