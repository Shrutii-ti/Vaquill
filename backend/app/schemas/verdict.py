"""
Pydantic schemas for Verdict model.
"""

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID


class VerdictIssue(BaseModel):
    """Schema for a single issue in the verdict."""
    issue: str = Field(..., description="The legal issue being addressed")
    finding: str = Field(..., description="The finding/conclusion on this issue")
    reasoning: str = Field(..., description="Reasoning behind the finding")


class VerdictData(BaseModel):
    """Schema for the verdict JSON structure."""
    summary: str = Field(..., description="Brief verdict summary")
    winner: str = Field(..., pattern="^(A|B|undecided)$", description="Winner: A, B, or undecided")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Confidence score (0-1)")
    issues: List[VerdictIssue] = Field(default_factory=list, description="List of issues addressed")
    final_decision: str = Field(..., description="Final decision text")
    key_evidence_cited: List[str] = Field(default_factory=list, description="Key evidence referenced")


class VerdictResponse(BaseModel):
    """Schema for verdict API responses."""
    id: UUID
    case_id: UUID
    round: int  # 0 = initial, 1-5 = after arguments
    verdict_json: VerdictData
    model_used: str
    tokens_used: Optional[int]
    created_at: datetime

    class Config:
        from_attributes = True


class VerdictCreateRequest(BaseModel):
    """Schema for generating a new verdict (Round 0)."""
    pass  # No additional fields needed; case_id comes from URL


class VerdictSummaryResponse(BaseModel):
    """
    Schema for verdict summary (lighter response).
    Used for listing verdicts without full JSON details.
    """
    id: UUID
    case_id: UUID
    round: int
    winner: str
    confidence_score: float
    summary: str
    created_at: datetime

    class Config:
        from_attributes = True
