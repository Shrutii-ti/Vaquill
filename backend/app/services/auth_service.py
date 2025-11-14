"""
Authentication service - Business logic for user authentication.
"""

from datetime import datetime
from sqlalchemy.orm import Session
from typing import Optional

from app.models.user import User
from app.schemas.user import UserCreate, UserResponse, LoginResponse
from app.utils.security import get_phone_hash, create_access_token


class AuthService:
    """Service class for authentication operations."""

    @staticmethod
    def login_or_register(phone: str, full_name: Optional[str], email: Optional[str], db: Session) -> LoginResponse:
        """
        Login or register a user with phone number.

        Args:
            phone: Phone number (will be hashed)
            full_name: Optional full name
            email: Optional email
            db: Database session

        Returns:
            LoginResponse with access token and user info
        """
        # Hash the phone number for secure storage
        phone_hash = get_phone_hash(phone)

        # Check if user exists
        user = db.query(User).filter(User.phone_hash == phone_hash).first()

        if user:
            # Existing user - update last login
            user.last_login = datetime.utcnow()

            # Update profile if provided
            if full_name:
                user.full_name = full_name
            if email:
                user.email = email

            db.commit()
            db.refresh(user)
        else:
            # New user - create account
            user = User(
                phone_hash=phone_hash,
                full_name=full_name,
                email=email,
                last_login=datetime.utcnow()
            )
            db.add(user)
            db.commit()
            db.refresh(user)

        # Generate JWT token
        access_token = create_access_token(data={"sub": str(user.id)})

        # Return login response
        return LoginResponse(
            access_token=access_token,
            token_type="bearer",
            user=UserResponse.model_validate(user)
        )

    @staticmethod
    def get_user_by_id(user_id: str, db: Session) -> Optional[User]:
        """
        Get user by ID.

        Args:
            user_id: User UUID as string
            db: Database session

        Returns:
            User object or None
        """
        return db.query(User).filter(User.id == user_id).first()
