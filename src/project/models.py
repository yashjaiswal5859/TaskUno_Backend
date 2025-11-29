"""
Project models.
"""
from datetime import datetime
from sqlalchemy.orm import relationship
from sqlalchemy import Column, String, ForeignKey, Text, DateTime, Integer

from src.database import Base


class Project(Base):
    """Project model."""
    __tablename__ = "project"

    id = Column(Integer, primary_key=True, autoincrement=True)
    createdDate = Column(DateTime, default=datetime.now)
    title = Column(String(50))
    description = Column(Text)
    owner_id = Column(Integer, ForeignKey("product_owner.id", ondelete="CASCADE"))
    organization_id = Column(Integer, ForeignKey("organization.id", ondelete="CASCADE"), nullable=True)
    created_by_id = Column(Integer, ForeignKey("product_owner.id", ondelete="SET NULL"), nullable=True)
    created_by_type = Column(String(50), default='product_owner')

    owner = relationship("ProductOwner", foreign_keys=[owner_id], lazy="joined")
    organization = relationship("Organization", lazy="joined")
    created_by = relationship("ProductOwner", foreign_keys=[created_by_id], lazy="joined")
    tasks = relationship("Task", back_populates="project", lazy="dynamic")

