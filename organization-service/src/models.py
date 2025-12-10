"""
Organization models.
"""
from sqlalchemy import Column, Integer, String

from common.database.db import Base


class Organization(Base):
    """Organization model."""
    __tablename__ = "organization"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), unique=True, nullable=False)

    # No relationships to models in other services (microservices pattern)
    # ProductOwners and Developers are managed by Auth Service, accessed via queries

