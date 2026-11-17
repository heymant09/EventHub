
from datetime import datetime, timedelta, timezone


def event_payload(**overrides):
    """Generate valid event data for tests."""

    start_time = datetime.now(timezone.utc) + timedelta(days=7)

    payload = {
        "title": "Python Developer Meetup",
        "description": "A meetup for Python developers to learn and network.",
        "location": "Jaipur",
        "start_time": start_time.isoformat(),
        "end_time": (start_time + timedelta(hours=2)).isoformat(),
        "capacity": 100,
        "category_ids": [],
    }

    payload.update(overrides)
    return payload


def auth_headers(token):
    return {"Authorization": f"Bearer {token}"}


def create_event(client, token, **overrides):
    response = client.post(
        "/api/v1/events/",
        json=event_payload(**overrides),
        headers=auth_headers(token),
    )

    assert response.status_code == 201, response.text
    return response.json()


def test_create_event_as_organiser(client, organiser_token):
    response = client.post(
        "/api/v1/events/",
        json=event_payload(),
        headers=auth_headers(organiser_token),
    )

    assert response.status_code == 201

    data = response.json()

    assert data["title"] == "Python Developer Meetup"
    assert data["location"] == "Jaipur"
    assert data["capacity"] == 100
    assert data["status"] == "draft"
    assert data["organiser_id"] is not None


def test_attendee_cannot_create_event(client):
    user_data = {
        "name": "Attendee User",
        "email": "attendee@example.com",
        "password": "StrongPass123!",
    }

    register_response = client.post(
        "/api/v1/auth/register",
        json=user_data
    )
    assert register_response.status_code == 201

    login_response = client.post(
        "/api/v1/auth/login",
        json={
            "email": user_data["email"],
            "password": user_data["password"],
        }
    )
    assert login_response.status_code == 200

    token = login_response.json()["access_token"]

    response = client.post(
        "/api/v1/events/",
        json=event_payload(),
        headers=auth_headers(token)
    )

    assert response.status_code == 403


def test_create_event_invalid_capacity(client, organiser_token):
    response = client.post(
        "/api/v1/events/",
        json=event_payload(capacity=0),
        headers=auth_headers(organiser_token),
    )

    assert response.status_code == 422


def test_create_event_invalid_time_range(client, organiser_token):
    start_time = datetime.now(timezone.utc) + timedelta(days=7)

    response = client.post(
        "/api/v1/events/",
        json=event_payload(
            start_time=start_time.isoformat(),
            end_time=(start_time - timedelta(hours=1)).isoformat(),
        ),
        headers=auth_headers(organiser_token),
    )

    assert response.status_code == 422


def test_draft_event_not_visible_in_public_listing(
    client,
    organiser_token,
):
    create_event(client, organiser_token)

    response = client.get("/api/v1/events/")

    assert response.status_code == 200
    assert response.json() == []


def test_draft_event_details_not_publicly_accessible(
    client,
    organiser_token,
):
    event = create_event(client, organiser_token)

    response = client.get(f"/api/v1/events/{event['id']}")

    assert response.status_code == 404


def test_publish_event(client, organiser_token):
    event = create_event(client, organiser_token)

    response = client.post(
        f"/api/v1/events/{event['id']}/publish",
        headers=auth_headers(organiser_token),
    )

    assert response.status_code == 200
    assert response.json()["status"] == "published"


def test_published_event_appears_in_listing(client, organiser_token):
    event = create_event(client, organiser_token)

    publish_response = client.post(
        f"/api/v1/events/{event['id']}/publish",
        headers=auth_headers(organiser_token),
    )

    assert publish_response.status_code == 200

    response = client.get("/api/v1/events/")

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["id"] == event["id"]


def test_get_published_event_details(client, organiser_token):
    event = create_event(client, organiser_token)

    client.post(
        f"/api/v1/events/{event['id']}/publish",
        headers=auth_headers(organiser_token),
    )

    response = client.get(f"/api/v1/events/{event['id']}")

    assert response.status_code == 200
    assert response.json()["id"] == event["id"]


def test_update_own_event(client, organiser_token):
    event = create_event(client, organiser_token)

    response = client.patch(
        f"/api/v1/events/{event['id']}",
        json={"title": "Updated Python Meetup"},
        headers=auth_headers(organiser_token),
    )

    assert response.status_code == 200
    assert response.json()["title"] == "Updated Python Meetup"


def test_cancel_own_event(client, organiser_token):
    event = create_event(client, organiser_token)

    response = client.delete(
        f"/api/v1/events/{event['id']}",
        headers=auth_headers(organiser_token),
    )

    assert response.status_code == 200
    assert response.json()["status"] == "cancelled"
    
def test_unauthenticated_user_cannot_create_event(client):
    response = client.post(
        "/api/v1/events/",
        json=event_payload(),
    )

    assert response.status_code == 401  

def test_organiser_cannot_update_another_organisers_event(
    client,
    organiser_token,
):
    # Create an event using the first organiser
    event = create_event(client, organiser_token)

    # Register a second user
    user_data = {
        "name": "Second Organiser",
        "email": "secondorganiser@example.com",
        "password": "StrongPass123!",
    }

    client.post("/api/v1/auth/register", json=user_data)

    # Promote the second user to organiser for this test
    from app.models.user import User, UserRole
    from app.db.session import SessionLocal

    db = SessionLocal()
    try:
        second_organiser = db.query(User).filter(
            User.email == user_data["email"]
        ).first()

        second_organiser.role = UserRole.ORGANISER
        db.commit()
    finally:
        db.close()

    # Login as the second organiser
    login_response = client.post(
        "/api/v1/auth/login",
        json={
            "email": user_data["email"],
            "password": user_data["password"],
        },
    )

    assert login_response.status_code == 200

    second_token = login_response.json()["access_token"]

    # Try updating the first organiser's event
    response = client.patch(
        f"/api/v1/events/{event['id']}",
        json={"title": "Unauthorized Update"},
        headers=auth_headers(second_token),
    )

    assert response.status_code == 403

def test_organiser_cannot_update_another_organisers_event(
    client,
    organiser_token,
    second_organiser_token,
):
    event = create_event(client, organiser_token)

    response = client.patch(
        f"/api/v1/events/{event['id']}",
        json={"title": "Unauthorized Update"},
        headers=auth_headers(second_organiser_token),
    )

    assert response.status_code == 403

def test_admin_can_update_another_organisers_event(
    client,
    organiser_token,
    admin_token,
):
    event = create_event(client, organiser_token)

    response = client.patch(
        f"/api/v1/events/{event['id']}",
        json={"title": "Admin Updated Event"},
        headers=auth_headers(admin_token),
    )

    assert response.status_code == 200
    assert response.json()["title"] == "Admin Updated Event"

def test_attendee_cannot_publish_event(client, organiser_token):
    event = create_event(client, organiser_token)

    user_data = {
        "name": "Attendee User",
        "email": "publisherattendee@example.com",
        "password": "StrongPass123!",
    }

    client.post("/api/v1/auth/register", json=user_data)

    login_response = client.post(
        "/api/v1/auth/login",
        json={
            "email": user_data["email"],
            "password": user_data["password"],
        },
    )

    assert login_response.status_code == 200

    token = login_response.json()["access_token"]

    response = client.post(
        f"/api/v1/events/{event['id']}/publish",
        headers=auth_headers(token),
    )

    assert response.status_code == 403


def test_organiser_can_list_own_draft_events(client, organiser_token):
    event = create_event(client, organiser_token)

    response = client.get(
        "/api/v1/events/manage",
        headers=auth_headers(organiser_token),
    )

    assert response.status_code == 200, response.text
    assert [item["id"] for item in response.json()] == [event["id"]]
    assert response.json()[0]["status"] == "draft"


def test_organiser_cannot_list_another_organisers_events(
    client,
    organiser_token,
    second_organiser_token,
):
    own_event = create_event(client, organiser_token, title="My Draft Event")
    create_event(client, second_organiser_token, title="Someone Else's Draft")

    response = client.get(
        "/api/v1/events/manage",
        headers=auth_headers(organiser_token),
    )

    assert response.status_code == 200, response.text
    assert [item["id"] for item in response.json()] == [own_event["id"]]


def test_organiser_cannot_complete_event_before_end(client, organiser_token):
    event = create_event(client, organiser_token)
    client.post(
        f"/api/v1/events/{event['id']}/publish",
        headers=auth_headers(organiser_token),
    )

    response = client.post(
        f"/api/v1/events/{event['id']}/complete",
        headers=auth_headers(organiser_token),
    )

    assert response.status_code == 409
    assert "after its end time" in response.json()["detail"]


def test_organiser_can_complete_ended_event_and_read_details(client, organiser_token):
    start_time = datetime.now(timezone.utc) - timedelta(hours=3)
    event = create_event(
        client,
        organiser_token,
        start_time=start_time.isoformat(),
        end_time=(start_time + timedelta(hours=2)).isoformat(),
    )
    client.post(
        f"/api/v1/events/{event['id']}/publish",
        headers=auth_headers(organiser_token),
    )

    completed = client.post(
        f"/api/v1/events/{event['id']}/complete",
        headers=auth_headers(organiser_token),
    )

    assert completed.status_code == 200, completed.text
    assert completed.json()["status"] == "completed"
    details = client.get(f"/api/v1/events/{event['id']}")
    assert details.status_code == 200
    assert details.json()["status"] == "completed"
