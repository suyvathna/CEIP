from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr

from app.constants.claim_status import ClaimFactStatus, ClaimResponseType


class ClaimAccessTokenCreate(BaseModel):
    recipient_email: EmailStr
    ttl_days: int = 60


class ClaimAccessTokenOut(BaseModel):
    id: UUID
    claim_id: UUID
    token: str
    recipient_email: str
    created_at: datetime
    expires_at: datetime
    last_used_at: datetime | None

    model_config = ConfigDict(from_attributes=True)


class PublicFactResponseRequest(BaseModel):
    """Same shape as ClaimFactRespond but scoped to the magic-link path -
    responded_by is taken from the token's recipient_email, not typed in,
    so a magic-link response can't be attributed to someone else."""

    status: ClaimFactStatus
    agreed_days: int | None = None
    response_comment: str | None = None


class PublicEngineerDecisionRequest(BaseModel):
    response_type: ClaimResponseType
    response_date: date
    days_granted: int | None = None
    comment: str | None = None
