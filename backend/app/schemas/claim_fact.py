from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.constants.claim_status import ClaimFactStatus, ClaimingParty


class ClaimFactCreate(BaseModel):
    description: str
    proposed_by_party: ClaimingParty = ClaimingParty.CONTRACTOR
    agreed_days: int | None = None
    evidence_ids: list[UUID] = []


class ClaimFactRespond(BaseModel):
    status: ClaimFactStatus
    agreed_days: int | None = None
    response_comment: str | None = None
    responded_by: str | None = None


class ClaimFactOut(BaseModel):
    id: UUID
    claim_id: UUID
    description: str
    proposed_by_party: ClaimingParty
    status: ClaimFactStatus
    agreed_days: int | None
    response_comment: str | None
    responded_by: str | None
    responded_at: datetime | None
    created_at: datetime
    updated_at: datetime
    evidence_ids: list[UUID] = []

    model_config = ConfigDict(from_attributes=True)


class ClaimFactSummaryOut(BaseModel):
    """
    The headline output of the fact-agreement register: the Contractor's
    own ask, versus how many days rest on facts both parties have
    actually agreed, versus how many are still disputed or waiting on
    evidence - so a claim's day-count is never just "the contractor says
    N days," it's a breakdown of what's settled and what isn't.
    """

    claim_id: UUID
    total_facts: int
    agreed_facts: int
    disputed_facts: int
    needs_evidence_facts: int
    proposed_facts: int
    agreed_days_total: int
    disputed_days_total: int
    claimed_days: int | None
