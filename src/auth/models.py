"""
User models for authentication.
"""
from sqlalchemy import Column, Integer, String, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship

from src.database import Base

# Import Organization from organization module
from src.organization.models import Organization


class ProductOwner(Base):
    """Product Owner model."""
    __tablename__ = "product_owner"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50))
    email = Column(String(255))  # Removed unique constraint - now unique per organization
    firstName = Column(String(50))
    lastName = Column(String(50))
    password = Column(String(255))
    organization_id = Column(Integer, ForeignKey("organization.id", ondelete="SET NULL"), nullable=False)

    organization = relationship("Organization", back_populates="product_owners", lazy="joined")
    invited_developers = relationship("Developer", back_populates="inviter", lazy="dynamic", foreign_keys="Developer.owner_id")
    
    # Composite unique constraint: email + organization_id
    __table_args__ = (
        UniqueConstraint('email', 'organization_id', name='uq_product_owner_email_org'),
    )

    def check_password(self, password: str) -> bool:
        """Check if provided password matches the user's password."""
        from src.auth.hashing import verify_password
        return verify_password(password, self.password)


class Developer(Base):
    """Developer model."""
    __tablename__ = "developer"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50))
    email = Column(String(255))  # Removed unique constraint - now unique per organization
    firstName = Column(String(50))
    lastName = Column(String(50))
    password = Column(String(255))
    owner_id = Column(Integer, ForeignKey("product_owner.id", ondelete="SET NULL"), nullable=True)
    organization_id = Column(Integer, ForeignKey("organization.id", ondelete="SET NULL"), nullable=False)

    inviter = relationship("ProductOwner", back_populates="invited_developers", foreign_keys=[owner_id])
    organization = relationship("Organization", lazy="joined")
    
    # Composite unique constraint: email + organization_id
    __table_args__ = (
        UniqueConstraint('email', 'organization_id', name='uq_developer_email_org'),
    )

    def check_password(self, password: str) -> bool:
        """Check if provided password matches the user's password."""
        from src.auth.hashing import verify_password
        return verify_password(password, self.password)


# Keep User model for backward compatibility with existing foreign keys
class User(Base):
    """Legacy User model - kept for backward compatibility with Task/Project foreign keys."""
    __tablename__ = "user"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50))
    email = Column(String(255), unique=True)
    role = Column(String(50), nullable=True, default='user')
    firstName = Column(String(50))
    lastName = Column(String(50))
    password = Column(String(255))
    # inviter_id is optional - only exists after migration
    # inviter_id = Column(Integer, ForeignKey("user.id", ondelete="SET NULL"), nullable=True)

    tasks = relationship("Task", back_populates="owner", lazy="dynamic")
    # Note: projects relationship removed - projects now belong to ProductOwner, not User
    # projects = relationship("Project", back_populates="owner", lazy="dynamic")

    def check_password(self, password: str) -> bool:
        """Check if provided password matches the user's password."""
        from src.auth.hashing import verify_password
        return verify_password(password, self.password)
