"""
Verdict model for AI judge decisions.
"""

from sqlalchemy import Column, String, DateTime, Integer, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.db.database import Base


class Verdict(Base):
    """
    Verdict model storing AI judge decisions per round.
    """

    __tablename__ = "verdicts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    case_id = Column(UUID(as_uuid=True), ForeignKey("cases.id"), nullable=False, index=True)
    round = Column(Integer, nullable=False)  # 0 = initial, 1-5 = after arguments

    # Structured verdict data (stored as JSON, becomes JSONB in PostgreSQL)
    verdict_json = Column(JSON, nullable=False)
    # Structure:
    # {
    #   "summary": "Brief verdict summary",
    #   "winner": "A" | "B" | "undecided",
    #   "confidence_score": 0.85,
    #   "issues": [
    #     {
    #       "issue": "Was contract valid?",
    #       "finding": "Yes",
    #       "reasoning": "..."
    #     }
    #   ],
    #   "final_decision": "...",
    #   "key_evidence_cited": ["Doc A - Contract", "Doc B - Email"]
    # }

    # AI metadata
    model_used = Column(String(100), default="gpt-4o-mini", nullable=False)
    tokens_used = Column(Integer, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    case = relationship("Case", back_populates="verdicts")

    def __repr__(self):
        return f"<Verdict Round {self.round} - Case {self.case_id}>"
