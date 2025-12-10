#!/usr/bin/env python3
"""
Database migration script.
Usage:
    python3 migrate.py up    # Create all tables
    python3 migrate.py down  # Drop all tables
"""

import sys
import os
import importlib.util
from pathlib import Path

# Load .env file from migrations directory before importing settings
migrations_dir = Path(__file__).parent
env_file = migrations_dir / ".env"

if env_file.exists():
    try:
        from dotenv import load_dotenv
        load_dotenv(env_file)
        print(f"✅ Loaded .env from: {env_file}")
    except ImportError:
        print("⚠️  python-dotenv not installed. Install with: pip install python-dotenv")
        print("   Trying to use environment variables directly...")
else:
    print(f"⚠️  .env file not found at: {env_file}")
    print("   Using environment variables directly...")

# Add parent directory to path
microservices_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, microservices_dir)

# Use common from auth-service (all services have same common code)
auth_service_dir = os.path.join(microservices_dir, "auth-service")
sys.path.insert(0, auth_service_dir)

from common.database.db import Base, engine
from common.database.audit_log import AuditLog
from sqlalchemy import inspect

# Import models from each service using importlib
def load_module_from_path(module_name, file_path):
    """Load a Python module from a file path."""
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

print("📦 Loading models from all services...")

# Load models from auth-service (includes Organization with relationships)
auth_models_path = os.path.join(microservices_dir, "auth-service", "src", "models.py")
auth_models = load_module_from_path("auth_models", auth_models_path)
# Organization is already defined in auth-service, skip from organization-service

# Load models from tasks-service
tasks_models_path = os.path.join(microservices_dir, "tasks-service", "src", "models.py")
tasks_models = load_module_from_path("tasks_models", tasks_models_path)

# Load models from projects-service
projects_models_path = os.path.join(microservices_dir, "projects-service", "src", "models.py")
projects_models = load_module_from_path("projects_models", projects_models_path)

print("✅ All models loaded")


def up():
    """Create all database tables."""
    print("🔨 Creating all tables...")
    Base.metadata.create_all(bind=engine)
    
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    
    print(f"✅ Created {len(tables)} table(s):")
    for table in sorted(tables):
        print(f"   ✓ {table}")
    
    # Remove created_by_id column from task table if it exists
    print("\n🔨 Removing created_by_id column from task table...")
    from sqlalchemy import text
    with engine.connect() as connection:
        try:
            # Try to drop the column (will fail silently if it doesn't exist)
            connection.execute(text("ALTER TABLE task DROP COLUMN IF EXISTS created_by_id;"))
            connection.commit()
            print("   ✅ Removed created_by_id column from task table (if it existed)")
        except Exception as e:
            # Column might not exist, which is fine
            print(f"   ℹ️  created_by_id column removal: {str(e)}")
            connection.rollback()


def down():
    """Drop all database tables."""
    print("⚠️  WARNING: This will delete ALL data!")
    response = input("Are you sure? (yes/no): ")
    
    if response.lower() not in ['yes', 'y']:
        print("❌ Cancelled.")
        return
    
    print("🗑️  Dropping all tables...")
    Base.metadata.drop_all(bind=engine)
    print("✅ All tables dropped.")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 migrate.py [up|down]")
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    if command == "up":
        up()
    elif command == "down":
        down()
    else:
        print(f"❌ Unknown command: {command}")
        print("Usage: python3 migrate.py [up|down]")
        sys.exit(1)
