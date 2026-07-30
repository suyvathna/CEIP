from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel


class DailyDiaryCreate(BaseModel):
    project_id: UUID
    event_id: UUID | None = None
    work_completed: str | None = None
    manpower: int | None = None
    equipment: str | None = None
    materials: str | None = None
    delays: str | None = None
    safety: str | None = None
    visitors: str | None = None
    engineer_instruction: str | None = None
    tomorrow_plan: str | None = None
    remarks: str | None = None
    diary_date: date
    additional_event_ids: list[UUID] = []


class DailyDiaryResponse(BaseModel):
    id: UUID
    project_id: UUID
    event_id: UUID | None
    work_completed: str | None
    manpower: int | None
    equipment: str | None
    materials: str | None
    delays: str | None
    safety: str | None
    visitors: str | None
    engineer_instruction: str | None
    tomorrow_plan: str | None
    remarks: str | None
    diary_date: date
    created_at: datetime
    updated_at: datetime
    linked_event_ids: list[UUID] = []

    model_config = {
        "from_attributes": True
    }
