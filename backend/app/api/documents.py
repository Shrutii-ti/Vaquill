"""
Document management API endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID

from app.db.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.document import DocumentResponse, DocumentDetailResponse
from app.services.document_service import DocumentService

router = APIRouter()


@router.post("/{case_id}/documents", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    case_id: UUID,
    title: str = Form(..., min_length=1, max_length=500),
    side: str = Form(..., pattern="^[AB]$"),
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Upload a document for a case.

    - **title**: Document title (required)
    - **side**: Side A or B (required)
    - **file**: File to upload (PDF, DOCX, TXT, max 10MB)

    Returns the created document.
    """
    try:
        document = await DocumentService.upload_document(
            case_id=case_id,
            title=title,
            side=side,
            file=file,
            user=current_user,
            db=db
        )
        return DocumentResponse.model_validate(document)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload document: {str(e)}"
        )


@router.get("/{case_id}/documents", response_model=List[DocumentResponse], status_code=status.HTTP_200_OK)
def get_case_documents(
    case_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all documents for a case.

    Returns a list of documents.
    """
    documents = DocumentService.get_case_documents(case_id, current_user, db)
    return [DocumentResponse.model_validate(doc) for doc in documents]


@router.get("/{case_id}/documents/{document_id}", response_model=DocumentDetailResponse, status_code=status.HTTP_200_OK)
def get_document(
    case_id: UUID,
    document_id: UUID,
    include_text: bool = False,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get a specific document by ID.

    - **include_text**: If true, includes the full extracted text (optional, default: false)

    Returns the document details.
    """
    document = DocumentService.get_document_by_id(
        case_id, document_id, current_user, db, include_text
    )
    return DocumentDetailResponse.model_validate(document)


@router.delete("/{case_id}/documents/{document_id}", status_code=status.HTTP_200_OK)
def delete_document(
    case_id: UUID,
    document_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete a document.

    Only the case owner can delete documents.
    This will also delete the file from storage.
    """
    DocumentService.delete_document(case_id, document_id, current_user, db)

    return {
        "message": "Document deleted successfully",
        "document_id": str(document_id)
    }
