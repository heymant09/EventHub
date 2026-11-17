from datetime import datetime

from sqlalchemy import (
    Integer,
    Text,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    CheckConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Review(Base):

    __tablename__ = "reviews"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True,
    )

    registration_id: Mapped[int] = mapped_column(
        Integer,
        unique=True,
        nullable=False,
    )

    event_id: Mapped[int] = mapped_column(
        ForeignKey("events.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    rating: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    comment: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    # Relationships
    registration = relationship(
        "Registration",
        back_populates="review",
        foreign_keys="Review.registration_id"
    )

    event = relationship(
        "Event",
        back_populates="reviews",
    )

    __table_args__ = (
        ForeignKeyConstraint(
            ["registration_id", "event_id"],
            ["registrations.id", "registrations.event_id"],
            name="fk_review_registration_event",
            ondelete="CASCADE",
        ),
        CheckConstraint(
            "rating >= 1 AND rating <= 5",
            name="check_review_rating",
        ),
    )
