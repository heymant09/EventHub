import pytest
from fastapi import status
from fastapi.testclient import TestClient

# Helper function to register a user and obtain JWT token (used in some tests)
def _register_and_login(client: TestClient, payload: dict) -> str:
    # Register
    reg = client.post("/api/v1/auth/register", json=payload)
    assert reg.status_code == status.HTTP_201_CREATED, f"Register failed: {reg.text}"
    # Login
    login = client.post(
        "/api/v1/auth/login",
        json={"email": payload["email"], "password": payload["password"]},
    )
    assert login.status_code == status.HTTP_200_OK, f"Login failed: {login.text}"
    return login.json()["access_token"]


def test_register_success(client):
    payload = {
        "name": "Test User",
        "email": "test@example.com",
        "password": "StrongPass123!",
    }
    resp = client.post("/api/v1/auth/register", json=payload)
    assert resp.status_code == status.HTTP_201_CREATED
    data = resp.json()
    assert data["email"] == payload["email"]
    assert "id" in data

def test_register_duplicate_email(client):
    payload = {
        "name": "Duplicate User",
        "email": "duplicate@example.com",
        "password": "StrongPass123!",
    }

    first = client.post("/api/v1/auth/register", json=payload)
    assert first.status_code == 201

    second = client.post("/api/v1/auth/register", json=payload)
    assert second.status_code == 409


def test_new_user_default_role(client):
    payload = {
        "name": "Attendee User",
        "email": "attendee@example.com",
        "password": "StrongPass123!",
    }

    response = client.post("/api/v1/auth/register", json=payload)

    assert response.status_code == 201
    assert response.json()["role"] == "attendee"

def test_register_missing_fields(client):
    payload = {"email": "missingname@example.com", "password": "StrongPass123!"}
    resp = client.post("/api/v1/auth/register", json=payload)
    assert resp.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_register_invalid_email(client):
    payload = {
        "name": "Bad Email",
        "email": "not-an-email",
        "password": "StrongPass123!",
    }
    resp = client.post("/api/v1/auth/register", json=payload)
    assert resp.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_register_short_password(client):
    payload = {
        "name": "Short Pass",
        "email": "shortpass@example.com",
        "password": "123",
    }
    resp = client.post("/api/v1/auth/register", json=payload)
    assert resp.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_login_success(client):
    payload = {
        "name": "Login User",
        "email": "login@example.com",
        "password": "StrongPass123!",
    }
    token = _register_and_login(client, payload)
    assert token  # token returned by helper ensures login succeeded


def test_login_nonexistent_email(client):
    resp = client.post(
        "/api/v1/auth/login",
        json={"email": "doesnotexist@example.com", "password": "any"},
    )
    assert resp.status_code == status.HTTP_401_UNAUTHORIZED


def test_login_invalid_password(client):
    payload = {
        "name": "Wrong Pass",
        "email": "wrongpass@example.com",
        "password": "StrongPass123!",
    }
    # Register correctly first
    reg = client.post("/api/v1/auth/register", json=payload)
    assert reg.status_code == status.HTTP_201_CREATED
    # Attempt login with wrong password
    resp = client.post(
        "/api/v1/auth/login",
        json={"email": payload["email"], "password": "BadPassword"},
    )
    assert resp.status_code == status.HTTP_401_UNAUTHORIZED


def test_protected_endpoint_missing_jwt(client):
    resp = client.get("/api/v1/users/me")
    assert resp.status_code == status.HTTP_401_UNAUTHORIZED


def test_protected_endpoint_invalid_jwt(client):
    headers = {"Authorization": "Bearer invalidtoken"}
    resp = client.get("/api/v1/users/me", headers=headers)
    assert resp.status_code == status.HTTP_401_UNAUTHORIZED


def test_protected_endpoint_valid_jwt(client, admin_token):
    headers = {"Authorization": f"Bearer {admin_token}"}
    resp = client.get("/api/v1/users/me", headers=headers)
    assert resp.status_code == status.HTTP_200_OK
    data = resp.json()
    assert data["email"] == "admin@example.com"
