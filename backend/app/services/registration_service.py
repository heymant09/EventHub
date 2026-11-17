from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload
from sqlalchemy.exc import IntegrityError
from sqlalchemy import func
from datetime import datetime, timezone
from fastapi import HTTPException, status

from app.models.event import Event, EventStatus
from app.models.registration import Registration, RegistrationStatus
from app.models.user import User, UserRole


def register_for_event(
    db: Session,
    event_id: int,
    current_user: User
) -> Registration:

    # Lock the event row to prevent concurrent capacity issues.
    event = db.scalar(
        select(Event)
        .where(Event.id == event_id)
        .with_for_update()
    )

    if event is None:
        raise HTTPException(
            status_code=404,
            detail="Event not found."
        )

    if event.status != EventStatus.PUBLISHED:
        raise HTTPException(
            status_code=409,
            detail="Registration is only available for published events."
        )

    # Check whether this user already has a registration.
    existing_registration = db.scalar(
        select(Registration)
        .where(
            Registration.event_id == event_id,
            Registration.user_id == current_user.id
        )
        .with_for_update()
    )

    if (
        existing_registration
        and existing_registration.status != RegistrationStatus.CANCELLED
    ):
        raise HTTPException(
            status_code=409,
            detail="You are already registered for this event."
        )

    # Count confirmed registrations.
    confirmed_count = db.scalar(
        select(func.count(Registration.id))
        .where(
            Registration.event_id == event_id,
            Registration.status == RegistrationStatus.CONFIRMED
        )
    ) or 0

    # Decide whether the user gets a confirmed seat or waitlist position.
    if confirmed_count < event.capacity:
        registration_status = RegistrationStatus.CONFIRMED
    else:
        registration_status = RegistrationStatus.WAITLISTED

    # Reuse a previously cancelled registration.
    if existing_registration:
        existing_registration.status = registration_status

        # Give a re-registering user a new waitlist timestamp.
        existing_registration.registered_at = datetime.now(timezone.utc)

        registration = existing_registration

    else:
        registration = Registration(
            user_id=current_user.id,
            event_id=event_id,
            status=registration_status
        )

        db.add(registration)

    try:
        db.commit()
        db.refresh(registration)

    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Registration could not be completed."
        )

    return registration


def cancel_registration(
    db: Session,
    event_id: int,
    current_user: User
) -> Registration:

    # Lock the event before changing registration status.
    event = db.scalar(
        select(Event)
        .where(Event.id == event_id)
        .with_for_update()
    )

    if event is None:
        raise HTTPException(
            status_code=404,
            detail="Event not found."
        )

    registration = db.scalar(
        select(Registration)
        .where(
            Registration.event_id == event_id,
            Registration.user_id == current_user.id
        )
        .with_for_update()
    )

    if (
        registration is None
        or registration.status == RegistrationStatus.CANCELLED
    ):
        raise HTTPException(
            status_code=404,
            detail="Active registration not found."
        )

    was_confirmed = (
        registration.status == RegistrationStatus.CONFIRMED
    )

    registration.status = RegistrationStatus.CANCELLED

    # Only promote someone if a confirmed seat was released.
    if was_confirmed:

        next_attendee = db.scalar(
            select(Registration)
            .where(
                Registration.event_id == event_id,
                Registration.status == RegistrationStatus.WAITLISTED
            )
            .order_by(
                Registration.registered_at.asc(),
                Registration.id.asc()
            )
            .limit(1)
            .with_for_update()
        )

        if next_attendee:
            next_attendee.status = RegistrationStatus.CONFIRMED

    db.commit()
    db.refresh(registration)

    return registration


def get_event_registrations(
    db: Session,
    event_id: int,
    current_user: User,
    skip: int = 0,
    limit: int = 20
) -> list[Registration]:

    event = db.get(Event, event_id)

    if event is None:
        raise HTTPException(
            status_code=404,
            detail="Event not found."
        )

    if (
        event.organiser_id != current_user.id
        and current_user.role != UserRole.ADMIN
    ):
        raise HTTPException(
            status_code=403,
            detail="You cannot view registrations for this event."
        )

    query = (
        select(Registration)
        .options(
            selectinload(Registration.event),
            selectinload(Registration.user),
        )
        .where(Registration.event_id == event_id)
        .order_by(
            Registration.registered_at.asc(),
            Registration.id.asc()
        )
        .offset(skip)
        .limit(limit)
    )

    return list(db.scalars(query).all())

def get_my_registrations(
    db: Session,
    current_user: User
):
    statement = (
        select(Registration)
        .options(
            selectinload(Registration.event),
            selectinload(Registration.user),
        )
        .where(Registration.user_id == current_user.id)
        .order_by(Registration.registered_at.desc())
    )

    return db.scalars(statement).all()
