"""
Document service - Business logic for document management.
"""

import os
import shutil
from datetime import datetime
from pathlib import Path
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
from fastapi import UploadFile, HTTPException, status

from app.models.document import Document
from app.models.case import Case
from app.models.user import User
from app.config import settings


class DocumentService:
    """Service class for document operations."""

    # Allowed file types
    ALLOWED_EXTENSIONS = {'pdf', 'docx', 'doc', 'txt'}
    ALLOWED_MIME_TYPES = {
        'application/pdf',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'application/msword',
        'text/plain'
    }

    # Max file size (10MB)
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB in bytes

    @staticmethod
    def get_file_extension(filename: str) -> str:
        """Get file extension from filename."""
        return filename.rsplit('.', 1)[1].lower() if '.' in filename else ''

    @staticmethod
    def validate_file(file: UploadFile) -> None:
        """
        Validate uploaded file.

        Args:
            file: Uploaded file

        Raises:
            HTTPException: If file is invalid
        """
        # Check if file exists
        if not file or not file.filename:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="No file provided"
            )

        # Check file extension
        ext = DocumentService.get_file_extension(file.filename)
        if ext not in DocumentService.ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"File type not allowed. Allowed types: {', '.join(DocumentService.ALLOWED_EXTENSIONS)}"
            )

        # Check MIME type
        if file.content_type not in DocumentService.ALLOWED_MIME_TYPES:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid file MIME type: {file.content_type}"
            )

    @staticmethod
    def check_file_size(file_size: int) -> None:
        """
        Check if file size is within limit.

        Args:
            file_size: Size of file in bytes

        Raises:
            HTTPException: If file is too large
        """
        if file_size > DocumentService.MAX_FILE_SIZE:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File too large. Max size: {DocumentService.MAX_FILE_SIZE / (1024 * 1024)}MB"
            )

    @staticmethod
    def save_file(file: UploadFile, case_id: UUID) -> tuple[str, str]:
        """
        Save uploaded file to disk.

        Args:
            file: Uploaded file
            case_id: Case UUID

        Returns:
            Tuple of (file_path, file_name)
        """
        # Create uploads directory if it doesn't exist
        upload_dir = Path(settings.UPLOAD_DIR) / str(case_id)
        upload_dir.mkdir(parents=True, exist_ok=True)

        # Generate unique filename
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        ext = DocumentService.get_file_extension(file.filename)
        safe_filename = f"{timestamp}_{file.filename}"
        file_path = upload_dir / safe_filename

        # Save file
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        return str(file_path), safe_filename

    @staticmethod
    async def upload_document(
        case_id: UUID,
        title: str,
        side: str,
        file: UploadFile,
        user: User,
        db: Session
    ) -> Document:
        """
        Upload a document for a case.

        Args:
            case_id: Case UUID
            title: Document title
            side: Side A or B
            file: Uploaded file
            user: User uploading
            db: Database session

        Returns:
            Created Document object

        Raises:
            HTTPException: If validation fails
        """
        # Check if case exists and user owns it
        case = db.query(Case).filter(Case.id == case_id).first()
        if not case:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Case not found"
            )

        if case.created_by != user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )

        # Validate file
        DocumentService.validate_file(file)

        # Read file to check size
        file_content = await file.read()
        file_size = len(file_content)
        DocumentService.check_file_size(file_size)

        # Reset file pointer and save
        await file.seek(0)
        file_path, file_name = DocumentService.save_file(file, case_id)

        # Get file type
        file_type = DocumentService.get_file_extension(file.filename)

        # Create document record
        document = Document(
            case_id=case_id,
            side=side,
            title=title,
            file_name=file_name,
            file_path=file_path,
            file_type=file_type,
            uploaded_by=user.id,
            status='pending'  # Will be 'processing' when OpenAI extraction starts
        )

        db.add(document)
        db.commit()
        db.refresh(document)

        # Trigger text extraction in background
        from app.services.openai_service import OpenAIService
        try:
            await OpenAIService.process_document(str(document.id), db)
        except Exception as e:
            print(f"Warning: Document extraction failed: {e}")
            # Don't fail the upload if extraction fails

        return document

    @staticmethod
    def get_case_documents(case_id: UUID, user: User, db: Session) -> List[Document]:
        """
        Get all documents for a case.

        Args:
            case_id: Case UUID
            user: User requesting
            db: Database session

        Returns:
            List of Document objects

        Raises:
            HTTPException: If access denied
        """
        # Check if case exists and user owns it
        case = db.query(Case).filter(Case.id == case_id).first()
        if not case:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Case not found"
            )

        if case.created_by != user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )

        return db.query(Document).filter(Document.case_id == case_id).all()

    @staticmethod
    def get_document_by_id(
        case_id: UUID,
        document_id: UUID,
        user: User,
        db: Session,
        include_text: bool = False
    ) -> Optional[Document]:
        """
        Get a single document by ID.

        Args:
            case_id: Case UUID
            document_id: Document UUID
            user: User requesting
            db: Database session
            include_text: Whether to include full text

        Returns:
            Document object or None

        Raises:
            HTTPException: If access denied
        """
        # Check if case exists and user owns it
        case = db.query(Case).filter(Case.id == case_id).first()
        if not case:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Case not found"
            )

        if case.created_by != user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )

        # Get document
        document = db.query(Document).filter(
            Document.id == document_id,
            Document.case_id == case_id
        ).first()

        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )

        return document

    @staticmethod
    def delete_document(
        case_id: UUID,
        document_id: UUID,
        user: User,
        db: Session
    ) -> bool:
        """
        Delete a document.

        Args:
            case_id: Case UUID
            document_id: Document UUID
            user: User requesting
            db: Database session

        Returns:
            True if deleted

        Raises:
            HTTPException: If access denied or not found
        """
        # Check if case exists and user owns it
        case = db.query(Case).filter(Case.id == case_id).first()
        if not case:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Case not found"
            )

        if case.created_by != user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )

        # Get document
        document = db.query(Document).filter(
            Document.id == document_id,
            Document.case_id == case_id
        ).first()

        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )

        # Delete file from disk
        try:
            if os.path.exists(document.file_path):
                os.remove(document.file_path)
        except Exception as e:
            # Log error but continue with database deletion
            print(f"Error deleting file: {e}")

        # Delete from database
        db.delete(document)
        db.commit()

        return True
