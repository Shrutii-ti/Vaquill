"""
Tests for Case CRUD endpoints (TDD approach).
"""

import pytest
from fastapi.testclient import TestClient


# ===== Create Case Tests =====

def test_create_case_with_valid_data(client, auth_headers):
    """Test creating a case with valid data."""
    response = client.post(
        "/api/cases",
        headers=auth_headers,
        json={
            "title": "Contract Dispute Case",
            "description": "Dispute over breach of contract terms",
            "case_type": "civil",
            "jurisdiction": "India"
        }
    )

    assert response.status_code == 201
    data = response.json()

    assert data["title"] == "Contract Dispute Case"
    assert data["case_type"] == "civil"
    assert data["jurisdiction"] == "India"
    assert data["status"] == "draft"
    assert data["current_round"] == 0
    assert "case_number" in data
    assert data["case_number"].startswith("CAS-")


def test_create_case_without_auth_fails(client):
    """Test that creating a case without auth fails."""
    response = client.post(
        "/api/cases",
        json={
            "title": "Test Case",
            "case_type": "civil",
            "jurisdiction": "India"
        }
    )

    assert response.status_code == 403  # Forbidden


def test_create_case_with_missing_fields_fails(client, auth_headers):
    """Test that creating a case without required fields fails."""
    response = client.post(
        "/api/cases",
        headers=auth_headers,
        json={
            "title": "Test Case"
            # Missing case_type and jurisdiction
        }
    )

    assert response.status_code == 422  # Validation error


def test_create_case_with_optional_description(client, auth_headers):
    """Test creating a case with optional description."""
    response = client.post(
        "/api/cases",
        headers=auth_headers,
        json={
            "title": "Simple Case",
            "case_type": "criminal",
            "jurisdiction": "USA-CA"
        }
    )

    assert response.status_code == 201
    data = response.json()
    assert data["description"] is None


# ===== Get Cases Tests =====

def test_get_all_cases_returns_user_cases(client, auth_headers, test_case):
    """Test getting all cases returns only user's cases."""
    response = client.get("/api/cases", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()

    assert isinstance(data, list)
    assert len(data) >= 1
    # Verify test_case is in the list
    case_ids = [case["id"] for case in data]
    assert str(test_case.id) in case_ids


def test_get_all_cases_without_auth_fails(client):
    """Test that getting cases without auth fails."""
    response = client.get("/api/cases")

    assert response.status_code == 403


def test_get_all_cases_empty_list_for_new_user(client, db_session):
    """Test that new user gets empty case list."""
    # Create new user and login
    login_response = client.post(
        "/api/auth/login",
        json={"phone": "9999999999"}
    )
    new_token = login_response.json()["access_token"]
    new_headers = {"Authorization": f"Bearer {new_token}"}

    # Get cases
    response = client.get("/api/cases", headers=new_headers)

    assert response.status_code == 200
    assert response.json() == []


# ===== Get Single Case Tests =====

def test_get_case_by_id(client, auth_headers, test_case):
    """Test getting a specific case by ID."""
    response = client.get(
        f"/api/cases/{test_case.id}",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()

    assert data["id"] == str(test_case.id)
    assert data["title"] == test_case.title
    assert data["case_number"] == test_case.case_number


def test_get_case_with_invalid_id_fails(client, auth_headers):
    """Test that getting a case with invalid ID fails."""
    response = client.get(
        "/api/cases/invalid-uuid-here",
        headers=auth_headers
    )

    assert response.status_code == 422  # Validation error


def test_get_case_not_found(client, auth_headers):
    """Test getting a non-existent case."""
    from uuid import uuid4
    fake_id = uuid4()

    response = client.get(
        f"/api/cases/{fake_id}",
        headers=auth_headers
    )

    assert response.status_code == 404


def test_get_case_owned_by_different_user_fails(client, db_session, test_case):
    """Test that user cannot access another user's case."""
    # Create different user
    other_login = client.post(
        "/api/auth/login",
        json={"phone": "8888888888"}
    )
    other_token = other_login.json()["access_token"]
    other_headers = {"Authorization": f"Bearer {other_token}"}

    # Try to access test_case (owned by test_user)
    response = client.get(
        f"/api/cases/{test_case.id}",
        headers=other_headers
    )

    assert response.status_code == 403  # Forbidden


# ===== Update Case Tests =====

def test_update_case_title(client, auth_headers, test_case):
    """Test updating case title."""
    response = client.patch(
        f"/api/cases/{test_case.id}",
        headers=auth_headers,
        json={"title": "Updated Title"}
    )

    assert response.status_code == 200
    data = response.json()

    assert data["title"] == "Updated Title"
    assert data["case_type"] == test_case.case_type  # Unchanged


def test_update_case_status(client, auth_headers, test_case):
    """Test updating case status."""
    response = client.patch(
        f"/api/cases/{test_case.id}",
        headers=auth_headers,
        json={"status": "in_progress"}
    )

    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "in_progress"


def test_update_case_without_auth_fails(client, test_case):
    """Test that updating without auth fails."""
    response = client.patch(
        f"/api/cases/{test_case.id}",
        json={"title": "New Title"}
    )

    assert response.status_code == 403


def test_update_case_not_owned_fails(client, db_session, test_case):
    """Test that updating another user's case fails."""
    # Different user
    other_login = client.post(
        "/api/auth/login",
        json={"phone": "7777777777"}
    )
    other_token = other_login.json()["access_token"]
    other_headers = {"Authorization": f"Bearer {other_token}"}

    response = client.patch(
        f"/api/cases/{test_case.id}",
        headers=other_headers,
        json={"title": "Hacked Title"}
    )

    assert response.status_code == 403


# ===== Delete Case Tests =====

def test_delete_case(client, auth_headers, test_case):
    """Test deleting a case."""
    response = client.delete(
        f"/api/cases/{test_case.id}",
        headers=auth_headers
    )

    assert response.status_code == 200

    # Verify case is deleted
    get_response = client.get(
        f"/api/cases/{test_case.id}",
        headers=auth_headers
    )
    assert get_response.status_code == 404


def test_delete_case_without_auth_fails(client, test_case):
    """Test that deleting without auth fails."""
    response = client.delete(f"/api/cases/{test_case.id}")

    assert response.status_code == 403


def test_delete_case_not_owned_fails(client, db_session, test_case):
    """Test that deleting another user's case fails."""
    # Different user
    other_login = client.post(
        "/api/auth/login",
        json={"phone": "6666666666"}
    )
    other_token = other_login.json()["access_token"]
    other_headers = {"Authorization": f"Bearer {other_token}"}

    response = client.delete(
        f"/api/cases/{test_case.id}",
        headers=other_headers
    )

    assert response.status_code == 403


def test_delete_nonexistent_case_fails(client, auth_headers):
    """Test deleting a non-existent case."""
    from uuid import uuid4
    fake_id = uuid4()

    response = client.delete(
        f"/api/cases/{fake_id}",
        headers=auth_headers
    )

    assert response.status_code == 404


# ===== Case Number Generation Test =====

def test_case_numbers_are_unique(client, auth_headers):
    """Test that case numbers are unique."""
    # Create multiple cases
    case1 = client.post(
        "/api/cases",
        headers=auth_headers,
        json={"title": "Case 1", "case_type": "civil", "jurisdiction": "India"}
    )
    case2 = client.post(
        "/api/cases",
        headers=auth_headers,
        json={"title": "Case 2", "case_type": "civil", "jurisdiction": "India"}
    )

    assert case1.status_code == 201
    assert case2.status_code == 201

    case1_number = case1.json()["case_number"]
    case2_number = case2.json()["case_number"]

    assert case1_number != case2_number
    assert case1_number.startswith("CAS-")
    assert case2_number.startswith("CAS-")
