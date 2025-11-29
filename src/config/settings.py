"""
Application configuration loaded from environment variables.
"""
from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import root_validator


class Settings(BaseSettings):
    """Application settings loaded from .env file."""
    
    # Database
    DATABASE_URL: str = "sqlite:///./scrum_master.db"
    
    # JWT - Support both naming conventions from .env
    # Accept both SECRET_KEY and JWT_SECRET_KEY
    SECRET_KEY: Optional[str] = None
    JWT_SECRET_KEY: Optional[str] = None
    REFRESH_SECRET_KEY: Optional[str] = None
    JWT_REFRESH_SECRET_KEY: Optional[str] = None
    ALGORITHM: str = "HS256"
    JWT_ALGORITHM: Optional[str] = None
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: Optional[int] = None
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: Optional[int] = None
    
    @root_validator(skip_on_failure=True)
    def validate_jwt_keys(cls, values):
        """Ensure we have secret keys from either naming convention."""
        # Map JWT_ prefixed vars to non-prefixed if needed
        if not values.get('SECRET_KEY') and values.get('JWT_SECRET_KEY'):
            values['SECRET_KEY'] = values['JWT_SECRET_KEY']
        if not values.get('REFRESH_SECRET_KEY') and values.get('JWT_REFRESH_SECRET_KEY'):
            values['REFRESH_SECRET_KEY'] = values['JWT_REFRESH_SECRET_KEY']
        if not values.get('SECRET_KEY'):
            raise ValueError("SECRET_KEY or JWT_SECRET_KEY must be set")
        if not values.get('REFRESH_SECRET_KEY'):
            raise ValueError("REFRESH_SECRET_KEY or JWT_REFRESH_SECRET_KEY must be set")
        
        # Map JWT_ prefixed algorithm/expiry if provided
        if values.get('JWT_ALGORITHM'):
            values['ALGORITHM'] = values['JWT_ALGORITHM']
        if values.get('JWT_ACCESS_TOKEN_EXPIRE_MINUTES') is not None:
            values['ACCESS_TOKEN_EXPIRE_MINUTES'] = values['JWT_ACCESS_TOKEN_EXPIRE_MINUTES']
        if values.get('JWT_REFRESH_TOKEN_EXPIRE_DAYS') is not None:
            values['REFRESH_TOKEN_EXPIRE_DAYS'] = values['JWT_REFRESH_TOKEN_EXPIRE_DAYS']
        
        return values
    
    # Aliases for backward compatibility (read from same env vars)
    @property
    def JWT_SECRET_KEY(self) -> str:
        return self.SECRET_KEY
    
    @property
    def JWT_REFRESH_SECRET_KEY(self) -> str:
        return self.REFRESH_SECRET_KEY
    
    @property
    def JWT_ALGORITHM(self) -> str:
        return self.ALGORITHM
    
    @property
    def JWT_ACCESS_TOKEN_EXPIRE_MINUTES(self) -> int:
        return self.ACCESS_TOKEN_EXPIRE_MINUTES
    
    @property
    def JWT_REFRESH_TOKEN_EXPIRE_DAYS(self) -> int:
        return self.REFRESH_TOKEN_EXPIRE_DAYS
    
    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8001
    
    # CORS
    CORS_ORIGINS: str = "http://localhost:3000"
    
    # Environment
    ENVIRONMENT: str = "development"
    
    # Redis (for Celery)
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # Email Configuration
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: int = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    SMTP_FROM_EMAIL: Optional[str] = None
    SMTP_USE_TLS: bool = True
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
        extra = "allow"  # Allow extra fields from .env file
        
        @classmethod
        def get_env_file_path(cls):
            """Get the path to .env file in backend directory."""
            import os
            backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            return os.path.join(backend_dir, ".env")


# Create settings instance
settings = Settings()


def get_cors_origins() -> List[str]:
    """Parse CORS origins from comma-separated string."""
    return [origin.strip() for origin in settings.CORS_ORIGINS.split(",")]

