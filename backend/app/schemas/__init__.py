"""
Pydantic schemas package.
Export all schemas for easy imports.
"""

from app.schemas.user import (
    UserBase,
    UserCreate,
    UserUpdate,
    UserResponse,
    LoginRequest,
    LoginResponse,
    TokenData,
)

from app.schemas.case import (
    CaseBase,
    CaseCreate,
    CaseUpdate,
    CaseResponse,
    CaseDetailResponse,
)

from app.schemas.document import (
    DocumentBase,
    DocumentCreate,
    DocumentResponse,
    DocumentDetailResponse,
)

from app.schemas.argument import (
    ArgumentBase,
    ArgumentCreate,
    ArgumentResponse,
)

from app.schemas.verdict import (
    VerdictIssue,
    VerdictData,
    VerdictResponse,
    VerdictCreateRequest,
    VerdictSummaryResponse,
)

__all__ = [
    # User & Auth
    "UserBase",
    "UserCreate",
    "UserUpdate",
    "UserResponse",
    "LoginRequest",
    "LoginResponse",
    "TokenData",
    # Case
    "CaseBase",
    "CaseCreate",
    "CaseUpdate",
    "CaseResponse",
    "CaseDetailResponse",
    # Document
    "DocumentBase",
    "DocumentCreate",
    "DocumentResponse",
    "DocumentDetailResponse",
    # Argument
    "ArgumentBase",
    "ArgumentCreate",
    "ArgumentResponse",
    # Verdict
    "VerdictIssue",
    "VerdictData",
    "VerdictResponse",
    "VerdictCreateRequest",
    "VerdictSummaryResponse",
]
