"""
Case model for legal case management.
"""

from sqlalchemy import Column, String, DateTime, Integer, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.db.database import Base


class Case(Base):
    """
    Case model representing a mock trial case.
    """

    __tablename__ = "cases"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    case_number = Column(String(50), unique=True, nullable=False, index=True)
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)

    case_type = Column(
        String(50),
        nullable=False,
        default="civil"
    )  # civil, criminal, corporate, constitutional, family
    jurisdiction = Column(String(100), nullable=False)  # India, USA-CA, UK, etc.

    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    status = Column(
        String(50),
        default="draft",
        nullable=False
    )  # draft, ready, in_progress, finalized

    current_round = Column(Integer, default=0, nullable=False)  # 0-5
    max_rounds = Column(Integer, default=5, nullable=False)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    finalized_at = Column(DateTime, nullable=True)

    # Relationships
    creator = relationship("User", back_populates="cases")
    documents = relationship("Document", back_populates="case", cascade="all, delete-orphan")
    arguments = relationship("Argument", back_populates="case", cascade="all, delete-orphan")
    verdicts = relationship("Verdict", back_populates="case", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Case {self.case_number} - {self.title}>"

    def generate_case_number(self):
        """Generate unique case number: CAS-2025-XXXXXX"""
        from datetime import datetime
        year = datetime.utcnow().year
        # Will be implemented with database sequence or counter
        return f"CAS-{year}-{str(uuid.uuid4())[:6].upper()}"
