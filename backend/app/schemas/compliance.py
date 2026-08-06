from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.constants.compliance import ObligationCategory, ObligationStatus, OwedBy


class ObligationOut(BaseModel):
    id: UUID
    project_id: UUID
    rule_key: str
    period_key: str
    clause_code: str
    title: str
    category: str
    owed_by: str
    anchor_date: date | None
    offset_days: int
    due_date: date
    period_start: date | None
    period_end: date | None
    status: str
    rights_destroying: bool
    is_historical: bool
    submitted_date: date | None
    submitted_reference: str | None
    evidence_id: UUID | None
    waived_reason: str | None
    notes: str | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ObligationRuleOut(BaseModel):
    """Reference data for the compliance screen: what each rule is and
    why it exists, so a PM can decide whether it applies to their
    contract before waiving it."""

    key: str
    title: str
    clause_code: str
    clause_title: str
    cadence: str
    category: ObligationCategory
    owed_by: OwedBy
    description: str
    rights_destroying: bool
    conditional: bool


class ComplianceRulesOut(BaseModel):
    disclaimer: str
    contract_edition: str
    rules: list[ObligationRuleOut]


class EventDrivenRuleOut(BaseModel):
    """Reference data for the EVENT-DRIVEN half of the document register:
    what notice/reply this is, what triggers it, and where in the app to
    actually track a live instance of it, if anywhere."""

    key: str
    title: str
    clause_code: str
    direction: OwedBy
    trigger: str
    deadline: str
    tracked_in: str | None
    description: str


class EventDrivenRulesOut(BaseModel):
    disclaimer: str
    contract_edition: str
    rules: list[EventDrivenRuleOut]


class ObligationSummaryOut(BaseModel):
    total: int
    open: int

    # "18 open" reads very differently once you know 15 of them fell due
    # before CEIP ever saw the project.
    historical_open: int = 0
    live_open: int = 0

    pending: int
    due_soon: int
    overdue: int
    submitted: int
    submitted_late: int
    waived: int
    superseded: int


class ComplianceRegisterOut(BaseModel):
    project_id: UUID
    summary: ObligationSummaryOut
    obligations: list[ObligationOut]


class ObligationSubmitRequest(BaseModel):
    submitted_date: date
    submitted_reference: str | None = None
    evidence_id: UUID | None = None
    notes: str | None = None


class ObligationWaiveRequest(BaseModel):
    # Required, not optional. A waiver with no stated reason is
    # indistinguishable from someone clearing an inconvenient row, and
    # this register is meant to survive being read back in a dispute.
    reason: str
    evidence_id: UUID | None = None


class ComplianceRunOut(BaseModel):
    id: UUID
    run_date: date
    trigger_source: str
    status: str
    projects_processed: int
    obligations_created: int
    obligations_updated: int
    notifications_created: int
    notifications_resolved: int
    error: str | None
    started_at: datetime
    finished_at: datetime | None

    model_config = ConfigDict(from_attributes=True)


class RegenerateResultOut(BaseModel):
    """What a Rebuild actually did.

    Returned so the button can say so. Silently succeeding was what made
    the register feel frozen - a PM who corrects a milestone, presses
    Rebuild and sees nothing change on screen has no way to tell the
    difference between "it worked and nothing needed changing" and "it is
    broken"."""

    created: int
    updated: int
    alerts: int
    resolved: int


class ObligationStatusOut(BaseModel):
    """Enum reference for the register's filter chips."""

    statuses: list[ObligationStatus]
    categories: list[ObligationCategory]
