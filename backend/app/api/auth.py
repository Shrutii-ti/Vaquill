"""
Authentication API endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.user import LoginRequest, LoginResponse, UserResponse
from app.services.auth_service import AuthService

router = APIRouter()


@router.post("/login", response_model=LoginResponse, status_code=status.HTTP_200_OK)
def login(
    login_data: LoginRequest,
    db: Session = Depends(get_db)
):
    """
    Login or register with phone number (demo authentication).

    - **phone**: Phone number (10-15 digits)
    - **full_name**: Optional full name
    - **email**: Optional email address

    Returns access token and user information.
    """
    try:
        return AuthService.login_or_register(
            phone=login_data.phone,
            full_name=getattr(login_data, 'full_name', None),
            email=getattr(login_data, 'email', None),
            db=db
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Login failed: {str(e)}"
        )


@router.get("/me", response_model=UserResponse, status_code=status.HTTP_200_OK)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """
    Get current authenticated user information.

    Requires valid JWT token in Authorization header.
    """
    return UserResponse.model_validate(current_user)


@router.post("/logout", status_code=status.HTTP_200_OK)
async def logout(
    current_user: User = Depends(get_current_user)
):
    """
    Logout endpoint (stateless JWT - client should discard token).

    Since we're using stateless JWT tokens, logout is handled client-side
    by discarding the token. This endpoint exists for API consistency.
    """
    return {
        "message": "Successfully logged out",
        "detail": "Please discard your access token"
    }
