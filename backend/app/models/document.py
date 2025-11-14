"""
Document model for case evidence storage.
"""

from sqlalchemy import Column, String, DateTime, Integer, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.db.database import Base


class Document(Base):
    """
    Document model for uploaded case evidence.
    """

    __tablename__ = "documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    case_id = Column(UUID(as_uuid=True), ForeignKey("cases.id"), nullable=False, index=True)
    side = Column(String(1), nullable=False)  # 'A' or 'B'

    title = Column(String(500), nullable=False)
    file_name = Column(String(500), nullable=False)
    file_path = Column(String(1000), nullable=False)
    file_type = Column(String(50), nullable=False)  # pdf, docx, txt

    # Extracted content (from GPT-4o-mini)
    full_text = Column(Text, nullable=True)
    page_count = Column(Integer, nullable=True)
    word_count = Column(Integer, nullable=True)

    uploaded_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    uploaded_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Processing status
    status = Column(
        String(50),
        default="pending",
        nullable=False
    )  # pending, processing, ready, failed

    # Relationships
    case = relationship("Case", back_populates="documents")
    uploaded_by_user = relationship("User", back_populates="documents")

    def __repr__(self):
        return f"<Document {self.title} - Side {self.side}>"
