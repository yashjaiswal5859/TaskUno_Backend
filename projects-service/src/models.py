"""
Project models.
"""
from datetime import datetime
from sqlalchemy.orm import relationship
from sqlalchemy import Column, String, ForeignKey, Text, DateTime, Integer

from common.database.db import Base


class Project(Base):
    """Project model."""
    __tablename__ = "project"

    id = Column(Integer, primary_key=True, autoincrement=True)
    createdDate = Column(DateTime, default=datetime.now)
    title = Column(String(50))
    description = Column(Text)
    # Store IDs as integers without foreign key constraints (microservices pattern)
    # Validation happens at application level by calling other services
    organization_id = Column(Integer, nullable=True)  # References organization.id in Organization Service
    created_by_id = Column(Integer, nullable=True)  # References product_owner.id or developer.id in Auth Service

