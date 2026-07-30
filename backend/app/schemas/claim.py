from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.constants.claim_status import ClaimingParty, ClaimResponseType, ClaimType


class ClaimCreate(BaseModel):
    project_id: UUID
    claim_type: ClaimType
    claiming_party: ClaimingParty = ClaimingParty.CONTRACTOR
    title: str
    description: str | None = None
    awareness_date: date
    claimed_days: int | None = None
    event_ids: list[UUID] = []


class ClaimOut(BaseModel):
    id: UUID
    project_id: UUID
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
    comment: str | None = None
    responded_by: str | None = None


class ClaimResponseOut(BaseModel):
    id: UUID
    claim_id: UUID
    response_type: ClaimResponseType
    response_date: date
    days_granted: int | None
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
