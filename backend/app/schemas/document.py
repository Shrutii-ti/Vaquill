"""
Pydantic schemas for Document model.
"""

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
from uuid import UUID


class DocumentBase(BaseModel):
    """Base document schema."""
    title: str = Field(..., min_length=1, max_length=500, description="Document title")
    side: str = Field(..., pattern="^[AB]$", description="Side A or B")


class DocumentCreate(DocumentBase):
    """
    Schema for document upload request.
    Note: file upload is handled separately as multipart/form-data
    """
    pass


class DocumentResponse(DocumentBase):
    """Schema for document API responses."""
    id: UUID
    case_id: UUID
    file_name: str
    file_path: str
    file_type: str
    page_count: Optional[int]
    word_count: Optional[int]
    status: str  # pending, processing, ready, failed
    uploaded_by: UUID
    uploaded_at: datetime

    class Config:
        from_attributes = True


class DocumentDetailResponse(DocumentResponse):
    """Schema for detailed document response with full text."""
    full_text: Optional[str] = Field(None, description="Extracted document text")
