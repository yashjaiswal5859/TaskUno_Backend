"""
JWT token verification utilities (for token verification only).
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt
from src.config.settings import settings


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


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


def get_current_user(token: str = Depends(oauth2_scheme)):
    """Dependency function to get current authenticated user from JWT token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"Authorization": "Bearer"}
    )
    return verify_token(token, credentials_exception)



