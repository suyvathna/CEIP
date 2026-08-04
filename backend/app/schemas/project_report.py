from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class ProjectReportResponse(BaseModel):
    project_id: UUID
    project_name: str

    total_events: int
    total_daily_logs: int
    total_evidence: int

    open_events: int
    closed_events: int

    high_severity: int
    medium_severity: int
    low_severity: int

    latest_event: str | None
    generated_at: datetime