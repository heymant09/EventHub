from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from fastapi import Query
from app.db.session import get_db
from app.models.user import User
from app.schemas.registration import RegistrationResponse

from app.dependencies.auth import get_current_user

from app.services.registration_service import (
    register_for_event,
    cancel_registration,
    get_event_registrations
)


router = APIRouter(
    prefix="/events",
    tags=["Registrations"]
)


@router.post(
    "/{event_id}/register",
    response_model=RegistrationResponse,
    status_code=status.HTTP_201_CREATED
)
def register_attendee(
    event_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return register_for_event(db, event_id, current_user)


@router.delete(
    "/{event_id}/register",
    response_model=RegistrationResponse
)
def cancel_attendee_registration(
    event_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return cancel_registration(db, event_id, current_user)


@router.get(
    "/{event_id}/registrations",
    response_model=list[RegistrationResponse]
)
def list_event_registrations(
    event_id: int,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return get_event_registrations(
        db,
        event_id,
        current_user,
        skip,
        limit
    )