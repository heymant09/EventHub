import enum

from sqlalchemy import (
    ForeignKey,
    Enum,
    DateTime,
    UniqueConstraint,
    func
)

from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class RegistrationStatus(str, enum.Enum):

    CONFIRMED = "confirmed"
    WAITLISTED = "waitlisted"
    CANCELLED = "cancelled"


class Registration(Base):

    __tablename__ = "registrations"

    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "event_id",
            name="uq_user_event"
        ),
        UniqueConstraint("id", "event_id", name="uq_registration_id_event"),
    )

    id: Mapped[int] = mapped_column(
        primary_key=True
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False
    )

    event_id: Mapped[int] = mapped_column(
        ForeignKey("events.id"),
        nullable=False
    )

    status: Mapped[RegistrationStatus] = mapped_column(
        Enum(RegistrationStatus, name="registration_status"),
        default=RegistrationStatus.CONFIRMED,
        nullable=False
    )

    registered_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    user = relationship(
        "User",
        back_populates="registrations"
    )

    event = relationship(
        "Event",
        back_populates="registrations"
    )

    # One-to-one relationship to Review
    review = relationship(
        "Review",
        back_populates="registration",
        foreign_keys="Review.registration_id",
        uselist=False,
    )
