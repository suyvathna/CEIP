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

    # FIDIC 2017 Sub-Clause 20.2 default periods (days). Left as optional
    # with the unamended FIDIC defaults so creating a project the old way
    # still works; override these when the contract's Particular
    # Conditions (or an MDB Harmonised Edition, common on ADB/World
    # Bank-funded work) amends them. NOTE: since this schema also backs
    # the project update endpoint, an update PUT must resend the
    # project's current period values or they will reset to these
    # defaults - the edit form does this automatically.
    notice_period_days: int = 28
    detailed_claim_period_days: int = 84
    engineer_late_notice_flag_days: int = 14
    engineer_response_period_days: int = 42


class ProjectResponse(ProjectCreate):
    id: UUID
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
