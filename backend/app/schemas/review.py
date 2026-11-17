from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator


class ReviewCreate(BaseModel):
    rating: int = Field(ge=1, le=5, description="Integer rating 1–5")
    comment: Optional[str] = Field(
        default=None,
        max_length=2000,
        description="Optional written review (max 2 000 characters)",
    )


class ReviewUpdate(BaseModel):
    rating: int | None = Field(default=None, ge=1, le=5)
    comment: str | None = Field(default=None, max_length=2000)

    @model_validator(mode="after")
    def validate_update(self):
        if not self.model_fields_set:
            raise ValueError("At least one field must be provided.")

        if "rating" in self.model_fields_set and self.rating is None:
            raise ValueError("Rating cannot be null.")

        return self


class ReviewAuthorResponse(BaseModel):
    id: int
    name: str

    model_config = ConfigDict(from_attributes=True)


class ReviewResponse(BaseModel):
    id: int
    event_id: int
    registration_id: int
    rating: int
    comment: Optional[str]
    created_at: datetime
    updated_at: datetime

    # Derived from review.registration.user
    author: ReviewAuthorResponse

    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def from_review(cls, review: object) -> "ReviewResponse":
        from app.models.review import Review as ReviewModel
        r: ReviewModel = review  # type: ignore[assignment]
        return cls(
            id=r.id,
            event_id=r.event_id,
            registration_id=r.registration_id,
            rating=r.rating,
            comment=r.comment,
            created_at=r.created_at,
            updated_at=r.updated_at,
            author=ReviewAuthorResponse(
                id=r.registration.user.id,
                name=r.registration.user.name,
            ),
        )


class EventRatingSummary(BaseModel):
    event_id: int
    average_rating: Optional[float]
    total_reviews: int

    model_config = ConfigDict(from_attributes=True)
