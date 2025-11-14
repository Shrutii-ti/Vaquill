"""
Test suite for VerdictOrchestrator (TDD RED phase).
"""

import pytest
import json
from unittest.mock import Mock, patch
from datetime import datetime


@pytest.fixture
def mock_openai_client():
    """Mock OpenAI client for testing."""
    with patch('app.services.openai_service.OpenAI') as mock_client:
        yield mock_client


@pytest.fixture
def case_with_documents(db_session, test_case):
    """Create a case with documents on both sides."""
    from app.models.document import Document

    # Side A documents
    doc_a1 = Document(
        case_id=test_case.id,
        side='A',
        title='Contract Agreement',
        file_name='contract.pdf',
        file_path='/uploads/contract.pdf',
        file_type='pdf',
        full_text='Contract states that Party A agrees to deliver goods by Jan 1, 2025. Payment terms: 30 days net.',
        word_count=15,
        page_count=1,
        uploaded_by=test_case.created_by,
        status='ready'
    )

    doc_a2 = Document(
        case_id=test_case.id,
        side='A',
        title='Email Evidence',
        file_name='email.txt',
        file_path='/uploads/email.txt',
        file_type='txt',
        full_text='Email from Party B dated Dec 15: "We confirm receipt of goods and will process payment."',
        word_count=16,
        page_count=1,
        uploaded_by=test_case.created_by,
        status='ready'
    )

    # Side B documents
    doc_b1 = Document(
        case_id=test_case.id,
        side='B',
        title='Delivery Receipt',
        file_name='receipt.pdf',
        file_path='/uploads/receipt.pdf',
        file_type='pdf',
        full_text='Receipt shows goods delivered on Jan 5, 2025 - 4 days late. Quality issues noted.',
        word_count=14,
        page_count=1,
        uploaded_by=test_case.created_by,
        status='ready'
    )

    doc_b2 = Document(
        case_id=test_case.id,
        side='B',
        title='Quality Report',
        file_name='quality.txt',
        file_path='/uploads/quality.txt',
        file_type='txt',
        full_text='Quality inspection found 15% of goods defective. Does not meet contract specifications.',
        word_count=12,
        page_count=1,
        uploaded_by=test_case.created_by,
        status='ready'
    )

    db_session.add_all([doc_a1, doc_a2, doc_b1, doc_b2])
    db_session.commit()

    return test_case


# ============================================================================
# Context Fetching Tests
# ============================================================================

def test_fetch_case_context(db_session, case_with_documents):
    """Test fetching case context with documents."""
    from app.services.verdict_orchestrator import VerdictOrchestrator

    context = VerdictOrchestrator.fetch_case_context(case_with_documents.id, db_session)

    assert context is not None
    assert 'case' in context
    assert 'side_a_docs' in context
    assert 'side_b_docs' in context
    assert len(context['side_a_docs']) == 2
    assert len(context['side_b_docs']) == 2
    assert context['case'].id == case_with_documents.id


def test_fetch_case_context_nonexistent_case(db_session):
    """Test fetching context for non-existent case raises error."""
    from app.services.verdict_orchestrator import VerdictOrchestrator
    from uuid import uuid4

    with pytest.raises(Exception):
        VerdictOrchestrator.fetch_case_context(uuid4(), db_session)


def test_validate_documents_both_sides_present(db_session, case_with_documents):
    """Test validation passes when both sides have documents."""
    from app.services.verdict_orchestrator import VerdictOrchestrator

    context = VerdictOrchestrator.fetch_case_context(case_with_documents.id, db_session)

    # Should not raise exception
    VerdictOrchestrator.validate_documents(context)


def test_validate_documents_missing_side_a(db_session, test_case):
    """Test validation fails when Side A has no documents."""
    from app.services.verdict_orchestrator import VerdictOrchestrator
    from app.models.document import Document

    # Only add Side B document
    doc_b = Document(
        case_id=test_case.id,
        side='B',
        title='Doc B',
        file_name='doc_b.txt',
        file_path='/uploads/doc_b.txt',
        file_type='txt',
        full_text='Content',
        uploaded_by=test_case.created_by,
        status='ready'
    )
    db_session.add(doc_b)
    db_session.commit()

    context = VerdictOrchestrator.fetch_case_context(test_case.id, db_session)

    with pytest.raises(ValueError, match="Side A"):
        VerdictOrchestrator.validate_documents(context)


def test_validate_documents_missing_side_b(db_session, test_case):
    """Test validation fails when Side B has no documents."""
    from app.services.verdict_orchestrator import VerdictOrchestrator
    from app.models.document import Document

    # Only add Side A document
    doc_a = Document(
        case_id=test_case.id,
        side='A',
        title='Doc A',
        file_name='doc_a.txt',
        file_path='/uploads/doc_a.txt',
        file_type='txt',
        full_text='Content',
        uploaded_by=test_case.created_by,
        status='ready'
    )
    db_session.add(doc_a)
    db_session.commit()

    context = VerdictOrchestrator.fetch_case_context(test_case.id, db_session)

    with pytest.raises(ValueError, match="Side B"):
        VerdictOrchestrator.validate_documents(context)


# ============================================================================
# Prompt Building Tests
# ============================================================================

def test_build_verdict_prompt(db_session, case_with_documents):
    """Test building verdict prompt for GPT."""
    from app.services.verdict_orchestrator import VerdictOrchestrator

    context = VerdictOrchestrator.fetch_case_context(case_with_documents.id, db_session)
    prompt = VerdictOrchestrator.build_verdict_prompt(context, round_number=0)

    assert isinstance(prompt, str)
    assert len(prompt) > 100
    assert 'judge' in prompt.lower() or 'verdict' in prompt.lower()
    assert 'side a' in prompt.lower()  # Check lowercase for case-insensitive match
    assert 'side b' in prompt.lower()  # Check lowercase for case-insensitive match
    assert 'Contract Agreement' in prompt  # Document title
    assert 'Delivery Receipt' in prompt  # Document title


def test_prompt_includes_case_details(db_session, case_with_documents):
    """Test prompt includes case title and type."""
    from app.services.verdict_orchestrator import VerdictOrchestrator

    context = VerdictOrchestrator.fetch_case_context(case_with_documents.id, db_session)
    prompt = VerdictOrchestrator.build_verdict_prompt(context, round_number=0)

    assert case_with_documents.title in prompt
    assert case_with_documents.case_type in prompt


def test_prompt_includes_document_content(db_session, case_with_documents):
    """Test prompt includes actual document text."""
    from app.services.verdict_orchestrator import VerdictOrchestrator

    context = VerdictOrchestrator.fetch_case_context(case_with_documents.id, db_session)
    prompt = VerdictOrchestrator.build_verdict_prompt(context, round_number=0)

    # Check for content from documents
    assert 'Contract states' in prompt
    assert 'Quality inspection' in prompt


# ============================================================================
# Verdict Generation Tests
# ============================================================================

def test_generate_initial_verdict(db_session, case_with_documents, mock_openai_client):
    """Test generating initial verdict (Round 0)."""
    from app.services.verdict_orchestrator import VerdictOrchestrator
    from app.services.openai_service import OpenAIService

    # Mock GPT response with valid verdict JSON
    mock_verdict = {
        "summary": "Contract dispute regarding late delivery and quality issues",
        "winner": "A",
        "confidence_score": 0.75,
        "issues": [
            {
                "issue": "Was delivery on time?",
                "finding": "No - 4 days late",
                "reasoning": "Contract specified Jan 1, delivery was Jan 5"
            },
            {
                "issue": "Were goods of acceptable quality?",
                "finding": "No - 15% defective",
                "reasoning": "Quality report shows defects exceeding tolerance"
            }
        ],
        "final_decision": "Side A has stronger case. Late delivery and quality issues breach contract terms.",
        "key_evidence_cited": ["Contract Agreement", "Quality Report"]
    }

    mock_response = Mock()
    mock_response.choices = [Mock(message=Mock(content=json.dumps(mock_verdict)))]
    mock_response.usage = Mock(total_tokens=500)  # Return actual integer, not Mock

    mock_instance = Mock()
    mock_instance.chat.completions.create.return_value = mock_response
    OpenAIService._client = mock_instance

    # Generate verdict
    verdict = VerdictOrchestrator.generate_initial_verdict(case_with_documents.id, db_session)

    assert verdict is not None
    assert verdict.case_id == case_with_documents.id
    assert verdict.round == 0
    assert verdict.verdict_json is not None
    assert verdict.verdict_json['winner'] in ['A', 'B', 'undecided']
    assert 'summary' in verdict.verdict_json
    assert 'issues' in verdict.verdict_json


def test_verdict_saved_to_database(db_session, case_with_documents, mock_openai_client):
    """Test that generated verdict is saved to database."""
    from app.services.verdict_orchestrator import VerdictOrchestrator
    from app.services.openai_service import OpenAIService
    from app.models.verdict import Verdict

    mock_verdict = {
        "summary": "Test summary",
        "winner": "B",
        "confidence_score": 0.65,
        "issues": [],
        "final_decision": "Test decision",
        "key_evidence_cited": []
    }

    mock_response = Mock()
    mock_response.choices = [Mock(message=Mock(content=json.dumps(mock_verdict)))]
    mock_response.usage = Mock(total_tokens=450)  # Return actual integer

    mock_instance = Mock()
    mock_instance.chat.completions.create.return_value = mock_response
    OpenAIService._client = mock_instance

    # Generate verdict
    verdict = VerdictOrchestrator.generate_initial_verdict(case_with_documents.id, db_session)

    # Verify it's in the database
    db_verdict = db_session.query(Verdict).filter(
        Verdict.case_id == case_with_documents.id,
        Verdict.round == 0
    ).first()

    assert db_verdict is not None
    assert db_verdict.id == verdict.id
    assert db_verdict.verdict_json['winner'] == 'B'


def test_verdict_includes_model_info(db_session, case_with_documents, mock_openai_client):
    """Test verdict includes model and token usage info."""
    from app.services.verdict_orchestrator import VerdictOrchestrator
    from app.services.openai_service import OpenAIService

    mock_verdict = {
        "summary": "Test",
        "winner": "A",
        "confidence_score": 0.8,
        "issues": [],
        "final_decision": "Test",
        "key_evidence_cited": []
    }

    mock_response = Mock()
    mock_response.choices = [Mock(message=Mock(content=json.dumps(mock_verdict)))]
    mock_response.usage = Mock(total_tokens=500)

    mock_instance = Mock()
    mock_instance.chat.completions.create.return_value = mock_response
    OpenAIService._client = mock_instance

    verdict = VerdictOrchestrator.generate_initial_verdict(case_with_documents.id, db_session)

    assert verdict.model_used == 'gpt-4o-mini'
    assert verdict.tokens_used is not None


# ============================================================================
# Verdict Parsing Tests
# ============================================================================

def test_parse_verdict_json_valid():
    """Test parsing valid verdict JSON."""
    from app.services.verdict_orchestrator import VerdictOrchestrator

    valid_json = json.dumps({
        "summary": "Test summary",
        "winner": "A",
        "confidence_score": 0.9,
        "issues": [{"issue": "Test", "finding": "Yes", "reasoning": "Because"}],
        "final_decision": "Decision text",
        "key_evidence_cited": ["Doc 1"]
    })

    result = VerdictOrchestrator.parse_verdict_json(valid_json)

    assert result is not None
    assert result['winner'] == 'A'
    assert result['confidence_score'] == 0.9


def test_parse_verdict_json_invalid():
    """Test parsing invalid JSON raises error."""
    from app.services.verdict_orchestrator import VerdictOrchestrator

    invalid_json = "This is not JSON"

    with pytest.raises(Exception):
        VerdictOrchestrator.parse_verdict_json(invalid_json)


def test_parse_verdict_json_missing_required_fields():
    """Test parsing JSON with missing required fields raises error."""
    from app.services.verdict_orchestrator import VerdictOrchestrator

    incomplete_json = json.dumps({
        "summary": "Test",
        # Missing winner, issues, etc.
    })

    with pytest.raises(Exception):
        VerdictOrchestrator.parse_verdict_json(incomplete_json)


# ============================================================================
# Error Handling Tests
# ============================================================================

def test_generate_verdict_handles_gpt_error(db_session, case_with_documents, mock_openai_client):
    """Test verdict generation handles GPT API errors."""
    from app.services.verdict_orchestrator import VerdictOrchestrator
    from app.services.openai_service import OpenAIService

    # Mock API error
    mock_instance = Mock()
    mock_instance.chat.completions.create.side_effect = Exception("API Error")
    OpenAIService._client = mock_instance

    with pytest.raises(Exception):
        VerdictOrchestrator.generate_initial_verdict(case_with_documents.id, db_session)


def test_cannot_generate_verdict_without_documents(db_session, test_case):
    """Test that verdict generation fails if documents missing."""
    from app.services.verdict_orchestrator import VerdictOrchestrator

    # No documents added
    with pytest.raises(Exception):
        VerdictOrchestrator.generate_initial_verdict(test_case.id, db_session)


# ============================================================================
# Round 0 Specific Tests
# ============================================================================

def test_round_0_verdict_has_no_arguments(db_session, case_with_documents, mock_openai_client):
    """Test Round 0 verdict prompt doesn't include arguments."""
    from app.services.verdict_orchestrator import VerdictOrchestrator

    context = VerdictOrchestrator.fetch_case_context(case_with_documents.id, db_session)
    prompt = VerdictOrchestrator.build_verdict_prompt(context, round_number=0)

    # Round 0 should not mention arguments
    assert 'argument' not in prompt.lower() or 'no arguments yet' in prompt.lower()


def test_only_one_round_0_verdict_per_case(db_session, case_with_documents, mock_openai_client):
    """Test that only one Round 0 verdict can exist per case."""
    from app.services.verdict_orchestrator import VerdictOrchestrator
    from app.services.openai_service import OpenAIService

    mock_verdict = {
        "summary": "Test",
        "winner": "A",
        "confidence_score": 0.8,
        "issues": [],
        "final_decision": "Test",
        "key_evidence_cited": []
    }

    mock_response = Mock()
    mock_response.choices = [Mock(message=Mock(content=json.dumps(mock_verdict)))]
    mock_response.usage = Mock(total_tokens=300)  # Return actual integer

    mock_instance = Mock()
    mock_instance.chat.completions.create.return_value = mock_response
    OpenAIService._client = mock_instance

    # Generate first verdict
    verdict1 = VerdictOrchestrator.generate_initial_verdict(case_with_documents.id, db_session)
    assert verdict1 is not None

    # Try to generate again - should raise error or return existing
    with pytest.raises(Exception, match="already exists"):
        VerdictOrchestrator.generate_initial_verdict(case_with_documents.id, db_session)
