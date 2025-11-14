"""
Pytest configuration and fixtures for testing.
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
from typing import Generator
import os

from app.main import app
from app.db.database import Base, get_db
from app.models import User, Case, Document, Argument, Verdict

# Test database URL (in-memory SQLite for fast tests)
SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///./test.db"

# Create test engine
test_engine = create_engine(
    SQLALCHEMY_TEST_DATABASE_URL,
    connect_args={"check_same_thread": False}  # Needed for SQLite
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="function")
def db_session() -> Generator:
    """
    Create a fresh database session for each test.
    Automatically rollback after each test.
    """
    # Create all tables
    Base.metadata.create_all(bind=test_engine)

    # Create session
    session = TestingSessionLocal()

    try:
        yield session
    finally:
        session.close()
        # Drop all tables after test
        Base.metadata.drop_all(bind=test_engine)


@pytest.fixture(scope="function")
def client(db_session) -> Generator:
    """
    Create a FastAPI test client with database dependency override.
    """

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture
def test_user(db_session) -> User:
    """
    Create a test user in the database.
    """
    from app.utils.security import get_phone_hash

    user = User(
        phone_hash=get_phone_hash("1234567890"),
        full_name="Test User",
        email="test@example.com"
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def auth_token(test_user) -> str:
    """
    Generate a JWT token for the test user.
    """
    from app.utils.security import create_access_token

    token = create_access_token(data={"sub": str(test_user.id)})
    return token


@pytest.fixture
def auth_headers(auth_token) -> dict:
    """
    Get authorization headers with the test token.
    """
    return {"Authorization": f"Bearer {auth_token}"}


@pytest.fixture
def test_case(db_session, test_user) -> Case:
    """
    Create a test case in the database.
    """
    case = Case(
        case_number="CAS-2025-TEST01",
        title="Test Case",
        description="Test case description",
        case_type="civil",
        jurisdiction="India",
        created_by=test_user.id,
        status="draft"
    )
    db_session.add(case)
    db_session.commit()
    db_session.refresh(case)
    return case


@pytest.fixture
def mock_openai_response():
    """
    Mock OpenAI API response for testing.
    """
    return {
        "summary": "Test verdict summary",
        "winner": "A",
        "confidence_score": 0.85,
        "issues": [
            {
                "issue": "Was contract valid?",
                "finding": "Yes",
                "reasoning": "Test reasoning"
            }
        ],
        "final_decision": "Side A wins",
        "key_evidence_cited": ["Doc A - Contract"]
    }


# Cleanup test database after all tests
def pytest_sessionfinish(session, exitstatus):
    """
    Cleanup after all tests are done.
    """
    if os.path.exists("test.db"):
        os.remove("test.db")
