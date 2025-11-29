"""
Script to create all database tables directly.
"""
import sys
import os

# Add src to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.database import Base, engine
from src.auth.models import Organization, ProductOwner, Developer, User
from src.tasks.models import Task, TaskLog
from src.project.models import Project
from src.notifications.models import EmailQueue

if __name__ == "__main__":
    print("Creating all tables...")
    Base.metadata.create_all(bind=engine)
    print("All tables created successfully!")
    print("\nTables created:")
    print("  - organization")
    print("  - product_owner")
    print("  - developer")
    print("  - user (legacy)")
    print("  - project")
    print("  - task")
    print("  - task_log")
    print("  - email_queue")


