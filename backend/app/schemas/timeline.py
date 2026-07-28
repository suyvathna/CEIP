from datetime import date, time
from uuid import UUID

from pydantic import BaseModel


class TimelineEvent(BaseModel):
    id: UUID
    title: str
    description: str | None
    event_date: date
    event_time: time
    event_type: str
    severity: str
    status: str
    location: str | None

    model_config = {
        "from_attributes": True
    }


class TimelineResponse(BaseModel):
    project_id: UUID
    total_events: int
    events: list[TimelineEvent]


class TimelineItem(BaseModel):
    event_id: UUID
    title: str
    event_type: str

    event_date: date
    event_time: time

    evidence_count: int

    model_config = {
        "from_attributes": True
    }