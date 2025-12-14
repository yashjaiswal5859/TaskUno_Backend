"""
Database connection and session management for Supabase PostgreSQL.
"""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from src.config.settings import settings

# Create database engine for Supabase PostgreSQL
database_url = settings.DATABASE_URL

if not database_url:
    raise ValueError("DATABASE_URL is required. Make sure SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY are set in .env")

# PostgreSQL/Supabase connection args
connect_args = {
    "sslmode": "require"
}

engine = create_engine(
    database_url,
    connect_args=connect_args,
    pool_pre_ping=True,  # Verify connections before using
    pool_size=1,  # Connection pool size (reduced for Supabase 15 connection limit)
    max_overflow=2  # Max overflow connections (reduced for Supabase 15 connection limit)
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()


def get_db():
    """
    Dependency function to get database session.
    Yields a database session and closes it after use.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()



