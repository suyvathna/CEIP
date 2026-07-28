from datetime import date
from uuid import UUID

from pydantic import BaseModel


class TimelineEvent(BaseModel):
    id: UUID
    title: str
    event_type: str

    model_config = {
        "from_attributes": True
    }


class TimelineDay(BaseModel):
    event_date: date
    total_events: int
    events: list[TimelineEvent]