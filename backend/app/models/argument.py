"""
Argument model for round-based case arguments.
"""

from sqlalchemy import Column, String, DateTime, Integer, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.db.database import Base


class Argument(Base):
    """
    Argument model for side A/B arguments in each round.
    """

    __tablename__ = "arguments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    case_id = Column(UUID(as_uuid=True), ForeignKey("cases.id"), nullable=False, index=True)
    round = Column(Integer, nullable=False)  # 1-5
    side = Column(String(1), nullable=False)  # 'A' or 'B'

    argument_text = Column(Text, nullable=False)

    submitted_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    submitted_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    case = relationship("Case", back_populates="arguments")
    submitted_by_user = relationship("User", back_populates="arguments")

    def __repr__(self):
        return f"<Argument Round {self.round} - Side {self.side}>"
