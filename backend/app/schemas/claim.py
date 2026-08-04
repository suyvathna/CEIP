from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.constants.claim_status import ClaimingParty, ClaimResponseType, ClaimType


class ClaimCreate(BaseModel):
    project_id: UUID
    claim_no: str | None = None
    governing_clause: str | None = None
    # The EventType key the "Applicable Governing Clause" dropdown
    # selection came from (see app.constants.fidic_clauses) - None if the
    # Contractor typed a governing_clause outside the curated list.
    claim_basis: str | None = None
    claim_type: ClaimType
    claiming_party: ClaimingParty = ClaimingParty.CONTRACTOR
    title: str
    description: str | None = None
    awareness_date: date
    claimed_days: int | None = None
    claimed_cost_amount: float | None = None
    event_ids: list[UUID] = []
    daily_log_ids: list[UUID] = []
    evidence_ids: list[UUID] = []


class ClaimOut(BaseModel):
    id: UUID
    project_id: UUID
    claim_no: str | None
    governing_clause: str | None
    claim_basis: str | None
    claim_type: ClaimType
    claiming_party: ClaimingParty
    title: str
    description: str | None
    status: str
    awareness_date: date
    notice_submitted_date: date | None
    notice_evidence_id: UUID | None
    detailed_claim_submitted_date: date | None
    legal_basis_statement: str | None
    particulars: str | None
    claimed_days: int | None
    claimed_cost_amount: float | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class NoticeSubmitRequest(BaseModel):
    notice_submitted_date: date
    notice_evidence_id: UUID | None = None


class EngineerLateNoticeFlagRequest(BaseModel):
    response_date: date
    comment: str | None = None
    responded_by: str | None = None


class DetailedClaimSubmitRequest(BaseModel):
    detailed_claim_submitted_date: date
    legal_basis_statement: str
    particulars: str | None = None
    claimed_days: int | None = None


class EngineerDecisionRequest(BaseModel):
    response_type: ClaimResponseType
    response_date: date
    days_granted: int | None = None
    cost_awarded_amount: float | None = None
    comment: str | None = None
    responded_by: str | None = None


class ClaimResponseOut(BaseModel):
    id: UUID
    claim_id: UUID
    response_type: ClaimResponseType
    response_date: date
    days_granted: int | None
    cost_awarded_amount: float | None
    comment: str | None
    responded_by: str | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ClaimClockStageOut(BaseModel):
    stage: str
    label: str
    deadline: date
    status: str
    completed_date: date | None


class ClaimClockOut(BaseModel):
    stages: list[ClaimClockStageOut]
    next_action: ClaimClockStageOut | None
    days_remaining: int | None
    at_risk: bool


class ClaimEventLinkRequest(BaseModel):
    event_id: UUID


class ClaimDailyLogLinkRequest(BaseModel):
    daily_log_id: UUID


class ClaimEvidenceLinkRequest(BaseModel):
    evidence_id: UUID


class ClauseReferenceOut(BaseModel):
    clause_code: str
    clause_title: str
    basis: str
    summary: str


class ClaimClauseOptionOut(BaseModel):
    """One entry in the "Applicable Governing Clause" dropdown."""

    event_type: str
    clause_code: str
    clause_title: str
    basis: str
    summary: str


class ClaimClauseOptionsOut(BaseModel):
    disclaimer: str
    options: list[ClaimClauseOptionOut]


class RequiredRecordItem(BaseModel):
    kind: str
    label: str
    satisfied: bool
    detail: str


class EventRequirementsSummaryOut(BaseModel):
    event_id: UUID
    event_no: str | None
    title: str
    checklist: list[RequiredRecordItem]
    all_satisfied: bool


class ClaimRequirementsOut(BaseModel):
    events: list[EventRequirementsSummaryOut]
    all_satisfied: bool
    missing_count: int


class EngineerDeterminationOut(BaseModel):
    """Latest decision-type response on this claim, for the claim
    detail page's "Engineer's Determination" summary panel."""

    response_date: date
    eot_awarded_days: int | None
    cost_awarded_amount: float | None
    comment: str | None
    responded_by: str | None
    response_type: ClaimResponseType
