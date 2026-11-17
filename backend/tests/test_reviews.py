"""
tests/test_reviews.py
======================
Comprehensive tests for Phase 3 — Event Reviews & Ratings.

Business rules verified
-----------------------
1. Only attendees with a CONFIRMED registration on a COMPLETED event can review.
2. One review per registration (409 on duplicate).
3. Only the review author or an admin can edit / delete a review.
4. Average rating is computed by SQL aggregation (no stored column).
5. Public endpoints (list, summary) are accessible without authentication.
6. 404 is returned when the event does not exist (both list and summary).
"""

import pytest
from fastapi import status
from datetime import datetime, timedelta, timezone


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()

def _past(hours: int = 2) -> str:
    return (datetime.now(timezone.utc) - timedelta(hours=hours)).isoformat()

def _future(hours: int = 2) -> str:
    return (datetime.now(timezone.utc) + timedelta(hours=hours)).isoformat()


def _register(client, token: str, event_id: int) -> dict:
    resp = client.post(
        f"/api/v1/events/{event_id}/register",
        headers={"Authorization": f"Bearer {token}"},
    )
    return resp


def _make_event(client, organiser_token: str, **overrides) -> dict:
    payload = {
        "title": "Test Event",
        "description": "A long enough description for testing.",
        "location": "Test Venue",
        "start_time": _past(4),
        "end_time": _past(2),
        "capacity": 10,
        **overrides,
    }
    resp = client.post(
        "/api/v1/events/",
        json=payload,
        headers={"Authorization": f"Bearer {organiser_token}"},
    )
    assert resp.status_code == status.HTTP_201_CREATED, resp.text
    return resp.json()


def _set_event_status(db_session, event_id: int, new_status: str):
    from app.models.event import Event, EventStatus
    event = db_session.get(Event, event_id)
    assert event is not None
    event.status = EventStatus(new_status)
    db_session.commit()


def _create_attendee(client, db_session, email: str = "attendee@example.com") -> tuple[dict, str]:
    """Register a new attendee via the public API, return (user_data, token)."""
    payload = {
        "name": "Attendee User",
        "email": email,
        "password": "StrongPass123!",
    }
    resp = client.post("/api/v1/auth/register", json=payload)
    assert resp.status_code == 201, resp.text

    login = client.post(
        "/api/v1/auth/login",
        json={"email": payload["email"], "password": payload["password"]},
    )
    assert login.status_code == 200, login.text
    return payload, login.json()["access_token"]


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def attendee_token(client, db_session):
    _, token = _create_attendee(client, db_session, "attendee@example.com")
    return token

@pytest.fixture
def second_attendee_token(client, db_session):
    _, token = _create_attendee(client, db_session, "attendee2@example.com")
    return token

@pytest.fixture
def completed_event(client, db_session, organiser_token):
    """A COMPLETED event that an organiser owns."""
    event = _make_event(client, organiser_token)
    _set_event_status(db_session, event["id"], "published")
    # Register the attendee so their token is usable
    return event

@pytest.fixture
def confirmed_registration_and_completed_event(
    client, db_session, organiser_token, attendee_token
):
    """
    Published event → attendee registers → event marked COMPLETED.
    Returns (event, attendee_token).
    """
    event = _make_event(client, organiser_token)
    _set_event_status(db_session, event["id"], "published")

    reg = _register(client, attendee_token, event["id"])
    assert reg.status_code == 201, reg.text

    _set_event_status(db_session, event["id"], "completed")
    return event, attendee_token


# ---------------------------------------------------------------------------
# Review submission
# ---------------------------------------------------------------------------

class TestCreateReview:

    def test_create_review_success(
        self, client, confirmed_registration_and_completed_event
    ):
        event, token = confirmed_registration_and_completed_event
        resp = client.post(
            f"/api/v1/events/{event['id']}/reviews",
            json={"rating": 5, "comment": "Fantastic event!"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == status.HTTP_201_CREATED, resp.text
        data = resp.json()
        assert data["rating"] == 5
        assert data["comment"] == "Fantastic event!"
        assert data["event_id"] == event["id"]
        assert "author" in data
        assert data["author"]["name"] == "Attendee User"

    def test_create_review_no_comment(
        self, client, confirmed_registration_and_completed_event
    ):
        event, token = confirmed_registration_and_completed_event
        resp = client.post(
            f"/api/v1/events/{event['id']}/reviews",
            json={"rating": 3},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == status.HTTP_201_CREATED, resp.text
        assert resp.json()["comment"] is None

    def test_create_review_duplicate_rejected(
        self, client, confirmed_registration_and_completed_event
    ):
        event, token = confirmed_registration_and_completed_event
        client.post(
            f"/api/v1/events/{event['id']}/reviews",
            json={"rating": 4},
            headers={"Authorization": f"Bearer {token}"},
        )
        resp = client.post(
            f"/api/v1/events/{event['id']}/reviews",
            json={"rating": 2},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == status.HTTP_409_CONFLICT, resp.text

    def test_create_review_unauthenticated(
        self, client, confirmed_registration_and_completed_event
    ):
        event, _ = confirmed_registration_and_completed_event
        resp = client.post(
            f"/api/v1/events/{event['id']}/reviews",
            json={"rating": 4},
        )
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED

    def test_create_review_event_not_completed(
        self, client, db_session, organiser_token, attendee_token
    ):
        """Cannot review a PUBLISHED event."""
        event = _make_event(client, organiser_token)
        _set_event_status(db_session, event["id"], "published")
        _register(client, attendee_token, event["id"])

        resp = client.post(
            f"/api/v1/events/{event['id']}/reviews",
            json={"rating": 4},
            headers={"Authorization": f"Bearer {attendee_token}"},
        )
        assert resp.status_code == status.HTTP_409_CONFLICT, resp.text

    def test_create_review_no_registration(
        self, client, db_session, organiser_token, attendee_token
    ):
        """Cannot review if the attendee never registered."""
        event = _make_event(client, organiser_token)
        _set_event_status(db_session, event["id"], "completed")

        resp = client.post(
            f"/api/v1/events/{event['id']}/reviews",
            json={"rating": 4},
            headers={"Authorization": f"Bearer {attendee_token}"},
        )
        assert resp.status_code == status.HTTP_403_FORBIDDEN, resp.text

    def test_create_review_rating_out_of_range(
        self, client, confirmed_registration_and_completed_event
    ):
        event, token = confirmed_registration_and_completed_event
        for bad_rating in [0, 6]:
            resp = client.post(
                f"/api/v1/events/{event['id']}/reviews",
                json={"rating": bad_rating},
                headers={"Authorization": f"Bearer {token}"},
            )
            assert resp.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY, (
                f"Expected 422 for rating={bad_rating}, got {resp.status_code}"
            )

    def test_create_review_comment_too_long(
        self, client, confirmed_registration_and_completed_event
    ):
        event, token = confirmed_registration_and_completed_event
        resp = client.post(
            f"/api/v1/events/{event['id']}/reviews",
            json={"rating": 3, "comment": "x" * 2001},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_create_review_event_not_found(self, client, attendee_token):
        resp = client.post(
            "/api/v1/events/99999/reviews",
            json={"rating": 4},
            headers={"Authorization": f"Bearer {attendee_token}"},
        )
        assert resp.status_code == status.HTTP_404_NOT_FOUND


def test_my_registrations_returns_event_and_attendee_details(
    client,
    confirmed_registration_and_completed_event,
):
    event, token = confirmed_registration_and_completed_event

    response = client.get(
        "/api/v1/users/me/registrations",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == status.HTTP_200_OK, response.text
    registration = next(item for item in response.json() if item["event_id"] == event["id"])
    assert registration["event"]["title"] == event["title"]
    assert registration["event"]["status"] == "completed"
    assert registration["attendee"]["name"] == "Attendee User"


# ---------------------------------------------------------------------------
# Public read endpoints
# ---------------------------------------------------------------------------

class TestListReviews:

    def test_list_reviews_public(
        self, client, confirmed_registration_and_completed_event
    ):
        event, token = confirmed_registration_and_completed_event
        client.post(
            f"/api/v1/events/{event['id']}/reviews",
            json={"rating": 5, "comment": "Great!"},
            headers={"Authorization": f"Bearer {token}"},
        )
        resp = client.get(f"/api/v1/events/{event['id']}/reviews")
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["rating"] == 5

    def test_list_reviews_empty_for_existing_event(
        self, client, db_session, organiser_token
    ):
        event = _make_event(client, organiser_token)
        _set_event_status(db_session, event["id"], "completed")

        resp = client.get(f"/api/v1/events/{event['id']}/reviews")
        assert resp.status_code == status.HTTP_200_OK
        assert resp.json() == []

    def test_list_reviews_event_not_found(self, client):
        resp = client.get("/api/v1/events/99999/reviews")
        assert resp.status_code == status.HTTP_404_NOT_FOUND


class TestRatingSummary:

    def test_summary_no_reviews(
        self, client, db_session, organiser_token
    ):
        event = _make_event(client, organiser_token)
        _set_event_status(db_session, event["id"], "completed")

        resp = client.get(f"/api/v1/events/{event['id']}/reviews/summary")
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        assert data["average_rating"] is None
        assert data["total_reviews"] == 0

    def test_summary_with_reviews(
        self,
        client,
        db_session,
        organiser_token,
        attendee_token,
        second_attendee_token,
    ):
        event = _make_event(client, organiser_token)
        _set_event_status(db_session, event["id"], "published")

        _register(client, attendee_token, event["id"])
        _register(client, second_attendee_token, event["id"])

        _set_event_status(db_session, event["id"], "completed")

        client.post(
            f"/api/v1/events/{event['id']}/reviews",
            json={"rating": 4},
            headers={"Authorization": f"Bearer {attendee_token}"},
        )
        client.post(
            f"/api/v1/events/{event['id']}/reviews",
            json={"rating": 2},
            headers={"Authorization": f"Bearer {second_attendee_token}"},
        )

        resp = client.get(f"/api/v1/events/{event['id']}/reviews/summary")
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        assert data["total_reviews"] == 2
        assert data["average_rating"] == 3.0  # (4+2)/2

    def test_summary_event_not_found(self, client):
        resp = client.get("/api/v1/events/99999/reviews/summary")
        assert resp.status_code == status.HTTP_404_NOT_FOUND


# ---------------------------------------------------------------------------
# Review editing (PATCH)
# ---------------------------------------------------------------------------

class TestUpdateReview:

    def _post_review(self, client, event, token, rating=4, comment="Good"):
        resp = client.post(
            f"/api/v1/events/{event['id']}/reviews",
            json={"rating": rating, "comment": comment},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 201, resp.text
        return resp.json()

    def test_author_can_update_rating(
        self, client, confirmed_registration_and_completed_event
    ):
        event, token = confirmed_registration_and_completed_event
        review = self._post_review(client, event, token)
        resp = client.patch(
            f"/api/v1/events/{event['id']}/reviews/{review['id']}",
            json={"rating": 2},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == status.HTTP_200_OK
        assert resp.json()["rating"] == 2

    def test_author_can_clear_comment(
        self, client, confirmed_registration_and_completed_event
    ):
        """Sending comment: null explicitly clears an existing comment."""
        event, token = confirmed_registration_and_completed_event
        review = self._post_review(client, event, token, comment="Nice event")
        resp = client.patch(
            f"/api/v1/events/{event['id']}/reviews/{review['id']}",
            json={"comment": None},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == status.HTTP_200_OK
        assert resp.json()["comment"] is None

    def test_empty_update_rejected(
        self, client, confirmed_registration_and_completed_event
    ):
        event, token = confirmed_registration_and_completed_event
        review = self._post_review(client, event, token)
        resp = client.patch(
            f"/api/v1/events/{event['id']}/reviews/{review['id']}",
            json={},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_admin_can_update_any_review(
        self, client, confirmed_registration_and_completed_event, admin_token
    ):
        event, token = confirmed_registration_and_completed_event
        review = self._post_review(client, event, token)
        resp = client.patch(
            f"/api/v1/events/{event['id']}/reviews/{review['id']}",
            json={"rating": 1},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == status.HTTP_200_OK
        assert resp.json()["rating"] == 1

    def test_other_user_cannot_update(
        self,
        client,
        db_session,
        organiser_token,
        attendee_token,
        second_attendee_token,
    ):
        event = _make_event(client, organiser_token)
        _set_event_status(db_session, event["id"], "published")
        _register(client, attendee_token, event["id"])
        _set_event_status(db_session, event["id"], "completed")
        review = client.post(
            f"/api/v1/events/{event['id']}/reviews",
            json={"rating": 4},
            headers={"Authorization": f"Bearer {attendee_token}"},
        ).json()

        resp = client.patch(
            f"/api/v1/events/{event['id']}/reviews/{review['id']}",
            json={"rating": 1},
            headers={"Authorization": f"Bearer {second_attendee_token}"},
        )
        assert resp.status_code == status.HTTP_403_FORBIDDEN

    def test_update_review_not_found(
        self, client, confirmed_registration_and_completed_event
    ):
        event, token = confirmed_registration_and_completed_event
        resp = client.patch(
            f"/api/v1/events/{event['id']}/reviews/99999",
            json={"rating": 3},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == status.HTTP_404_NOT_FOUND

    def test_update_review_through_wrong_event_url_returns_404(
        self, client, db_session, organiser_token,
        confirmed_registration_and_completed_event
    ):
        event, token = confirmed_registration_and_completed_event
        review = self._post_review(client, event, token)
        other_event = _make_event(client, organiser_token)

        resp = client.patch(
            f"/api/v1/events/{other_event['id']}/reviews/{review['id']}",
            json={"rating": 1},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == status.HTTP_404_NOT_FOUND


# ---------------------------------------------------------------------------
# Review deletion (DELETE)
# ---------------------------------------------------------------------------

class TestDeleteReview:

    def _post_review(self, client, event, token):
        resp = client.post(
            f"/api/v1/events/{event['id']}/reviews",
            json={"rating": 5},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 201, resp.text
        return resp.json()

    def test_author_can_delete_own_review(
        self, client, confirmed_registration_and_completed_event
    ):
        event, token = confirmed_registration_and_completed_event
        review = self._post_review(client, event, token)
        resp = client.delete(
            f"/api/v1/events/{event['id']}/reviews/{review['id']}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == status.HTTP_204_NO_CONTENT

    def test_admin_can_delete_any_review(
        self, client, confirmed_registration_and_completed_event, admin_token
    ):
        event, token = confirmed_registration_and_completed_event
        review = self._post_review(client, event, token)
        resp = client.delete(
            f"/api/v1/events/{event['id']}/reviews/{review['id']}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == status.HTTP_204_NO_CONTENT

    def test_other_user_cannot_delete(
        self,
        client,
        db_session,
        organiser_token,
        attendee_token,
        second_attendee_token,
    ):
        event = _make_event(client, organiser_token)
        _set_event_status(db_session, event["id"], "published")
        _register(client, attendee_token, event["id"])
        _set_event_status(db_session, event["id"], "completed")
        review = client.post(
            f"/api/v1/events/{event['id']}/reviews",
            json={"rating": 4},
            headers={"Authorization": f"Bearer {attendee_token}"},
        ).json()

        resp = client.delete(
            f"/api/v1/events/{event['id']}/reviews/{review['id']}",
            headers={"Authorization": f"Bearer {second_attendee_token}"},
        )
        assert resp.status_code == status.HTTP_403_FORBIDDEN

    def test_delete_review_unauthenticated(
        self, client, confirmed_registration_and_completed_event
    ):
        event, token = confirmed_registration_and_completed_event
        review = self._post_review(client, event, token)
        resp = client.delete(
            f"/api/v1/events/{event['id']}/reviews/{review['id']}"
        )
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED

    def test_delete_review_not_found(
        self, client, confirmed_registration_and_completed_event
    ):
        event, token = confirmed_registration_and_completed_event
        resp = client.delete(
            f"/api/v1/events/{event['id']}/reviews/99999",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_review_through_wrong_event_url_returns_404(
        self, client, db_session, organiser_token,
        confirmed_registration_and_completed_event
    ):
        event, token = confirmed_registration_and_completed_event
        review = self._post_review(client, event, token)
        other_event = _make_event(client, organiser_token)

        resp = client.delete(
            f"/api/v1/events/{other_event['id']}/reviews/{review['id']}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == status.HTTP_404_NOT_FOUND
