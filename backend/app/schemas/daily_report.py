from app.schemas.daily_diary import DailyDiaryResponse
from app.schemas.event import EventResponse


class DailyReportResponse(DailyDiaryResponse):
    event: EventResponse
    evidence_count: int