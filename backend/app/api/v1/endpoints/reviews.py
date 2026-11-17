from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.review import (
    ReviewCreate,
    ReviewUpdate,
    ReviewResponse,
    EventRatingSummary,
)
from app.services import review_service

router = APIRouter(prefix="/events", tags=["Reviews"])


# ---------------------------------------------------------------------------
# Public endpoints (no auth required)
# ---------------------------------------------------------------------------

@router.get(
    "/{event_id}/reviews",
    response_model=list[ReviewResponse],
    summary="List reviews for an event",
)
def list_reviews(
    event_id: int,
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
):
    reviews = review_service.list_event_reviews(db, event_id, skip=skip, limit=limit)
    return [ReviewResponse.from_review(r) for r in reviews]


@router.get(
    "/{event_id}/reviews/summary",
    response_model=EventRatingSummary,
    summary="Get average rating and review count for an event",
)
def get_rating_summary(
    event_id: int,
    db: Session = Depends(get_db),
):
    return review_service.get_event_rating_summary(db, event_id)


# ---------------------------------------------------------------------------
# Authenticated endpoints
# ---------------------------------------------------------------------------

@router.post(
    "/{event_id}/reviews",
    response_model=ReviewResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit a review for an event",
)
def create_review(
    event_id: int,
    data: ReviewCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    review = review_service.create_review(db, event_id, data, current_user)
    return ReviewResponse.from_review(review)


@router.patch(
    "/{event_id}/reviews/{review_id}",
    response_model=ReviewResponse,
    summary="Edit a review (author or admin only)",
)
def update_review(
    event_id: int,
    review_id: int,
    data: ReviewUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    review = review_service.update_review(
        db, event_id, review_id, data, current_user
    )
    return ReviewResponse.from_review(review)


@router.delete(
    "/{event_id}/reviews/{review_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a review (author or admin only)",
)
def delete_review(
    event_id: int,
    review_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    review_service.delete_review(db, event_id, review_id, current_user)
