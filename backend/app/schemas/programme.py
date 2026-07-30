from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.constants.claim_status import RiskCategory


class ActivityCreate(BaseModel):
    activity_code: str
    name: str
    planned_start: date
    planned_finish: date
    actual_start: date | None = None
    actual_finish: date | None = None


class ProgrammeActivityOut(BaseModel):
    id: UUID
    project_id: UUID
    activity_code: str
    name: str
    planned_start: date
    planned_finish: date
    actual_start: date | None
    actual_finish: date | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PredecessorLinkRequest(BaseModel):
    predecessor_id: UUID


class EventActivityImpactCreate(BaseModel):
    activity_id: UUID
    impact_days: int
    risk_category: RiskCategory
    notes: str | None = None


class EventActivityImpactOut(BaseModel):
    id: UUID
    event_id: UUID
    activity_id: UUID
    impact_days: int
    risk_category: RiskCategory
    notes: str | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ActivityCPMOut(BaseModel):
    id: UUID
    activity_code: str
    name: str
    duration_days: int
    early_start: date
    early_finish: date
    late_start: date
    late_finish: date
    total_float: int
    is_critical: bool


class ProjectCPMOut(BaseModel):
    project_id: UUID
    project_start: date
    project_finish: date
    activities: list[ActivityCPMOut]


class OverlappingRiskEventOut(BaseModel):
    event_id: UUID
    event_title: str
    activity_id: UUID
    activity_name: str
    impact_days: int
    risk_category: RiskCategory


class ClaimDelayAnalysisOut(BaseModel):
    """
    The "how many days should the claim be" answer, shown as three
    figures side by side rather than one number the platform silently
    picks: what the Contractor is asking for, what the fact register
    shows as agreed, and what a critical-path recalculation over the
    programme actually supports once float absorption is accounted for.
    Concurrent Contractor-Risk events on the same critical window are
    surfaced for transparency (SCL Protocol: they do not reduce the
    Employer-Risk claim's entitlement where each is independently
    critical).
    """

    claim_id: UUID
    baseline_project_finish: date
    claim_impacted_project_finish: date
    gross_critical_delay_days: int
    requested_impact_days: int
    float_absorbed_days: int
    claimed_days: int | None
    fact_register_agreed_days: int | None
    overlapping_contractor_risk_events: list[OverlappingRiskEventOut]
    note: str
