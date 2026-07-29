from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from app.constants.event_types import EventType
from app.constants.severity import Severity
from app.constants.status import RecordStatus


class RecentEvent(BaseModel):
    id: UUID
    title: str
    event_type: EventType
    severity: Severity
    status: RecordStatus
    created_at: datetime

    model_config = {
        "from_attributes": True
    }


class EventTypeStatistic(BaseModel):
    event_type: str
    total: int


class DashboardResponse(BaseModel):
    project_id: UUID
    project_name: str

    total_events: int
    total_daily_diaries: int
    total_evidence: int

    open_events: int
    closed_events: int

    high_severity_events: int
    medium_severity_events: int
    low_severity_events: int

    event_type_statistics: list[EventTypeStatistic]

    recent_events: list[RecentEvent]