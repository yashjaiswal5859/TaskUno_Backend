"""
Token blacklist for logout functionality.
"""
from datetime import datetime, timedelta
from typing import Set
import hashlib

# In-memory blacklist (simple implementation)
# For production, consider using Redis or database table
_token_blacklist: Set[str] = set()


def blacklist_token(token: str) -> None:
    """
    Add token to blacklist.
    
    Args:
        token: JWT token string to blacklist
    """
    # Hash the token to save memory
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    _token_blacklist.add(token_hash)


def is_token_blacklisted(token: str) -> bool:
    """
    Check if token is blacklisted.
    
    Args:
        token: JWT token string to check
        
    Returns:
        True if token is blacklisted, False otherwise
    """
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    return token_hash in _token_blacklist


def clear_expired_tokens() -> None:
    """
    Clear expired tokens from blacklist.
    Note: For in-memory implementation, this is a no-op.
    For database/Redis implementation, this would clean up expired entries.
    """
    # In-memory blacklist doesn't track expiration
    # Tokens are removed when server restarts
    pass


