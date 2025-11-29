"""
Organization models.
"""
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship

from src.database import Base


class Organization(Base):
    """Organization model."""
    __tablename__ = "organization"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), unique=True, nullable=False)

    product_owners = relationship("ProductOwner", back_populates="organization", lazy="dynamic")

