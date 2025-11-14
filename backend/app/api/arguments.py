"""
Argument API endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID
from typing import List, Dict, Any

from app.dependencies import get_db, get_current_user
from app.models.user import User
from app.models.case import Case
from app.schemas.argument import ArgumentCreate, ArgumentResponse
from app.schemas.verdict import VerdictResponse
from app.services.argument_orchestrator import ArgumentOrchestrator

router = APIRouter()


@router.post("/{case_id}/arguments", status_code=status.HTTP_201_CREATED)
async def submit_argument(
    case_id: UUID,
    argument_data: ArgumentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Submit an argument for the current round.

    **Flow:**
    1. Validates case exists and user has access
    2. Checks that max rounds not exceeded
    3. Verifies this side hasn't already submitted for current round
    4. Saves the argument
    5. If BOTH sides have now submitted arguments:
       - Automatically generates new verdict for this round
       - Advances case to next round
    6. Returns argument + verdict (if generated) + waiting status

    **Requirements:**
    - Case must have an initial verdict (Round 0)
    - Case must not be finalized
    - Current round must be <= max_rounds
    - This side must not have already submitted for current round

    Args:
        case_id: UUID of the case
        argument_data: Argument text and side

    Returns:
        Dict with:
        - argument: The created argument object
        - verdict: New verdict (if both sides submitted), else null
        - waiting_for_other_side: True if waiting for other side's argument
        - message: Status message
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

    # Submit argument using orchestrator
    try:
        result = ArgumentOrchestrator.submit_argument(
            case_id=case_id,
            side=argument_data.side,
            argument_text=argument_data.argument_text,
            user_id=current_user.id,
            db=db
        )

        # Build response
        response = {
            "argument": ArgumentResponse.model_validate(result['argument']),
            "verdict": VerdictResponse.model_validate(result['verdict']) if result['verdict'] else None,
            "waiting_for_other_side": result['waiting_for_other_side'],
            "message": "Argument submitted and verdict generated" if result['verdict']
                      else f"Argument submitted. Waiting for Side {'B' if argument_data.side == 'A' else 'A'} to submit."
        }

        return response

    except Exception as e:
        error_msg = str(e)

        # Map common errors to appropriate HTTP status codes
        if "not found" in error_msg.lower():
            status_code = status.HTTP_404_NOT_FOUND
        elif "already submitted" in error_msg.lower():
            status_code = status.HTTP_409_CONFLICT
        elif "finalized" in error_msg.lower() or "draft" in error_msg.lower() or "maximum rounds" in error_msg.lower():
            status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
        else:
            status_code = status.HTTP_500_INTERNAL_SERVER_ERROR

        raise HTTPException(
            status_code=status_code,
            detail=error_msg
        )


@router.get("/{case_id}/arguments", response_model=List[ArgumentResponse])
async def get_case_arguments(
    case_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get all arguments for a case, ordered by round and side.

    Useful for viewing the progression of arguments throughout the case.

    Args:
        case_id: UUID of the case

    Returns:
        List[ArgumentResponse]: All arguments ordered by round, then by side
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

    # Get all arguments
    arguments = ArgumentOrchestrator.get_case_arguments(case_id, db)
    return arguments
