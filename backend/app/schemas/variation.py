from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.constants.variation import VariationOrigin, VariationStatus
from app.schemas.claim import ClaimClockOut


class VariationCreate(BaseModel):
    project_id: UUID
    variation_no: str | None = None
    title: str
    description: str | None = None

    origin: VariationOrigin

    instruction_reference: str | None = None
    instruction_date: date | None = None

    # Defaults to instruction_date server-side when omitted. The
    # Sub-Clause 3.5 clock runs from receipt, so capture it separately
    # wherever the two differ.
    instruction_received_date: date | None = None

    # Forced to False for UNLABELLED_INSTRUCTION / CONSTRUCTIVE origins
    # and True for ENGINEER_INSTRUCTION - the flag and the origin are not
    # allowed to disagree, since the whole 3.5 alarm hangs off them.
    is_labelled_as_variation: bool = False

    work_commenced: bool = False
    work_commenced_date: date | None = None

    proposal_requested_date: date | None = None

    event_id: UUID | None = None
    claim_id: UUID | None = None


class VariationUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    origin: VariationOrigin | None = None
    status: VariationStatus | None = None
    instruction_reference: str | None = None
    instruction_date: date | None = None
    instruction_received_date: date | None = None
    is_labelled_as_variation: bool | None = None
    work_commenced: bool | None = None
    work_commenced_date: date | None = None
    proposal_requested_date: date | None = None
    claim_id: UUID | None = None
    event_id: UUID | None = None


class VariationNoticeRequest(BaseModel):
    notice_given_date: date
    notice_reference: str | None = None
    notice_evidence_id: UUID | None = None


class VariationProposalRequest(BaseModel):
    proposal_submitted_date: date
    quoted_days: int | None = None
    quoted_cost: float | None = None


class VariationValuationRequest(BaseModel):
    agreed_days: int | None = None
    agreed_cost: float | None = None
    status: VariationStatus = VariationStatus.VALUED


class VariationOut(BaseModel):
    id: UUID
    project_id: UUID
    variation_no: str | None
    title: str
    description: str | None
    origin: str
    status: str
    instruction_reference: str | None
    instruction_date: date | None
    instruction_received_date: date | None
    is_labelled_as_variation: bool
    work_commenced: bool
    work_commenced_date: date | None
    notice_given_date: date | None
    notice_reference: str | None
    notice_evidence_id: UUID | None
    proposal_requested_date: date | None
    proposal_submitted_date: date | None
    quoted_days: int | None
    quoted_cost: float | None
    agreed_days: int | None
    agreed_cost: float | None
    claim_id: UUID | None
    event_id: UUID | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class VariationClockOut(ClaimClockOut):
    # The one thing the shared clock shape can't express: a Contractor
    # who started the instructed work before giving the Sub-Clause 3.5
    # Notice is already out of time, no matter what the remaining-days
    # arithmetic says.
    notice_late_because_work_started: bool = False


class VariationDetailOut(BaseModel):
    variation: VariationOut
    clock: VariationClockOut
    contract_edition: str | None


class VariationOriginOptionOut(BaseModel):
    value: str
    label: str
    description: str
    triggers_immediate_notice: bool


class VariationOriginOptionsOut(BaseModel):
    clause_code: str
    disclaimer: str
    options: list[VariationOriginOptionOut]
