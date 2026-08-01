from app.schemas.daily_log import DailyLogResponse
from app.schemas.event import EventResponse


class DailyReportResponse(DailyLogResponse):
    event: EventResponse | None
    evidence_count: int
