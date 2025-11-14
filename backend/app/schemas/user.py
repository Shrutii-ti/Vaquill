"""
Pydantic schemas for User model and authentication.
"""

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
from uuid import UUID


# ===== User Schemas =====

class UserBase(BaseModel):
    """Base user schema with common fields."""
    full_name: Optional[str] = Field(None, max_length=255, description="User's full name")
    email: Optional[str] = Field(None, max_length=255, description="User's email address")


class UserCreate(BaseModel):
    """Schema for creating a new user (demo phone login)."""
    phone: str = Field(..., min_length=10, max_length=15, description="Phone number (10-15 digits)")
    full_name: Optional[str] = Field(None, max_length=255)
    email: Optional[str] = Field(None, max_length=255)


class UserUpdate(UserBase):
    """Schema for updating user profile."""
    pass


class UserResponse(UserBase):
    """Schema for user API responses."""
    id: UUID
    created_at: datetime
    last_login: Optional[datetime]

    class Config:
        from_attributes = True  # Pydantic v2 (was orm_mode in v1)


# ===== Auth Schemas =====

class LoginRequest(BaseModel):
    """Schema for login request (phone-based demo auth)."""
    phone: str = Field(..., min_length=10, max_length=15, description="Phone number")
    full_name: Optional[str] = Field(None, max_length=255, description="Optional full name")
    email: Optional[str] = Field(None, max_length=255, description="Optional email")


class LoginResponse(BaseModel):
    """Schema for login response."""
    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type")
    user: UserResponse = Field(..., description="User information")


class TokenData(BaseModel):
    """Schema for JWT token payload."""
    user_id: Optional[str] = None
