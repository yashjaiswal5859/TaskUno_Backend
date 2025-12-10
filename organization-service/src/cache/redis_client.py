"""
Redis connection management - Singleton pattern.
"""
from typing import Optional
from src.config.settings import settings

# Try to import redis
try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    redis = None

# Singleton Redis client instance
_redis_client: Optional[any] = None


def get_redis_client():
    """Get singleton Redis client instance."""
    global _redis_client
    return _redis_client


def is_redis_available() -> bool:
    """Check if Redis singleton is available."""
    return _redis_client is not None


def initialize_redis():
    """Initialize Redis singleton at application startup."""
    global _redis_client
    
    print("\n" + "="*50)
    print("🔧 Initializing Redis connection...")
    if not REDIS_AVAILABLE:
        print("❌ Redis Python package not installed")
        print("   Install with: pip install redis")
        print("="*50 + "\n")
        _redis_client = None
        return False
    try:
        print(f"   Connecting to Redis at {settings.REDIS_HOST}:{settings.REDIS_PORT}...")
        _redis_client = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            decode_responses=True,
            socket_connect_timeout=settings.REDIS_SOCKET_CONNECT_TIMEOUT,
            socket_timeout=settings.REDIS_SOCKET_TIMEOUT,
            retry_on_timeout=False
        )
        _redis_client.ping()
        print("✅ Redis connection successful!")
        print("="*50 + "\n")
        return True
    except Exception as e:
        _redis_client = None
        print(f"❌ Redis connection failed: {type(e).__name__}: {e}")
        print("="*50 + "\n")
        return False



