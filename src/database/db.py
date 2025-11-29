"""
Database connection and session management.
"""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

from src.config import settings

# Create database engine
# For SQLite, ensure database file is in backend directory
database_url = settings.DATABASE_URL
if "sqlite" in database_url and not database_url.startswith("sqlite:///"):
    import os
    backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    db_file = database_url.replace("sqlite:///", "")
    if not os.path.isabs(db_file):
        database_url = f"sqlite:///{os.path.join(backend_dir, db_file)}"

engine = create_engine(
    database_url,
    connect_args={"check_same_thread": False} if "sqlite" in database_url else {}
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

