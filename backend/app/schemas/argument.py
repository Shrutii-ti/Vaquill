"""
Pydantic schemas for Argument model.
"""

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
from uuid import UUID


class ArgumentBase(BaseModel):
    """Base argument schema."""
    side: str = Field(..., pattern="^[AB]$", description="Side A or B")
    argument_text: str = Field(..., min_length=10, description="Argument text (min 10 chars)")


class ArgumentCreate(ArgumentBase):
    """Schema for submitting an argument."""
    pass


class ArgumentResponse(ArgumentBase):
    """Schema for argument API responses."""
    id: UUID
    case_id: UUID
    round: int
    submitted_by: UUID
    submitted_at: datetime

    class Config:
        from_attributes = True
