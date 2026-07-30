from datetime import date, datetime, time
from uuid import UUID

from pydantic import BaseModel, computed_field

from app.constants.event_types import EventType
from app.constants.severity import Severity
from app.constants.status import RecordStatus
from app.services.notice_deadline_service import (
    NOTICE_PERIOD_DAYS,
    calculate_notice_deadline,
    days_remaining,
    get_notice_status,
    get_today,
)


class EventCreate(BaseModel):
    project_id: UUID
    title: str
    description: str | None = None
    event_date: date
    event_time: time
    event_type: EventType
    location: str | None = None
    severity: Severity = Severity.LOW


class NoticeGivenRequest(BaseModel):
    notice_given_date: date


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
    notice_given_date: date | None
    created_at: datetime
    updated_at: datetime

    # Not a column on Event - hydrated onto the ORM object by
    # event_service.py from the owning Project's notice_period_days
    # before serialization, so the deadline math below respects any
    # per-project override instead of always assuming the FIDIC
    # unamended 28 days. Falls back to that default if a service call
    # site ever forgets to hydrate it.
    notice_period_days: int = NOTICE_PERIOD_DAYS

    model_config = {
        "from_attributes": True
    }

    @computed_field
    @property
    def notice_deadline(self) -> date:
        return calculate_notice_deadline(self.event_date, self.notice_period_days)

    @computed_field
    @property
    def notice_status(self) -> str:
        return get_notice_status(
            self.event_date,
            self.notice_given_date,
            get_today(),
            self.notice_period_days,
        )

    @computed_field
    @property
    def notice_days_remaining(self) -> int:
        return days_remaining(self.event_date, get_today(), self.notice_period_days)
