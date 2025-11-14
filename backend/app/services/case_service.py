"""
Case service - Business logic for case management.
"""

from datetime import datetime
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID, uuid4

from app.models.case import Case
from app.models.user import User
from app.schemas.case import CaseCreate, CaseUpdate, CaseResponse, CaseDetailResponse


class CaseService:
    """Service class for case operations."""

    @staticmethod
    def generate_case_number() -> str:
        """
        Generate unique case number in format: CAS-YYYY-XXXXXX

        Returns:
            str: Generated case number
        """
        year = datetime.utcnow().year
        unique_id = str(uuid4())[:6].upper()
        return f"CAS-{year}-{unique_id}"

    @staticmethod
    def create_case(case_data: CaseCreate, user: User, db: Session) -> Case:
        """
        Create a new case.

        Args:
            case_data: Case creation data
            user: User creating the case
            db: Database session

        Returns:
            Created Case object
        """
        # Generate unique case number
        case_number = CaseService.generate_case_number()

        # Create case
        case = Case(
            case_number=case_number,
            title=case_data.title,
            description=case_data.description,
            case_type=case_data.case_type,
            jurisdiction=case_data.jurisdiction,
            created_by=user.id,
            status="draft",
            current_round=0,
            max_rounds=5
        )

        db.add(case)
        db.commit()
        db.refresh(case)

        return case

    @staticmethod
    def get_user_cases(user: User, db: Session) -> List[Case]:
        """
        Get all cases created by a user.

        Args:
            user: User object
            db: Database session

        Returns:
            List of Case objects
        """
        return db.query(Case).filter(Case.created_by == user.id).all()

    @staticmethod
    def get_case_by_id(case_id: UUID, user: User, db: Session) -> Optional[Case]:
        """
        Get a specific case by ID (only if user owns it).

        Args:
            case_id: Case UUID
            user: User object
            db: Database session

        Returns:
            Case object or None
        """
        return db.query(Case).filter(
            Case.id == case_id,
            Case.created_by == user.id
        ).first()

    @staticmethod
    def update_case(
        case_id: UUID,
        case_data: CaseUpdate,
        user: User,
        db: Session
    ) -> Optional[Case]:
        """
        Update a case (only if user owns it).

        Args:
            case_id: Case UUID
            case_data: Update data
            user: User object
            db: Database session

        Returns:
            Updated Case object or None
        """
        case = CaseService.get_case_by_id(case_id, user, db)
        if not case:
            return None

        # Update only provided fields
        update_data = case_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(case, field, value)

        case.updated_at = datetime.utcnow()

        db.commit()
        db.refresh(case)

        return case

    @staticmethod
    def delete_case(case_id: UUID, user: User, db: Session) -> bool:
        """
        Delete a case (only if user owns it).

        Args:
            case_id: Case UUID
            user: User object
            db: Database session

        Returns:
            True if deleted, False if not found
        """
        case = CaseService.get_case_by_id(case_id, user, db)
        if not case:
            return False

        db.delete(case)
        db.commit()

        return True

    @staticmethod
    def get_case_detail(case_id: UUID, user: User, db: Session) -> Optional[CaseDetailResponse]:
        """
        Get detailed case information with counts.

        Args:
            case_id: Case UUID
            user: User object
            db: Database session

        Returns:
            CaseDetailResponse or None
        """
        case = CaseService.get_case_by_id(case_id, user, db)
        if not case:
            return None

        # Count related entities
        documents_count = len(case.documents)
        side_a_docs = len([d for d in case.documents if d.side == 'A'])
        side_b_docs = len([d for d in case.documents if d.side == 'B'])
        arguments_count = len(case.arguments)
        verdicts_count = len(case.verdicts)

        # Build response
        case_dict = CaseResponse.model_validate(case).model_dump()
        case_dict.update({
            "documents_count": documents_count,
            "side_a_docs_count": side_a_docs,
            "side_b_docs_count": side_b_docs,
            "arguments_count": arguments_count,
            "verdicts_count": verdicts_count
        })

        return CaseDetailResponse(**case_dict)
