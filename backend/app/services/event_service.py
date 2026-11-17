from datetime import datetime, timezone
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.models.category import Category
from app.models.event import Event, EventStatus
from app.models.user import User, UserRole
from app.schemas.event import EventCreate, EventUpdate


def create_event(db: Session, event_data, organiser):
    event_data_dict = event_data.model_dump(exclude={"category_ids"})

    category_ids = event_data.category_ids

    event = Event(
        **event_data_dict,
        organiser_id=organiser.id,
        categories=get_categories_by_ids(db, category_ids)
    )

    db.add(event)
    db.commit()
    db.refresh(event)

    return event


# 1. Discover published events
def get_published_events(
    db: Session,
    skip: int = 0,
    limit: int = 10,
    search: str | None = None,
    location: str | None = None,
    category_id: int | None = None,
    start_from: datetime | None = None,
    start_to: datetime | None = None,
    sort_by: str = "start_time",
    order: str = "asc"
):
    statement = select(Event).where(
        Event.status == EventStatus.PUBLISHED
    )

    # Search in event title and description.
    if search:
        search_term = f"%{search.strip()}%"
        statement = statement.where(
            Event.title.ilike(search_term)
            | Event.description.ilike(search_term)
        )

    # Filter by location.
    if location:
        statement = statement.where(
            Event.location.ilike(f"%{location.strip()}%")
        )

    # Filter by category.
    if category_id is not None:
        statement = statement.join(Event.categories).where(
            Category.id == category_id
        )

    # Filter by event start time.
    if start_from is not None:
        statement = statement.where(
            Event.start_time >= start_from
        )

    if start_to is not None:
        statement = statement.where(
            Event.start_time <= start_to
        )

    # Allow only specific sorting columns.
    sort_columns = {
        "start_time": Event.start_time,
        "title": Event.title,
        "created_at": Event.created_at
    }

    sort_column = sort_columns[sort_by]

    if order == "desc":
        statement = statement.order_by(sort_column.desc())
    else:
        statement = statement.order_by(sort_column.asc())

    statement = statement.offset(skip).limit(limit)

    return db.scalars(statement).unique().all()


def get_manageable_events(
    db: Session,
    current_user: User,
    skip: int = 0,
    limit: int = 100,
):
    """List events the current organiser owns, or all events for admins."""
    statement = select(Event)

    if current_user.role != UserRole.ADMIN:
        statement = statement.where(Event.organiser_id == current_user.id)

    statement = statement.order_by(Event.created_at.desc(), Event.id.desc())
    statement = statement.offset(skip).limit(limit)
    return db.scalars(statement).unique().all()


# 2. Get event details
def get_event_by_id(
    db: Session,
    event_id: int
) -> Event:

    event = db.scalar(
        select(Event).where(
            Event.id == event_id,
            Event.status.in_((EventStatus.PUBLISHED, EventStatus.COMPLETED))
        )
    )

    if event is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found."
        )

    return event


# Common ownership/permission check
def check_event_permission(
    event: Event,
    current_user: User
):
    is_owner = event.organiser_id == current_user.id
    is_admin = current_user.role == UserRole.ADMIN

    if not (is_owner or is_admin):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You cannot manage this event."
        )


# 3. Update an existing event
def update_event(
    db: Session,
    event_id: int,
    event_data: EventUpdate,
    current_user: User
) -> Event:

    event = db.get(Event, event_id)

    if event is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found."
        )

    check_event_permission(event, current_user)

    if event.status in (
        EventStatus.CANCELLED,
        EventStatus.COMPLETED
    ):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This event cannot be updated."
        )

    # Extract only fields provided by the client.
    update_data = event_data.model_dump(exclude_unset=True)

    # Extract category IDs separately.
    category_ids = update_data.pop("category_ids", None)

    # Validate combined start and end times.
    new_start = update_data.get("start_time", event.start_time)
    new_end = update_data.get("end_time", event.end_time)

    if new_end <= new_start:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Event end time must be after start time."
        )

    # Update categories if category_ids was provided.
    if category_ids is not None:
        event.categories = get_categories_by_ids(db, category_ids)

    # Update remaining event fields.
    for field, value in update_data.items():
        setattr(event, field, value)

    db.commit()
    db.refresh(event)

    return event

# 4. Publish an event
def publish_event(
    db: Session,
    event_id: int,
    current_user: User
) -> Event:

    event = db.get(Event, event_id)

    if event is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found."
        )

    check_event_permission(event, current_user)

    if event.status != EventStatus.DRAFT:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Only draft events can be published."
        )

    event.status = EventStatus.PUBLISHED

    db.commit()
    db.refresh(event)

    return event


# 5. Cancel an event
def cancel_event(
    db: Session,
    event_id: int,
    current_user: User
) -> Event:

    event = db.get(Event, event_id)

    if event is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found."
        )

    check_event_permission(event, current_user)

    if event.status in (
        EventStatus.CANCELLED,
        EventStatus.COMPLETED
    ):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This event cannot be cancelled."
        )

    # Soft cancellation: preserve the database record.
    event.status = EventStatus.CANCELLED

    db.commit()
    db.refresh(event)

    return event


def complete_event(
    db: Session,
    event_id: int,
    current_user: User,
) -> Event:
    event = db.get(Event, event_id)

    if event is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found.",
        )

    check_event_permission(event, current_user)

    if event.status != EventStatus.PUBLISHED:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Only published events can be marked completed.",
        )

    end_time = event.end_time
    if end_time.tzinfo is None:
        end_time = end_time.replace(tzinfo=timezone.utc)
    if end_time > datetime.now(timezone.utc):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An event can only be completed after its end time.",
        )

    event.status = EventStatus.COMPLETED
    db.commit()
    db.refresh(event)
    return event

def get_categories_by_ids(db: Session, category_ids: list[int]):
    # Remove duplicate IDs while preserving order.
    category_ids = list(dict.fromkeys(category_ids))

    if not category_ids:
        return []

    categories = db.scalars(
        select(Category).where(Category.id.in_(category_ids))
    ).all()

    if len(categories) != len(category_ids):
        raise HTTPException(
            status_code=404,
            detail="One or more categories were not found"
        )

    return categories
