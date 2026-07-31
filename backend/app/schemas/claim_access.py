from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr


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

# No request schemas for a public response - the token resolves straight
# to a read-only PDF (see api/claim_access.py's public_router). CEIP has
# no endpoint that accepts a write from outside an authenticated
# Contractor session.
