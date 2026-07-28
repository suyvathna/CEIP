from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class RecentEvent(BaseModel):
    id: UUID
    title: str
    event_type: str
    status: str
    severity: str
    created_at: datetime

    model_config = {
        "from_attributes": True
    }


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

    recent_events: list[RecentEvent]