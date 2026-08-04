from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.constants.determination import DeterminationOutcome
from app.schemas.claim import ClaimClockOut


class DeterminationCreate(BaseModel):
    project_id: UUID

    # Null for a matter that never became a Sub-Clause 20.2 Claim - a
    # valuation dispute, a measurement disagreement, a rate adjustment.
    # Sub-Clause 3.7 governs "any matter or Claim", and every one of
    # those opens its own Notice of Dissatisfaction window.
    claim_id: UUID | None = None

    determination_no: str | None = None
    matter_title: str
    matter_description: str | None = None
    subject_clause: str | None = None

    # Date the Engineer received the matter - start of the 42-day time
    # limit for agreement under 3.7.3.
    referred_date: date


class DeterminationUpdate(BaseModel):
    matter_title: str | None = None
    matter_description: str | None = None
    subject_clause: str | None = None
    referred_date: date | None = None


class DeterminationReceivedRequest(BaseModel):
    determination_notice_date: date

    # The date the determination actually reached the Contractor. The
    # 28-day Sub-Clause 3.7.5 clock runs from THIS, not from the date
    # printed on the Engineer's letter - see the note on the
    # Determination model.
    determination_received_date: date

    determination_summary: str | None = None
    outcome: DeterminationOutcome = DeterminationOutcome.NOT_YET_DETERMINED
    days_determined: int | None = None
    cost_determined: float | None = None
    determination_evidence_id: UUID | None = None


class NoticeOfDissatisfactionRequest(BaseModel):
    nod_given_date: date
    nod_reference: str | None = None
    nod_grounds: str | None = None
    nod_evidence_id: UUID | None = None


class AgreementRequest(BaseModel):
    agreement_reached_date: date
    summary: str | None = None


class DeterminationOut(BaseModel):
    id: UUID
    project_id: UUID
    claim_id: UUID | None
    determination_no: str | None
    matter_title: str
    matter_description: str | None
    subject_clause: str | None
    referred_date: date
    agreement_reached_date: date | None
    determination_notice_date: date | None
    determination_received_date: date | None
    determination_summary: str | None
    outcome: str
    days_determined: int | None
    cost_determined: float | None
    determination_evidence_id: UUID | None
    nod_given_date: date | None
    nod_reference: str | None
    nod_grounds: str | None
    nod_evidence_id: UUID | None
    is_final_and_binding: bool
    became_final_on: date | None
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DeterminationDetailOut(BaseModel):
    determination: DeterminationOut

    # Reuses ClaimClockOut deliberately: the 3.7 clock has exactly the
    # same shape as the 20.2 one (stages, next action, days remaining,
    # at-risk flag), and a second identical schema would only be a second
    # place for the two to drift apart.
    clock: ClaimClockOut

    claim_no: str | None
    claim_title: str | None
