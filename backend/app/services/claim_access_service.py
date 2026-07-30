import secrets
from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.claim_access_token import ClaimAccessToken

DEFAULT_TOKEN_TTL_DAYS = 60


def create_access_token(
    db: Session,
    claim_id: UUID,
    recipient_email: str,
    ttl_days: int = DEFAULT_TOKEN_TTL_DAYS,
) -> ClaimAccessToken:
    token = ClaimAccessToken(
        claim_id=claim_id,
        token=secrets.token_urlsafe(32),
        recipient_email=recipient_email,
        expires_at=datetime.now(timezone.utc) + timedelta(days=ttl_days),
    )
    db.add(token)
    db.commit()
    db.refresh(token)
    return token


def resolve_access_token(db: Session, token: str) -> ClaimAccessToken | None:
    record = db.scalar(
        select(ClaimAccessToken).where(ClaimAccessToken.token == token)
    )

    if record is None:
        return None

    if record.expires_at < datetime.now(timezone.utc):
        return None

    record.last_used_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(record)

    return record


def get_claim_tokens(db: Session, claim_id: UUID) -> list[ClaimAccessToken]:
    stmt = select(ClaimAccessToken).where(ClaimAccessToken.claim_id == claim_id)
    return list(db.scalars(stmt).all())
