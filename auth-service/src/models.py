"""
User models for authentication.
"""
from sqlalchemy import Column, Integer, String, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship

from common.database.db import Base


# Organization model (shared across services via same database)
class Organization(Base):
    """Organization model."""
    __tablename__ = "organization"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), unique=True, nullable=False)

    product_owners = relationship("ProductOwner", back_populates="organization", lazy="dynamic")


class ProductOwner(Base):
    """Product Owner model."""
    __tablename__ = "product_owner"

    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(255))
    firstName = Column(String(50))
    lastName = Column(String(50))
    password = Column(String(255))
    organization_id = Column(Integer, ForeignKey("organization.id", ondelete="SET NULL"), nullable=False)

    organization = relationship("Organization", back_populates="product_owners", lazy="joined")
    
    __table_args__ = (
        UniqueConstraint('email', 'organization_id', name='uq_product_owner_email_org'),
    )

    def check_password(self, password: str) -> bool:
        """Check if provided password matches the user's password."""
        from src.hashing import verify_password
        return verify_password(password, self.password)


class Developer(Base):
    """Developer model."""
    __tablename__ = "developer"

    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(255))
    firstName = Column(String(50))
    lastName = Column(String(50))
    password = Column(String(255))
    organization_id = Column(Integer, ForeignKey("organization.id", ondelete="SET NULL"), nullable=False)

    organization = relationship("Organization", lazy="joined")
    
    __table_args__ = (
        UniqueConstraint('email', 'organization_id', name='uq_developer_email_org'),
    )

    def check_password(self, password: str) -> bool:
        """Check if provided password matches the user's password."""
        from src.hashing import verify_password
        return verify_password(password, self.password)


# User model removed - use ProductOwner or Developer instead

