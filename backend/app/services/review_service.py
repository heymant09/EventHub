from sqlalchemy import select, func
from sqlalchemy.orm import Session, joinedload
from fastapi import HTTPException, status

from app.models.event import Event, EventStatus
from app.models.registration import Registration, RegistrationStatus
from app.models.review import Review
from app.models.user import User, UserRole
from app.schemas.review import ReviewCreate, ReviewUpdate


def _get_confirmed_registration(
    db: Session,
    event_id: int,
    current_user: User,
) -> Registration:
    """
    Return the CONFIRMED registration for current_user on event_id.
    Raises 404 / 403 / 409 as appropriate.
    """
    event = db.get(Event, event_id)
    if event is None:
        raise HTTPException(status_code=404, detail="Event not found.")

    if event.status != EventStatus.COMPLETED:
        raise HTTPException(
            status_code=409,
            detail="Reviews can only be submitted for completed events.",
        )

    registration = db.scalar(
        select(Registration).where(
            Registration.event_id == event_id,
            Registration.user_id == current_user.id,
            Registration.status == RegistrationStatus.CONFIRMED,
        )
    )

    if registration is None:
        raise HTTPException(
            status_code=403,
            detail=(
                "Only attendees with a confirmed registration "
                "can review this event."
            ),
        )

    return registration


def create_review(
    db: Session,
    event_id: int,
    data: ReviewCreate,
    current_user: User,
) -> Review:
    if current_user.role != UserRole.ATTENDEE:
        raise HTTPException(
            status_code=403,
            detail="Only attendees can submit reviews."
        )
    registration = _get_confirmed_registration(db, event_id, current_user)

    # Enforce one review per registration
    existing_review = db.scalar(
        select(Review.id).where(
            Review.registration_id == registration.id
        )
    )

    if existing_review is not None:
        raise HTTPException(
            status_code=409,
            detail="You have already reviewed this event.",
        )

    review = Review(
        registration_id=registration.id,
        event_id=event_id,
        rating=data.rating,
        comment=data.comment,
    )
    db.add(review)
    db.commit()
    db.refresh(review)

    # Eagerly load the relationship chain needed by ReviewResponse
    db.refresh(review)
    _ = review.registration.user  # trigger lazy load while session is open

    return review


def get_review(db: Session, review_id: int) -> Review:
    review = db.scalar(
        select(Review)
        .options(joinedload(Review.registration).joinedload(Registration.user))
        .where(Review.id == review_id)
    )
    if review is None:
        raise HTTPException(status_code=404, detail="Review not found.")
    return review


def list_event_reviews(
    db: Session,
    event_id: int,
    skip: int = 0,
    limit: int = 20,
) -> list[Review]:
    event = db.get(Event, event_id)
    if event is None:
        raise HTTPException(status_code=404, detail="Event not found.")

    rows = db.scalars(
        select(Review)
        .options(joinedload(Review.registration).joinedload(Registration.user))
        .where(Review.event_id == event_id)
        .order_by(Review.created_at.desc())
        .offset(skip)
        .limit(limit)
    ).all()

    return list(rows)


def update_review(
    db: Session,
    event_id: int,
    review_id: int,
    data: ReviewUpdate,
    current_user: User,
) -> Review:
    review = get_review(db, review_id)

    if review.event_id != event_id:
        raise HTTPException(status_code=404, detail="Review not found.")

    # Only the author or an admin may edit
    if (
        review.registration.user_id != current_user.id
        and current_user.role != UserRole.ADMIN
    ):
        raise HTTPException(
            status_code=403,
            detail="You can only edit your own reviews.",
        )

    if data.rating is not None:
        review.rating = data.rating

    # Update comment only when "comment" key was explicitly present in the payload
    if "comment" in data.model_fields_set:
        review.comment = data.comment  # may be null — clears existing comment

    db.commit()
    db.refresh(review)
    _ = review.registration.user  # trigger lazy load while session is open

    return review


def delete_review(
    db: Session,
    event_id: int,
    review_id: int,
    current_user: User,
) -> None:
    review = get_review(db, review_id)

    if review.event_id != event_id:
        raise HTTPException(status_code=404, detail="Review not found.")

    if (
        review.registration.user_id != current_user.id
        and current_user.role != UserRole.ADMIN
    ):
        raise HTTPException(
            status_code=403,
            detail="You can only delete your own reviews.",
        )

    db.delete(review)
    db.commit()


def get_event_rating_summary(db: Session, event_id: int) -> dict:
    event = db.get(Event, event_id)
    if event is None:
        raise HTTPException(status_code=404, detail="Event not found.")

    result = db.execute(
        select(
            func.avg(Review.rating).label("average_rating"),
            func.count(Review.id).label("total_reviews"),
        ).where(Review.event_id == event_id)
    ).one()

    avg = float(round(result.average_rating, 2)) if result.average_rating else None

    return {
        "event_id": event_id,
        "average_rating": avg,
        "total_reviews": result.total_reviews,
    }
