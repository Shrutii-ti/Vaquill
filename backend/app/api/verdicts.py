"""
Verdict API endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID
from typing import List

from app.dependencies import get_db, get_current_user
from app.models.user import User
from app.models.case import Case
from app.schemas.verdict import VerdictResponse, VerdictCreateRequest
from app.services.verdict_orchestrator import VerdictOrchestrator

router = APIRouter()


@router.post("/{case_id}/verdict", response_model=VerdictResponse, status_code=status.HTTP_201_CREATED)
async def generate_initial_verdict(
    case_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Generate initial verdict (Round 0) for a case.

    Requires both sides to have submitted at least one document.

    **Requirements:**
    - Case must exist and belong to current user
    - Case must have documents from both Side A and Side B
    - Round 0 verdict must not already exist

    **Process:**
    1. Fetches all documents for both sides
    2. Builds structured prompt for AI judge
    3. Calls GPT-4o-mini to generate verdict
    4. Saves verdict to database
    5. Updates case status to 'in_progress' and current_round to 1

    Returns:
        VerdictResponse: The generated verdict with AI analysis
    """
    # Verify case exists and user owns it
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Case not found"
        )

    if case.created_by != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )

    # Generate verdict using orchestrator
    try:
        verdict = VerdictOrchestrator.generate_initial_verdict(case_id, db)
        return verdict
    except ValueError as e:
        # Document validation errors
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except Exception as e:
        # Verdict generation errors
        if "already exists" in str(e):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=str(e)
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate verdict: {str(e)}"
        )


@router.get("/{case_id}/verdicts", response_model=List[VerdictResponse])
async def get_all_verdicts(
    case_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get all verdicts for a case, ordered by round.

    Returns verdicts from Round 0 (initial) through Round 5 (if applicable).
    Each verdict shows the AI judge's analysis at that point in the case.

    Args:
        case_id: UUID of the case

    Returns:
        List[VerdictResponse]: All verdicts ordered by round number
    """
    # Verify case exists and user owns it
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Case not found"
        )

    if case.created_by != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )

    # Get all verdicts
    verdicts = VerdictOrchestrator.get_all_verdicts(case_id, db)
    return verdicts


@router.get("/{case_id}/verdicts/{round}", response_model=VerdictResponse)
async def get_verdict_by_round(
    case_id: UUID,
    round: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get verdict for a specific round.

    Rounds:
    - Round 0: Initial verdict based only on submitted documents
    - Rounds 1-5: Verdicts after each argument round

    Args:
        case_id: UUID of the case
        round: Round number (0-5)

    Returns:
        VerdictResponse: The verdict for that round

    Raises:
        404: If verdict for that round doesn't exist
    """
    # Validate round number
    if round < 0 or round > 5:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Round must be between 0 and 5"
        )

    # Verify case exists and user owns it
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Case not found"
        )

    if case.created_by != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )

    # Get verdict for specific round
    verdict = VerdictOrchestrator.get_verdict_by_round(case_id, round, db)

    if not verdict:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Verdict for round {round} not found"
        )

    return verdict
