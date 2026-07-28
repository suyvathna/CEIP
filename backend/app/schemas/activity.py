from datetime import date, datetime, time
from uuid import UUID

from pydantic import BaseModel


class ActivityResponse(BaseModel):
    activity_type: str

    event_id: UUID

    title: str

    event_date: date

    event_time: time

    evidence_count: int

    diary_exists: bool

    created_at: datetime

    model_config = {
        "from_attributes": True
    }