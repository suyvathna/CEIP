from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ProjectCreate(BaseModel):
    project_code: str
    project_name: str
    client_name: str
    contractor_name: str | None = None
    engineer_name: str | None = None
    contract_type: str
    country: str
    city: str
    planned_start: date
    planned_finish: date


class ProjectResponse(ProjectCreate):
    id: UUID
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)