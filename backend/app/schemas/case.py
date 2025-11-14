"""
Pydantic schemas for Case model.
"""

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
from uuid import UUID


class CaseBase(BaseModel):
    """Base case schema with common fields."""
    title: str = Field(..., min_length=1, max_length=500, description="Case title")
    description: Optional[str] = Field(None, description="Case description")
    case_type: str = Field(..., description="Case type: civil, criminal, corporate, constitutional, family")
    jurisdiction: str = Field(..., max_length=100, description="Jurisdiction (e.g., India, USA-CA, UK)")


class CaseCreate(CaseBase):
    """Schema for creating a new case."""
    pass


class CaseUpdate(BaseModel):
    """Schema for updating a case (all fields optional)."""
    title: Optional[str] = Field(None, min_length=1, max_length=500)
    description: Optional[str] = None
    case_type: Optional[str] = None
    jurisdiction: Optional[str] = Field(None, max_length=100)
    status: Optional[str] = Field(None, description="Status: draft, ready, in_progress, finalized")


class CaseResponse(CaseBase):
    """Schema for case API responses."""
    id: UUID
    case_number: str
    created_by: UUID
    status: str
    current_round: int
    max_rounds: int
    created_at: datetime
    updated_at: Optional[datetime]
    finalized_at: Optional[datetime]

    class Config:
        from_attributes = True


class CaseDetailResponse(CaseResponse):
    """
    Schema for detailed case response with related data.
    This will include documents, arguments, and verdicts counts or summaries.
    """
    documents_count: int = Field(default=0, description="Number of documents uploaded")
    side_a_docs_count: int = Field(default=0, description="Number of Side A documents")
    side_b_docs_count: int = Field(default=0, description="Number of Side B documents")
    arguments_count: int = Field(default=0, description="Number of arguments submitted")
    verdicts_count: int = Field(default=0, description="Number of verdicts generated")
