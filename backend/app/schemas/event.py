from datetime import date, datetime, time
from uuid import UUID

from pydantic import BaseModel

from app.constants.event_types import EventType
from app.constants.severity import Severity
from app.constants.status import RecordStatus


class EventCreate(BaseModel):
    project_id: UUID
    title: str
    description: str | None = None
    event_date: date
    event_time: time
    event_type: EventType
    location: str | None = None
    severity: Severity = Severity.LOW


class EventResponse(BaseModel):
    id: UUID
    project_id: UUID
    title: str
    description: str | None
    event_date: date
    event_time: time
    event_type: EventType
    location: str | None
    severity: Severity
    status: RecordStatus
    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True
    }