import enum
from sqlalchemy import CheckConstraint
from datetime import datetime

from sqlalchemy import (
    String,
    Text,
    Integer,
    DateTime,
    ForeignKey,
    Enum,
    func
)

from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class EventStatus(str, enum.Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    CANCELLED = "cancelled"
    COMPLETED = "completed"


class Event(Base):

    __tablename__ = "events"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True
    )

    title: Mapped[str] = mapped_column(
        String(200),
        nullable=False
    )

    description: Mapped[str] = mapped_column(
        Text,
        nullable=False
    )

    location: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )

    start_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False
    )

    end_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False
    )

    capacity: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )

    status: Mapped[EventStatus] = mapped_column(
        Enum(EventStatus, name="event_status"),
        default=EventStatus.DRAFT,
        nullable=False
    )

    organiser_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    # Relationships
    organiser = relationship(
        "User",
        back_populates="events"
    )
    # New relationship for reviews
    reviews = relationship("Review", back_populates="event")

    registrations = relationship(
        "Registration",
        back_populates="event"
    )

    categories = relationship(
        "Category",
        secondary="event_categories",
        back_populates="events"
    )
    __table_args__ = (
        CheckConstraint(
            "capacity > 0",
            name="check_event_capacity"
        ),
        CheckConstraint(
             "end_time > start_time",
             name="check_event_time"
        ),
    )