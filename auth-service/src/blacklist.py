"""
Token blacklist for logout functionality.
"""
from typing import Set
import hashlib

# In-memory blacklist
_token_blacklist: Set[str] = set()


def blacklist_token(token: str) -> None:
    """Add token to blacklist."""
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    _token_blacklist.add(token_hash)


def is_token_blacklisted(token: str) -> bool:
    """Check if token is blacklisted."""
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    return token_hash in _token_blacklist


def clear_expired_tokens() -> None:
    """Clear expired tokens from blacklist."""
    pass



