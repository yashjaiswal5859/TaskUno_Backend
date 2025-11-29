#!/usr/bin/env python3
"""
Script to delete all records from all database tables.
Run this when database schema changes to clear all data.
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.database.db import engine, Base
from sqlalchemy import text
from src.auth.models import Organization, ProductOwner, Developer, User
from src.tasks.models import Task, TaskLog
from src.project.models import Project
from src.notifications.models import EmailQueue

def clear_all_data():
    """Delete all records from all tables."""
    print("=" * 60)
    print("DELETING ALL RECORDS FROM DATABASE")
    print("=" * 60)
    
    # List of all tables in order (child tables first to respect foreign keys)
    tables = [
        "task_log",      # Child table
        "task",          # Child table
        "project",       # Child table
        "email_queue",   # Independent table
        "developer",     # Child table
        "product_owner", # Child table
        "user",          # Legacy table
        "organization",  # Parent table
    ]
    
    with engine.connect() as conn:
        # Disable foreign key checks for SQLite
        if "sqlite" in str(engine.url):
            conn.execute(text("PRAGMA foreign_keys = OFF"))
            print("\n✓ Foreign key constraints disabled (SQLite)")
        
        deleted_counts = {}
        
        for table in tables:
            try:
                # Get count before deletion
                result = conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
                count_before = result.scalar()
                
                # Delete all records
                conn.execute(text(f"DELETE FROM {table}"))
                deleted_counts[table] = count_before
                print(f"✓ Deleted {count_before} records from '{table}'")
            except Exception as e:
                print(f"✗ Error deleting from '{table}': {e}")
        
        # Re-enable foreign key checks
        if "sqlite" in str(engine.url):
            conn.execute(text("PRAGMA foreign_keys = ON"))
            print("\n✓ Foreign key constraints re-enabled")
        
        # Commit the transaction
        conn.commit()
    
    print("\n" + "=" * 60)
    print("DELETION SUMMARY")
    print("=" * 60)
    total_deleted = 0
    for table, count in deleted_counts.items():
        print(f"  {table}: {count} records")
        total_deleted += count
    print(f"\nTotal records deleted: {total_deleted}")
    print("=" * 60)
    print("✓ All data cleared successfully!")
    print("=" * 60)

if __name__ == "__main__":
    try:
        clear_all_data()
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

