"""
Application configuration loaded from environment variables.
"""
from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import root_validator
from pydantic import ConfigDict
import os


class Settings(BaseSettings):
    """Application settings loaded from .env file."""
    
    # Database - Supabase PostgreSQL
    # Option 1: Provide DATABASE_URL directly (recommended - get from Supabase Dashboard > Settings > Database)
    DATABASE_URL: Optional[str] = None
    
    # Option 2: Build from Supabase credentials (if DATABASE_URL not provided)
    SUPABASE_URL: Optional[str] = None
    SUPABASE_DB_PASSWORD: Optional[str] = None  # Database password (NOT service role key)
    
    # JWT Configuration (for token verification)
    SECRET_KEY: str
    REFRESH_SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    @root_validator(skip_on_failure=True, pre=True)
    def validate_and_build_config(cls, values):
        """Build DATABASE_URL from Supabase credentials if not provided directly."""
        # If DATABASE_URL is provided directly, use it
        database_url = os.environ.get('DATABASE_URL') or values.get('DATABASE_URL')
        
        if not database_url:
            # Try to build from Supabase credentials
            supabase_url = os.environ.get('SUPABASE_URL') or values.get('SUPABASE_URL')
            db_password = os.environ.get('SUPABASE_DB_PASSWORD') or values.get('SUPABASE_DB_PASSWORD')
            
            if not supabase_url or not db_password:
                raise ValueError(
                    "Either DATABASE_URL must be provided, or both SUPABASE_URL and SUPABASE_DB_PASSWORD are required. "
                    "Get DATABASE_URL from Supabase Dashboard > Settings > Database > Connection string"
                )
            
            # Extract project reference from Supabase URL
            if supabase_url.startswith('https://'):
                project_ref = supabase_url.replace('https://', '').replace('.supabase.co', '').strip()
                # Build PostgreSQL connection string using database password
                database_url = f"postgresql://postgres.{project_ref}:{db_password}@db.{project_ref}.supabase.co:5432/postgres?sslmode=require"
                values['DATABASE_URL'] = database_url
                print(f"✅ Using Supabase database: {project_ref}")
            else:
                raise ValueError("SUPABASE_URL must start with https://")
        else:
            print("✅ Using provided DATABASE_URL")
        
        # Validate JWT keys
        if not values.get('SECRET_KEY'):
            raise ValueError("SECRET_KEY is required")
        if not values.get('REFRESH_SECRET_KEY'):
            raise ValueError("REFRESH_SECRET_KEY is required")
        
        return values
    
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
        return self.JWT_REFRESH_TOKEN_EXPIRE_DAYS
    
    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8004
    
    # CORS
    CORS_ORIGINS: str = "http://localhost:3000"
    
    # Environment
    ENVIRONMENT: str = "development"
    
    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="allow"
    )


# Create settings instance
settings = Settings()


def get_cors_origins() -> List[str]:
    """Parse CORS origins from comma-separated string."""
    return [origin.strip() for origin in settings.CORS_ORIGINS.split(",")]

