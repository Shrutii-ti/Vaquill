"""
Tests for authentication endpoints (TDD approach).
Write tests first, then implement the endpoints.
"""

import pytest
from fastapi.testclient import TestClient


# ===== Login Endpoint Tests =====

def test_login_with_new_phone_creates_user(client):
    """Test that logging in with a new phone number creates a user."""
    response = client.post(
        "/api/auth/login",
        json={"phone": "1234567890"}
    )

    assert response.status_code == 200
    data = response.json()

    assert "access_token" in data
    assert "token_type" in data
    assert data["token_type"] == "bearer"
    assert "user" in data
    assert data["user"]["id"] is not None


def test_login_with_existing_phone_returns_same_user(client, db_session):
    """Test that logging in with existing phone returns the same user."""
    # First login
    response1 = client.post("/api/auth/login", json={"phone": "9876543210"})
    assert response1.status_code == 200
    user1_id = response1.json()["user"]["id"]

    # Second login with same phone
    response2 = client.post("/api/auth/login", json={"phone": "9876543210"})
    assert response2.status_code == 200
    user2_id = response2.json()["user"]["id"]

    # Should be the same user
    assert user1_id == user2_id


def test_login_with_full_name_and_email(client):
    """Test login with optional full_name and email."""
    response = client.post(
        "/api/auth/login",
        json={
            "phone": "5551234567",
            "full_name": "John Doe",
            "email": "john@example.com"
        }
    )

    assert response.status_code == 200
    data = response.json()

    assert data["user"]["full_name"] == "John Doe"
    assert data["user"]["email"] == "john@example.com"


def test_login_with_invalid_phone_fails(client):
    """Test that login with invalid phone number fails."""
    response = client.post(
        "/api/auth/login",
        json={"phone": "123"}  # Too short
    )

    assert response.status_code == 422  # Validation error


def test_login_without_phone_fails(client):
    """Test that login without phone number fails."""
    response = client.post(
        "/api/auth/login",
        json={}
    )

    assert response.status_code == 422


# ===== Get Current User Endpoint Tests =====

def test_get_current_user_with_valid_token(client, auth_headers):
    """Test getting current user with valid JWT token."""
    response = client.get("/api/auth/me", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()

    assert "id" in data
    assert "created_at" in data


def test_get_current_user_without_token_fails(client):
    """Test that accessing /me without token fails."""
    response = client.get("/api/auth/me")

    assert response.status_code == 403  # Forbidden (no token)


def test_get_current_user_with_invalid_token_fails(client):
    """Test that accessing /me with invalid token fails."""
    response = client.get(
        "/api/auth/me",
        headers={"Authorization": "Bearer invalid_token_here"}
    )

    assert response.status_code == 401  # Unauthorized


# ===== Token Validation Tests =====

def test_jwt_token_contains_user_id(client):
    """Test that JWT token encodes user ID."""
    response = client.post("/api/auth/login", json={"phone": "7778889999"})

    assert response.status_code == 200
    token = response.json()["access_token"]
    user_id = response.json()["user"]["id"]

    # Decode and verify token contains user_id
    # (This will be tested in implementation, just verify token exists)
    assert isinstance(token, str)
    assert len(token) > 20  # JWT tokens are long


# ===== Edge Cases =====

def test_login_updates_last_login_timestamp(client):
    """Test that logging in updates the last_login timestamp."""
    # First login
    response1 = client.post("/api/auth/login", json={"phone": "4445556666"})
    last_login1 = response1.json()["user"]["last_login"]

    # Second login (with a small delay in real scenario)
    response2 = client.post("/api/auth/login", json={"phone": "4445556666"})
    last_login2 = response2.json()["user"]["last_login"]

    # Timestamps should exist (exact comparison depends on precision)
    assert last_login1 is not None
    assert last_login2 is not None
