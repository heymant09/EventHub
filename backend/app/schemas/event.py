from datetime import datetime

from pydantic import BaseModel, Field, ConfigDict, model_validator
from pydantic import Field
from app.models.event import EventStatus
from app.schemas.category import CategoryResponse


class EventCreate(BaseModel):
    title: str = Field(min_length=3, max_length=200)
    description: str = Field(min_length=10)
    location: str = Field(min_length=2, max_length=255)
    category_ids: list[int] = Field(default_factory=list)

    start_time: datetime
    end_time: datetime

    capacity: int = Field(gt=0)

    @model_validator(mode="after")
    def validate_event_times(self):
        if not self.model_fields_set:
            raise ValueError("At least one field must be provided")
        for field in self.model_fields_set:
            if getattr(self, field) is None:
                raise ValueError(f"{field} cannot be null.")
        if self.end_time <= self.start_time:
            raise ValueError("Event end time must be after start time.")

        return self


class EventResponse(BaseModel):
    id: int
    title: str
    description: str
    location: str
    start_time: datetime
    end_time: datetime
    capacity: int
    status: EventStatus
    organiser_id: int
    created_at: datetime
    categories: list[CategoryResponse] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)

class EventUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=3, max_length=200)
    description: str | None = Field(default=None, min_length=10)
    location: str | None = Field(default=None, min_length=2, max_length=255)
    category_ids: list[int] | None = None

    start_time: datetime | None = None
    end_time: datetime | None = None

    capacity: int | None = Field(default=None, gt=0)

    @model_validator(mode="after")
    def validate_event_times(self):
        if self.start_time is not None and self.end_time is not None:
            if self.end_time <= self.start_time:
                raise ValueError("Event end time must be after start time.")

        return self
