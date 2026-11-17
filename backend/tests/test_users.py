from app.models.user import User
from app.core.security import verify_password


def _register_and_login(client, *, email="member@example.com", password="StrongPass123!"):
    response = client.post("/api/v1/auth/register", json={
        "name": "Member User",
        "email": email,
        "password": password,
    })
    assert response.status_code == 201, response.text
    response = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200, response.text
    return response.json()["access_token"]


def test_admin_can_list_users(client, admin_token):
    response = client.get("/api/v1/users/", headers={"Authorization": f"Bearer {admin_token}"})
    assert response.status_code == 200
    assert response.json()
    assert all("password_hash" not in user for user in response.json())


def test_non_admin_cannot_list_users(client):
    token = _register_and_login(client)
    response = client.get("/api/v1/users/", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 403


def test_user_can_update_own_profile(client):
    token = _register_and_login(client)
    response = client.patch("/api/v1/users/me", headers={"Authorization": f"Bearer {token}"}, json={
        "name": "  Updated Member  ",
        "email": "updated@example.com",
    })
    assert response.status_code == 200, response.text
    assert response.json()["name"] == "Updated Member"
    assert response.json()["email"] == "updated@example.com"


def test_user_can_change_password_with_current_password(client, db_session):
    token = _register_and_login(client)
    response = client.patch("/api/v1/users/me", headers={"Authorization": f"Bearer {token}"}, json={
        "current_password": "StrongPass123!",
        "new_password": "EvenStronger456!",
    })
    assert response.status_code == 200, response.text
    user = db_session.query(User).filter(User.email == "member@example.com").one()
    assert verify_password("EvenStronger456!", user.password_hash)


def test_password_change_rejects_incorrect_current_password(client):
    token = _register_and_login(client)
    response = client.patch("/api/v1/users/me", headers={"Authorization": f"Bearer {token}"}, json={
        "current_password": "wrong password",
        "new_password": "EvenStronger456!",
    })
    assert response.status_code == 400


def test_profile_update_cannot_change_role(client):
    token = _register_and_login(client)
    response = client.patch("/api/v1/users/me", headers={"Authorization": f"Bearer {token}"}, json={
        "name": "Updated Member",
        "role": "admin",
    })
    assert response.status_code == 200
    assert response.json()["role"] == "attendee"


def test_admin_user_list_is_paginated(client, admin_token):
    for index in range(3):
        client.post("/api/v1/auth/register", json={
            "name": f"Page User {index}",
            "email": f"page{index}@example.com",
            "password": "StrongPass123!",
        })
    response = client.get("/api/v1/users/?skip=1&limit=2", headers={"Authorization": f"Bearer {admin_token}"})
    assert response.status_code == 200
    assert len(response.json()) == 2
