from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr


class ClaimAccessTokenCreate(BaseModel):
    # Optional: this is "for your own record" only (see ShareReportPanel
    # in the frontend) - the link itself works with no email attached,
    # since CEIP doesn't send it anywhere on the Contractor's behalf. A
    # required field here was previously blocking link generation
    # whenever the Contractor just wanted the URL to paste into Telegram
    # or WhatsApp themselves.
    recipient_email: EmailStr | None = None
    ttl_days: int = 60


class ClaimAccessTokenOut(BaseModel):
    id: UUID
    claim_id: UUID
    token: str
    recipient_email: str | None
    created_at: datetime
    expires_at: datetime
    last_used_at: datetime | None

    model_config = ConfigDict(from_attributes=True)

# No request schemas for a public response - the token resolves straight
# to a read-only PDF (see api/claim_access.py's public_router). CEIP has
# no endpoint that accepts a write from outside an authenticated
# Contractor session.
