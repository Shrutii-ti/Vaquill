"""
Case management API endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from app.db.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.case import (
    CaseCreate,
    CaseUpdate,
    CaseResponse,
    CaseDetailResponse
)
from app.services.case_service import CaseService

router = APIRouter()


@router.post("", response_model=CaseResponse, status_code=status.HTTP_201_CREATED)
def create_case(
    case_data: CaseCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new case.

    - **title**: Case title (required)
    - **description**: Case description (optional)
    - **case_type**: Type of case (civil, criminal, corporate, etc.)
    - **jurisdiction**: Jurisdiction (e.g., India, USA-CA)

    Returns the created case with auto-generated case number.
    """
    try:
        case = CaseService.create_case(case_data, current_user, db)
        return CaseResponse.model_validate(case)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create case: {str(e)}"
        )


@router.get("", response_model=List[CaseResponse], status_code=status.HTTP_200_OK)
def get_all_cases(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all cases created by the current user.

    Returns a list of cases.
    """
    cases = CaseService.get_user_cases(current_user, db)
    return [CaseResponse.model_validate(case) for case in cases]


@router.get("/{case_id}", response_model=CaseDetailResponse, status_code=status.HTTP_200_OK)
def get_case(
    case_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get detailed information about a specific case.

    Includes counts of documents, arguments, and verdicts.
    """
    # First check if case exists
    from app.models.case import Case
    case_exists = db.query(Case).filter(Case.id == case_id).first()

    if not case_exists:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Case not found"
        )

    # Check if user owns the case
    if case_exists.created_by != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )

    case_detail = CaseService.get_case_detail(case_id, current_user, db)
    return case_detail


@router.patch("/{case_id}", response_model=CaseResponse, status_code=status.HTTP_200_OK)
def update_case(
    case_id: UUID,
    case_data: CaseUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update case information.

    Only the case owner can update. All fields are optional.
    """
    case = CaseService.update_case(case_id, case_data, current_user, db)

    if not case:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Case not found or access denied"
        )

    return CaseResponse.model_validate(case)


@router.delete("/{case_id}", status_code=status.HTTP_200_OK)
def delete_case(
    case_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete a case.

    Only the case owner can delete. This will also delete all related
    documents, arguments, and verdicts (cascade delete).
    """
    # First check if case exists
    from app.models.case import Case
    case_exists = db.query(Case).filter(Case.id == case_id).first()

    if not case_exists:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Case not found"
        )

    # Check if user owns the case
    if case_exists.created_by != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )

    CaseService.delete_case(case_id, current_user, db)

    return {
        "message": "Case deleted successfully",
        "case_id": str(case_id)
    }


@router.post("/{case_id}/finalize", response_model=CaseResponse, status_code=status.HTTP_200_OK)
def finalize_case(
    case_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Finalize a case - mark it as complete and lock it from further modifications.

    **Requirements:**
    - Case must have at least the initial verdict (Round 0)
    - Case cannot already be finalized
    - User must own the case

    **Effects:**
    - Sets case status to 'finalized'
    - Sets finalized_at timestamp
    - Prevents future document uploads, arguments, or verdicts

    Returns the finalized case.
    """
    # Check if case exists
    from app.models.case import Case
    from app.models.verdict import Verdict
    from datetime import datetime

    case = db.query(Case).filter(Case.id == case_id).first()

    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Case not found"
        )

    # Check if user owns the case
    if case.created_by != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )

    # Check if already finalized
    if case.status == 'finalized':
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Case is already finalized"
        )

    # Check if case has at least the initial verdict
    verdict = db.query(Verdict).filter(
        Verdict.case_id == case_id,
        Verdict.round == 0
    ).first()

    if not verdict:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Cannot finalize case without an initial verdict"
        )

    # Finalize the case
    case.status = 'finalized'
    case.finalized_at = datetime.utcnow()

    db.commit()
    db.refresh(case)

    return CaseResponse.model_validate(case)
