"""
Settings for email service.
"""
import os
from pathlib import Path
from pydantic_settings import BaseSettings
from typing import Optional
from dotenv import load_dotenv

# Load .env file from email-service directory
# Path: common/config/settings.py -> common/config/ -> common/ -> email-service/ -> .env
env_path = Path(__file__).parent.parent.parent / ".env"
if env_path.exists():
    load_dotenv(env_path)
    print(f"✅ Loaded .env from: {env_path}")
else:
    # Also try loading from current directory
    load_dotenv()
    if Path(".env").exists():
        print(f"✅ Loaded .env from current directory")
    else:
        print("⚠️  .env file not found, using environment variables or defaults")


class Settings(BaseSettings):
    """Application settings."""
    
    # Server Configuration
    HOST: str = "0.0.0.0"
    PORT: int = 8005
    
    # Redis Configuration
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    
    # Email Configuration (SMTP)
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: int = 587
    SMTP_USER: Optional[str] = None  # Sender email
    SMTP_PASSWORD: Optional[str] = None  # Sender password
    SMTP_FROM_EMAIL: Optional[str] = None  # From email (defaults to SMTP_USER if not set)
    SMTP_USE_TLS: bool = True
    
    # Queue Configuration
    QUEUE_NAME: str = "task-events-queue"
    QUEUE_BLOCKING_TIMEOUT: int = 5  # seconds
    
    # CORS Configuration (Optional)
    CORS_ORIGINS: str = "http://localhost:3000"
    
    # Environment Configuration (Optional)
    ENVIRONMENT: str = "development"
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        # Allow extra fields from .env file (optional fields)
        extra = "ignore"  # This will ignore extra fields instead of raising errors
    
    @property
    def sender_email(self) -> Optional[str]:
        """Get sender email (SMTP_FROM_EMAIL or SMTP_USER)."""
        return self.SMTP_FROM_EMAIL or self.SMTP_USER


settings = Settings()

