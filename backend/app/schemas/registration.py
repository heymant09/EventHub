from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.event import EventStatus
from app.models.registration import RegistrationStatus


class RegistrationEventSummary(BaseModel):
    id: int
    title: str
    location: str
    start_time: datetime
    end_time: datetime
    status: EventStatus

    model_config = ConfigDict(from_attributes=True)


class RegistrationAttendeeSummary(BaseModel):
    id: int
    name: str
    email: str

    model_config = ConfigDict(from_attributes=True)


class RegistrationResponse(BaseModel):
    id: int
    user_id: int
    event_id: int
    status: RegistrationStatus
    registered_at: datetime
    event: RegistrationEventSummary
    attendee: RegistrationAttendeeSummary = Field(
        validation_alias="user",
        serialization_alias="attendee",
    )

    model_config = ConfigDict(from_attributes=True)
