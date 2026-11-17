from sqlalchemy import String, Text, Table, Column, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


event_categories = Table(
    "event_categories",
    Base.metadata,

    Column(
        "event_id",
        ForeignKey("events.id"),
        primary_key=True
    ),

    Column(
        "category_id",
        ForeignKey("categories.id"),
        primary_key=True
    )
)


class Category(Base):

    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(
        primary_key=True
    )

    name: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    events = relationship(
        "Event",
        secondary=event_categories,
        back_populates="categories"
    )