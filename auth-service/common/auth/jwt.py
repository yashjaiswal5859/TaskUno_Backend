"""
Shared JWT token creation and verification utilities.
Used across all microservices for consistent authentication.
"""
from datetime import datetime, timedelta
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt
from common.config.settings import settings


def create_access_token(data: dict) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: dict) -> str:
    """Create a JWT refresh token."""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, settings.JWT_REFRESH_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt


def verify_token(token: str, credentials_exception: HTTPException):
    """Verify and decode a JWT token."""
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        email: str = payload.get("sub")
        id: int = payload.get("id")
        role: str = payload.get("role")
        org_id: int = payload.get("org_id")
        if email is None or id is None:
            raise credentials_exception
        return {"email": email, "id": id, "role": role, "org_id": org_id}
    except:
        raise credentials_exception


def verify_refresh_token(token: str, credentials_exception: HTTPException):
    """Verify and decode a JWT refresh token."""
    try:
        payload = jwt.decode(token, settings.JWT_REFRESH_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        if payload.get("type") != "refresh":
            raise credentials_exception
        email: str = payload.get("sub")
        id: int = payload.get("id")
        role: str = payload.get("role")
        org_id: int = payload.get("org_id")
        if email is None or id is None:
            raise credentials_exception
        return {"email": email, "id": id, "role": role, "org_id": org_id}
    except:
        raise credentials_exception


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


def get_current_user(token: str = Depends(oauth2_scheme)):
    """Dependency function to get current authenticated user from JWT token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"Authorization": "Bearer"}
    )
    return verify_token(token, credentials_exception)

