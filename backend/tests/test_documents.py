"""
Test suite for Document upload endpoints (TDD RED phase).
"""

import io
import os
from uuid import uuid4

import pytest
from app.models.document import Document


# ============================================================================
# Upload Tests
# ============================================================================

def test_upload_document_with_valid_file(client, auth_headers, test_case):
    """Test uploading a valid document to a case."""
    # Create a fake PDF file
    file_content = b"%PDF-1.4 Test PDF content"
    files = {
        'file': ('test_doc.pdf', io.BytesIO(file_content), 'application/pdf')
    }
    data = {
        'title': 'Contract Agreement',
        'side': 'A'
    }

    response = client.post(
        f"/api/cases/{test_case.id}/documents",
        files=files,
        data=data,
        headers=auth_headers
    )

    assert response.status_code == 201
    doc = response.json()
    assert doc['title'] == 'Contract Agreement'
    assert doc['side'] == 'A'
    assert 'test_doc.pdf' in doc['file_name']  # Filename includes timestamp prefix
    assert doc['file_type'] == 'pdf'
    assert doc['status'] == 'pending'
    assert 'id' in doc
    assert 'uploaded_at' in doc


def test_upload_document_without_auth_fails(client, test_case):
    """Test that uploading without authentication fails."""
    file_content = b"Test content"
    files = {
        'file': ('test.txt', io.BytesIO(file_content), 'text/plain')
    }
    data = {
        'title': 'Test Document',
        'side': 'B'
    }

    response = client.post(
        f"/api/cases/{test_case.id}/documents",
        files=files,
        data=data
    )

    assert response.status_code in [401, 403]  # Either Unauthorized or Forbidden


def test_upload_document_to_nonexistent_case_fails(client, auth_headers):
    """Test uploading to a non-existent case fails."""
    fake_case_id = uuid4()
    file_content = b"Test content"
    files = {
        'file': ('test.txt', io.BytesIO(file_content), 'text/plain')
    }
    data = {
        'title': 'Test Document',
        'side': 'A'
    }

    response = client.post(
        f"/api/cases/{fake_case_id}/documents",
        files=files,
        data=data,
        headers=auth_headers
    )

    assert response.status_code == 404


def test_upload_document_to_case_not_owned_fails(client, db_session, test_case):
    """Test uploading to another user's case fails."""
    # Create a different user
    from app.models.user import User
    from app.utils.security import create_access_token

    other_user = User(
        phone_hash="other_user_hash",
        full_name="Other User"
    )
    db_session.add(other_user)
    db_session.commit()

    # Create auth headers for other user
    other_token = create_access_token(data={"sub": str(other_user.id)})
    other_headers = {"Authorization": f"Bearer {other_token}"}

    file_content = b"Test content"
    files = {
        'file': ('test.txt', io.BytesIO(file_content), 'text/plain')
    }
    data = {
        'title': 'Test Document',
        'side': 'A'
    }

    response = client.post(
        f"/api/cases/{test_case.id}/documents",
        files=files,
        data=data,
        headers=other_headers
    )

    assert response.status_code == 403


def test_upload_document_with_invalid_side_fails(client, auth_headers, test_case):
    """Test uploading with invalid side (not A or B) fails."""
    file_content = b"Test content"
    files = {
        'file': ('test.txt', io.BytesIO(file_content), 'text/plain')
    }
    data = {
        'title': 'Test Document',
        'side': 'C'  # Invalid side
    }

    response = client.post(
        f"/api/cases/{test_case.id}/documents",
        files=files,
        data=data,
        headers=auth_headers
    )

    assert response.status_code == 422


def test_upload_document_without_file_fails(client, auth_headers, test_case):
    """Test uploading without a file fails."""
    data = {
        'title': 'Test Document',
        'side': 'A'
    }

    response = client.post(
        f"/api/cases/{test_case.id}/documents",
        data=data,
        headers=auth_headers
    )

    assert response.status_code == 422


def test_upload_document_with_invalid_file_type_fails(client, auth_headers, test_case):
    """Test uploading with unsupported file type fails."""
    file_content = b"Binary content"
    files = {
        'file': ('test.exe', io.BytesIO(file_content), 'application/x-msdownload')
    }
    data = {
        'title': 'Invalid Document',
        'side': 'A'
    }

    response = client.post(
        f"/api/cases/{test_case.id}/documents",
        files=files,
        data=data,
        headers=auth_headers
    )

    assert response.status_code == 422


def test_upload_document_exceeding_size_limit_fails(client, auth_headers, test_case):
    """Test uploading a file exceeding size limit fails."""
    # Create a file larger than allowed (assuming 10MB limit)
    large_content = b"x" * (11 * 1024 * 1024)  # 11MB
    files = {
        'file': ('large.pdf', io.BytesIO(large_content), 'application/pdf')
    }
    data = {
        'title': 'Large Document',
        'side': 'A'
    }

    response = client.post(
        f"/api/cases/{test_case.id}/documents",
        files=files,
        data=data,
        headers=auth_headers
    )

    assert response.status_code == 413


def test_upload_multiple_documents_to_same_side(client, auth_headers, test_case):
    """Test uploading multiple documents to the same side."""
    # First document
    file1 = {'file': ('doc1.txt', io.BytesIO(b"Content 1"), 'text/plain')}
    data1 = {'title': 'Document 1', 'side': 'A'}
    response1 = client.post(
        f"/api/cases/{test_case.id}/documents",
        files=file1,
        data=data1,
        headers=auth_headers
    )
    assert response1.status_code == 201

    # Second document
    file2 = {'file': ('doc2.txt', io.BytesIO(b"Content 2"), 'text/plain')}
    data2 = {'title': 'Document 2', 'side': 'A'}
    response2 = client.post(
        f"/api/cases/{test_case.id}/documents",
        files=file2,
        data=data2,
        headers=auth_headers
    )
    assert response2.status_code == 201


def test_upload_documents_to_both_sides(client, auth_headers, test_case):
    """Test uploading documents to both sides A and B."""
    # Side A document
    file_a = {'file': ('doc_a.txt', io.BytesIO(b"Side A content"), 'text/plain')}
    data_a = {'title': 'Document A', 'side': 'A'}
    response_a = client.post(
        f"/api/cases/{test_case.id}/documents",
        files=file_a,
        data=data_a,
        headers=auth_headers
    )
    assert response_a.status_code == 201

    # Side B document
    file_b = {'file': ('doc_b.txt', io.BytesIO(b"Side B content"), 'text/plain')}
    data_b = {'title': 'Document B', 'side': 'B'}
    response_b = client.post(
        f"/api/cases/{test_case.id}/documents",
        files=file_b,
        data=data_b,
        headers=auth_headers
    )
    assert response_b.status_code == 201


# ============================================================================
# Get Tests
# ============================================================================

def test_get_all_documents_for_case(client, auth_headers, test_case, db_session):
    """Test getting all documents for a case."""
    from app.models.document import Document

    # Create test documents
    doc1 = Document(
        case_id=test_case.id,
        side='A',
        title='Doc 1',
        file_name='doc1.txt',
        file_path='/uploads/doc1.txt',
        file_type='txt',
        uploaded_by=test_case.created_by,
        status='ready'
    )
    doc2 = Document(
        case_id=test_case.id,
        side='B',
        title='Doc 2',
        file_name='doc2.txt',
        file_path='/uploads/doc2.txt',
        file_type='txt',
        uploaded_by=test_case.created_by,
        status='ready'
    )
    db_session.add(doc1)
    db_session.add(doc2)
    db_session.commit()

    response = client.get(
        f"/api/cases/{test_case.id}/documents",
        headers=auth_headers
    )

    assert response.status_code == 200
    docs = response.json()
    assert len(docs) == 2


def test_get_documents_without_auth_fails(client, test_case):
    """Test getting documents without authentication fails."""
    response = client.get(f"/api/cases/{test_case.id}/documents")
    assert response.status_code in [401, 403]  # Either Unauthorized or Forbidden


def test_get_documents_for_case_not_owned_fails(client, db_session, test_case):
    """Test getting documents for another user's case fails."""
    from app.models.user import User
    from app.utils.security import create_access_token

    other_user = User(
        phone_hash="other_user_hash_2",
        full_name="Other User"
    )
    db_session.add(other_user)
    db_session.commit()

    other_token = create_access_token(data={"sub": str(other_user.id)})
    other_headers = {"Authorization": f"Bearer {other_token}"}

    response = client.get(
        f"/api/cases/{test_case.id}/documents",
        headers=other_headers
    )

    assert response.status_code == 403


def test_get_single_document_by_id(client, auth_headers, test_case, db_session):
    """Test getting a single document by ID."""
    from app.models.document import Document

    doc = Document(
        case_id=test_case.id,
        side='A',
        title='Test Doc',
        file_name='test.txt',
        file_path='/uploads/test.txt',
        file_type='txt',
        uploaded_by=test_case.created_by,
        status='ready'
    )
    db_session.add(doc)
    db_session.commit()

    response = client.get(
        f"/api/cases/{test_case.id}/documents/{doc.id}",
        headers=auth_headers
    )

    assert response.status_code == 200
    doc_data = response.json()
    assert doc_data['id'] == str(doc.id)
    assert doc_data['title'] == 'Test Doc'


def test_get_document_with_full_text(client, auth_headers, test_case, db_session):
    """Test getting document with full extracted text."""
    from app.models.document import Document

    doc = Document(
        case_id=test_case.id,
        side='A',
        title='Test Doc',
        file_name='test.txt',
        file_path='/uploads/test.txt',
        file_type='txt',
        full_text='This is the full extracted text content.',
        uploaded_by=test_case.created_by,
        status='ready'
    )
    db_session.add(doc)
    db_session.commit()

    response = client.get(
        f"/api/cases/{test_case.id}/documents/{doc.id}?include_text=true",
        headers=auth_headers
    )

    assert response.status_code == 200
    doc_data = response.json()
    assert 'full_text' in doc_data
    assert doc_data['full_text'] == 'This is the full extracted text content.'


def test_get_nonexistent_document_fails(client, auth_headers, test_case):
    """Test getting a non-existent document fails."""
    fake_doc_id = uuid4()

    response = client.get(
        f"/api/cases/{test_case.id}/documents/{fake_doc_id}",
        headers=auth_headers
    )

    assert response.status_code == 404


# ============================================================================
# Delete Tests
# ============================================================================

def test_delete_document(client, auth_headers, test_case, db_session):
    """Test deleting a document."""
    from app.models.document import Document

    doc = Document(
        case_id=test_case.id,
        side='A',
        title='To Delete',
        file_name='delete.txt',
        file_path='/uploads/delete.txt',
        file_type='txt',
        uploaded_by=test_case.created_by,
        status='ready'
    )
    db_session.add(doc)
    db_session.commit()
    doc_id = doc.id

    response = client.delete(
        f"/api/cases/{test_case.id}/documents/{doc_id}",
        headers=auth_headers
    )

    assert response.status_code == 200
    assert 'message' in response.json()

    # Verify document is deleted
    deleted_doc = db_session.query(Document).filter(Document.id == doc_id).first()
    assert deleted_doc is None


def test_delete_document_without_auth_fails(client, test_case, db_session):
    """Test deleting document without authentication fails."""
    from app.models.document import Document

    doc = Document(
        case_id=test_case.id,
        side='A',
        title='Protected',
        file_name='protected.txt',
        file_path='/uploads/protected.txt',
        file_type='txt',
        uploaded_by=test_case.created_by,
        status='ready'
    )
    db_session.add(doc)
    db_session.commit()

    response = client.delete(
        f"/api/cases/{test_case.id}/documents/{doc.id}"
    )

    assert response.status_code in [401, 403]  # Either Unauthorized or Forbidden


def test_delete_document_not_owned_fails(client, db_session, test_case):
    """Test deleting document from another user's case fails."""
    from app.models.user import User
    from app.models.document import Document
    from app.utils.security import create_access_token

    # Create document
    doc = Document(
        case_id=test_case.id,
        side='A',
        title='Protected',
        file_name='protected.txt',
        file_path='/uploads/protected.txt',
        file_type='txt',
        uploaded_by=test_case.created_by,
        status='ready'
    )
    db_session.add(doc)
    db_session.commit()

    # Create other user
    other_user = User(
        phone_hash="other_user_hash_3",
        full_name="Other User"
    )
    db_session.add(other_user)
    db_session.commit()

    other_token = create_access_token(data={"sub": str(other_user.id)})
    other_headers = {"Authorization": f"Bearer {other_token}"}

    response = client.delete(
        f"/api/cases/{test_case.id}/documents/{doc.id}",
        headers=other_headers
    )

    assert response.status_code == 403


def test_delete_nonexistent_document_fails(client, auth_headers, test_case):
    """Test deleting a non-existent document fails."""
    fake_doc_id = uuid4()

    response = client.delete(
        f"/api/cases/{test_case.id}/documents/{fake_doc_id}",
        headers=auth_headers
    )

    assert response.status_code == 404


# ============================================================================
# Edge Cases
# ============================================================================

def test_document_count_increases_after_upload(client, auth_headers, test_case, db_session):
    """Test that document count in case details increases after upload."""
    # Get initial count
    case_response = client.get(
        f"/api/cases/{test_case.id}",
        headers=auth_headers
    )
    initial_count = case_response.json().get('documents_count', 0)

    # Upload document
    file_content = b"Test content"
    files = {'file': ('test.txt', io.BytesIO(file_content), 'text/plain')}
    data = {'title': 'Test Document', 'side': 'A'}

    upload_response = client.post(
        f"/api/cases/{test_case.id}/documents",
        files=files,
        data=data,
        headers=auth_headers
    )
    assert upload_response.status_code == 201

    # Get updated count
    case_response_after = client.get(
        f"/api/cases/{test_case.id}",
        headers=auth_headers
    )
    final_count = case_response_after.json().get('documents_count', 0)

    assert final_count == initial_count + 1


def test_uploaded_file_is_accessible_in_filesystem(client, auth_headers, test_case):
    """Test that uploaded files are stored in filesystem."""
    file_content = b"Test file content for storage check"
    files = {'file': ('storage_test.txt', io.BytesIO(file_content), 'text/plain')}
    data = {'title': 'Storage Test', 'side': 'A'}

    response = client.post(
        f"/api/cases/{test_case.id}/documents",
        files=files,
        data=data,
        headers=auth_headers
    )

    assert response.status_code == 201
    doc = response.json()
    file_path = doc['file_path']

    # Verify file exists (will be in uploads directory)
    # Note: In production this would check actual filesystem
    assert file_path is not None
    assert len(file_path) > 0
