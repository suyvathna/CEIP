from datetime import date, time
from uuid import UUID

from pydantic import BaseModel

from app.constants.event_types import EventType
from app.constants.severity import Severity
from app.constants.status import RecordStatus


class TimelineEvent(BaseModel):
    id: UUID
    title: str
    description: str | None
    event_date: date
    event_time: time
    event_type: EventType
    severity: Severity
    status: RecordStatus
    location: str | None

    model_config = {
        "from_attributes": True
    }


class TimelineResponse(BaseModel):
    project_id: UUID
    total_events: int
    events: list[TimelineEvent]