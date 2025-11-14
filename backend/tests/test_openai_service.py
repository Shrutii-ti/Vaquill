"""
Test suite for OpenAI service (TDD RED phase).
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import tempfile


@pytest.fixture
def mock_openai_client():
    """Mock OpenAI client for testing."""
    with patch('app.services.openai_service.OpenAI') as mock_client:
        yield mock_client


@pytest.fixture
def sample_txt_file():
    """Create a temporary text file for testing."""
    content = "This is a sample legal document.\nIt contains multiple lines.\nAnd some legal terms."
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write(content)
        temp_path = f.name
    yield temp_path
    # Cleanup
    Path(temp_path).unlink(missing_ok=True)


@pytest.fixture
def sample_pdf_file():
    """Create a temporary PDF file for testing."""
    # Create a simple PDF-like file (not a real PDF, just for testing)
    content = b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n>>\nendobj\nThis is PDF content."
    with tempfile.NamedTemporaryFile(mode='wb', suffix='.pdf', delete=False) as f:
        f.write(content)
        temp_path = f.name
    yield temp_path
    # Cleanup
    Path(temp_path).unlink(missing_ok=True)


# ============================================================================
# Text Extraction Tests
# ============================================================================

def test_extract_text_from_txt_file(sample_txt_file, mock_openai_client):
    """Test extracting text from a plain text file."""
    from app.services.openai_service import OpenAIService

    result = OpenAIService.extract_text_from_file(sample_txt_file, 'txt')

    assert result is not None
    assert 'full_text' in result
    assert 'word_count' in result
    assert 'page_count' in result
    assert len(result['full_text']) > 0
    assert result['word_count'] > 0
    assert result['page_count'] >= 1


def test_extract_text_from_pdf_with_gpt(sample_pdf_file, mock_openai_client):
    """Test extracting text from PDF using GPT-4o-mini."""
    from app.services.openai_service import OpenAIService

    # Mock GPT response
    mock_response = Mock()
    mock_response.choices = [Mock(message=Mock(content="Extracted PDF text content here"))]
    mock_openai_client.return_value.chat.completions.create.return_value = mock_response

    result = OpenAIService.extract_text_from_file(sample_pdf_file, 'pdf')

    assert result is not None
    assert 'full_text' in result
    assert result['full_text'] == "Extracted PDF text content here"
    assert result['word_count'] > 0


def test_extract_text_handles_empty_file():
    """Test extraction from empty file."""
    from app.services.openai_service import OpenAIService

    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        temp_path = f.name

    try:
        result = OpenAIService.extract_text_from_file(temp_path, 'txt')
        assert result['full_text'] == ""
        assert result['word_count'] == 0
    finally:
        Path(temp_path).unlink(missing_ok=True)


def test_extract_text_from_nonexistent_file():
    """Test extraction from non-existent file raises error."""
    from app.services.openai_service import OpenAIService

    with pytest.raises(FileNotFoundError):
        OpenAIService.extract_text_from_file('/nonexistent/file.txt', 'txt')


def test_extract_text_from_unsupported_type():
    """Test extraction from unsupported file type raises error."""
    from app.services.openai_service import OpenAIService

    with tempfile.NamedTemporaryFile(mode='w', suffix='.exe', delete=False) as f:
        temp_path = f.name

    try:
        with pytest.raises(ValueError):
            OpenAIService.extract_text_from_file(temp_path, 'exe')
    finally:
        Path(temp_path).unlink(missing_ok=True)


# ============================================================================
# Word Count Tests
# ============================================================================

def test_count_words():
    """Test word counting functionality."""
    from app.services.openai_service import OpenAIService

    text = "This is a test document with ten words in it."
    count = OpenAIService.count_words(text)
    assert count == 10


def test_count_words_empty_string():
    """Test word count for empty string."""
    from app.services.openai_service import OpenAIService

    count = OpenAIService.count_words("")
    assert count == 0


def test_count_words_with_special_characters():
    """Test word count with special characters."""
    from app.services.openai_service import OpenAIService

    text = "Hello, world! This is a test... with special-characters."
    count = OpenAIService.count_words(text)
    assert count > 0


# ============================================================================
# Document Processing Integration Tests
# ============================================================================

@pytest.mark.asyncio
async def test_process_document_updates_status(db_session, test_case, sample_txt_file, mock_openai_client):
    """Test that document processing updates status correctly."""
    from app.models.document import Document
    from app.services.openai_service import OpenAIService

    # Create a document
    doc = Document(
        case_id=test_case.id,
        side='A',
        title='Test Doc',
        file_name='test.txt',
        file_path=sample_txt_file,
        file_type='txt',
        uploaded_by=test_case.created_by,
        status='pending'
    )
    db_session.add(doc)
    db_session.commit()

    # Process document
    await OpenAIService.process_document(doc.id, db_session)

    # Refresh to get updated status
    db_session.refresh(doc)

    assert doc.status == 'ready'
    assert doc.full_text is not None
    assert doc.word_count > 0


@pytest.mark.asyncio
async def test_process_document_handles_errors(db_session, test_case):
    """Test that document processing handles errors gracefully."""
    from app.models.document import Document
    from app.services.openai_service import OpenAIService

    # Create a document with non-existent file
    doc = Document(
        case_id=test_case.id,
        side='A',
        title='Test Doc',
        file_name='nonexistent.txt',
        file_path='/nonexistent/file.txt',
        file_type='txt',
        uploaded_by=test_case.created_by,
        status='pending'
    )
    db_session.add(doc)
    db_session.commit()

    # Process document (should fail)
    await OpenAIService.process_document(doc.id, db_session)

    # Refresh to get updated status
    db_session.refresh(doc)

    assert doc.status == 'failed'


@pytest.mark.asyncio
async def test_process_document_with_pdf(db_session, test_case, sample_pdf_file, mock_openai_client):
    """Test processing a PDF document."""
    from app.models.document import Document
    from app.services.openai_service import OpenAIService

    # Mock GPT response
    mock_response = Mock()
    mock_response.choices = [Mock(message=Mock(content="Extracted PDF text content here"))]

    # Mock the client instance and its methods
    mock_instance = Mock()
    mock_instance.chat.completions.create.return_value = mock_response

    # Reset client to use mock
    OpenAIService._client = mock_instance

    # Create a document
    doc = Document(
        case_id=test_case.id,
        side='A',
        title='PDF Doc',
        file_name='test.pdf',
        file_path=sample_pdf_file,
        file_type='pdf',
        uploaded_by=test_case.created_by,
        status='pending'
    )
    db_session.add(doc)
    db_session.commit()

    # Process document
    await OpenAIService.process_document(doc.id, db_session)

    # Refresh to get updated status
    db_session.refresh(doc)

    assert doc.status == 'ready'
    assert doc.full_text == "Extracted PDF text content here"


# ============================================================================
# OpenAI API Call Tests
# ============================================================================

def test_call_gpt_for_extraction(mock_openai_client):
    """Test calling GPT-4o-mini for text extraction."""
    from app.services.openai_service import OpenAIService

    # Mock response
    mock_response = Mock()
    mock_response.choices = [Mock(message=Mock(content="Extracted PDF text content here"))]

    # Mock the client instance and its methods
    mock_instance = Mock()
    mock_instance.chat.completions.create.return_value = mock_response
    mock_openai_client.return_value = mock_instance

    # Reset client to use mock
    OpenAIService._client = mock_instance

    result = OpenAIService.call_gpt_for_extraction("Raw file content here", 'pdf')

    assert result == "Extracted PDF text content here"

    # Verify GPT was called with correct parameters
    mock_instance.chat.completions.create.assert_called_once()
    call_args = mock_instance.chat.completions.create.call_args
    assert call_args[1]['model'] == 'gpt-4o-mini'


def test_call_gpt_handles_api_error(mock_openai_client):
    """Test that GPT call handles API errors."""
    from app.services.openai_service import OpenAIService

    # Mock API error
    mock_instance = Mock()
    mock_instance.chat.completions.create.side_effect = Exception("API Error")

    # Reset client to use mock
    OpenAIService._client = mock_instance

    with pytest.raises(Exception):
        OpenAIService.call_gpt_for_extraction("Content", 'pdf')


def test_build_extraction_prompt():
    """Test building extraction prompt for GPT."""
    from app.services.openai_service import OpenAIService

    content = "Raw document content"
    file_type = "pdf"

    prompt = OpenAIService.build_extraction_prompt(content, file_type)

    assert isinstance(prompt, str)
    assert len(prompt) > 0
    assert 'extract' in prompt.lower() or 'text' in prompt.lower()
    assert file_type in prompt.lower()


# ============================================================================
# Batch Processing Tests
# ============================================================================

@pytest.mark.asyncio
async def test_process_pending_documents(db_session, test_case, sample_txt_file, mock_openai_client):
    """Test batch processing of pending documents."""
    from app.models.document import Document
    from app.services.openai_service import OpenAIService

    # Create multiple pending documents
    doc1 = Document(
        case_id=test_case.id,
        side='A',
        title='Doc 1',
        file_name='test1.txt',
        file_path=sample_txt_file,
        file_type='txt',
        uploaded_by=test_case.created_by,
        status='pending'
    )
    doc2 = Document(
        case_id=test_case.id,
        side='B',
        title='Doc 2',
        file_name='test2.txt',
        file_path=sample_txt_file,
        file_type='txt',
        uploaded_by=test_case.created_by,
        status='pending'
    )
    db_session.add_all([doc1, doc2])
    db_session.commit()

    # Process all pending documents
    await OpenAIService.process_pending_documents(db_session)

    # Refresh documents
    db_session.refresh(doc1)
    db_session.refresh(doc2)

    assert doc1.status == 'ready'
    assert doc2.status == 'ready'


# ============================================================================
# Edge Cases
# ============================================================================

def test_extract_very_large_text(mock_openai_client):
    """Test extracting very large text (chunk handling)."""
    from app.services.openai_service import OpenAIService

    # Create a large text file
    large_text = "word " * 10000  # 10000 words

    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write(large_text)
        temp_path = f.name

    try:
        result = OpenAIService.extract_text_from_file(temp_path, 'txt')
        assert result['word_count'] == 10000
    finally:
        Path(temp_path).unlink(missing_ok=True)


def test_extract_text_with_unicode(mock_openai_client):
    """Test extracting text with unicode characters."""
    from app.services.openai_service import OpenAIService

    unicode_text = "This document contains unicode: 你好世界 Здравствуй мир مرحبا بالعالم"

    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
        f.write(unicode_text)
        temp_path = f.name

    try:
        result = OpenAIService.extract_text_from_file(temp_path, 'txt')
        assert '你好世界' in result['full_text']
        assert 'Здравствуй' in result['full_text']
    finally:
        Path(temp_path).unlink(missing_ok=True)
