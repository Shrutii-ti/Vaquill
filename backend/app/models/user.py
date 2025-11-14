"""
User model for authentication and profile management.
"""

from sqlalchemy import Column, String, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.db.database import Base


class User(Base):
    """
    User model for demo phone-based authentication.
    """

    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    phone_hash = Column(String(255), unique=True, nullable=False, index=True)
    full_name = Column(String(255), nullable=True)
    email = Column(String(255), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_login = Column(DateTime, nullable=True)

    # Relationships
    cases = relationship("Case", back_populates="creator", cascade="all, delete-orphan")
    documents = relationship("Document", back_populates="uploaded_by_user")
    arguments = relationship("Argument", back_populates="submitted_by_user")

    def __repr__(self):
        return f"<User {self.id} - {self.full_name or 'Anonymous'}>"
