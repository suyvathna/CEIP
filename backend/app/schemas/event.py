from datetime import date, datetime, time
from uuid import UUID

from pydantic import BaseModel


class EventCreate(BaseModel):
    project_id: UUID
    title: str
    description: str | None = None
    event_date: date
    event_time: time
    event_type: str
    location: str | None = None
    severity: str = "Low"


class EventResponse(BaseModel):
    id: UUID
    project_id: UUID
    title: str
    description: str | None
    event_date: date
    event_time: time
    event_type: str
    location: str | None
    severity: str
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True
    }