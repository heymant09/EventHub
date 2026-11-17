from fastapi import APIRouter, Depends, Query, status, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Literal
from fastapi import Query
from app.db.session import get_db
from app.models.user import User
from app.schemas.event import (
    EventCreate,
    EventUpdate,
    EventResponse
)
from app.services import event_service

from app.dependencies.auth import (
    get_current_user,
    get_current_organiser
)

from app.services.event_service import (
    create_event,
    get_published_events,
    get_manageable_events,
    get_event_by_id,
    update_event,
    publish_event,
    cancel_event,
    complete_event,
)


router = APIRouter(
    prefix="/events",
    tags=["Events"]
)


# Create event
@router.post(
    "/",
    response_model=EventResponse,
    status_code=status.HTTP_201_CREATED
)
def create_new_event(
    event_data: EventCreate,
    db: Session = Depends(get_db),
    organiser: User = Depends(get_current_organiser)
):
    return create_event(db, event_data, organiser)


# Discover published events
@router.get("/", response_model=list[EventResponse])
def list_events(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=10, ge=1, le=100),

    search: str | None = None,
    location: str | None = None,
    category_id: int | None = Query(default=None, gt=0),

    start_from: datetime | None = None,
    start_to: datetime | None = None,

    sort_by: Literal["start_time", "title", "created_at"] = "start_time",
    order: Literal["asc", "desc"] = "asc",

    db: Session = Depends(get_db)
):
    if start_from and start_to and start_from > start_to:
        raise HTTPException(
            status_code=400,
            detail="start_from cannot be later than start_to"
        )

    return event_service.get_published_events(
        db=db,
        skip=skip,
        limit=limit,
        search=search,
        location=location,
        category_id=category_id,
        start_from=start_from,
        start_to=start_to,
        sort_by=sort_by,
        order=order
    )


# List manageable events, including drafts and cancelled events.
@router.get("/manage", response_model=list[EventResponse])
def list_manageable_events(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_organiser),
):
    return get_manageable_events(db, current_user, skip=skip, limit=limit)



# Get event details
@router.get(
    "/{event_id}",
    response_model=EventResponse
)
def get_event_details(
    event_id: int,
    db: Session = Depends(get_db)
):
    return get_event_by_id(db, event_id)


# Update existing event
@router.patch(
    "/{event_id}",
    response_model=EventResponse
)
def update_existing_event(
    event_id: int,
    event_data: EventUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return update_event(
        db,
        event_id,
        event_data,
        current_user
    )


# Publish event
@router.post(
    "/{event_id}/publish",
    response_model=EventResponse
)
def publish_existing_event(
    event_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return publish_event(
        db,
        event_id,
        current_user
    )


# Cancel event
@router.delete(
    "/{event_id}",
    response_model=EventResponse
)
def cancel_existing_event(
    event_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return cancel_event(
        db,
        event_id,
        current_user
    )


@router.post("/{event_id}/complete", response_model=EventResponse)
def complete_existing_event(
    event_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return complete_event(db, event_id, current_user)
