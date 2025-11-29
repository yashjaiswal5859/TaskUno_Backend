"""
Password hashing utilities using bcrypt.
"""
import bcrypt


def get_password_hash(password: str) -> str:
    """
    Hash a password using bcrypt.
    
    Args:
        password: Plain text password
        
    Returns:
        Hashed password as string
    """
    password_bytes = password.encode('utf-8')
    # Use rounds=4 for faster hashing in development (default is 12)
    # In production, use rounds=12 or higher for better security
    salt = bcrypt.gensalt(rounds=4)
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against a hash.
    
    Args:
        plain_password: Plain text password to verify
        hashed_password: Hashed password to compare against
        
    Returns:
        True if password matches, False otherwise
    """
    try:
        password_bytes = plain_password.encode('utf-8')
        hashed_bytes = hashed_password.encode('utf-8')
        # bcrypt.checkpw automatically uses the rounds from the stored hash
        # This will be slower for hashes created with rounds=12, but that's expected
        return bcrypt.checkpw(password_bytes, hashed_bytes)
    except Exception:
        # If verification fails for any reason, return False
        return False

