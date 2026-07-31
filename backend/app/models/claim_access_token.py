import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class ClaimAccessToken(Base):
    """
    A no-account way for the Contractor to hand a claim to the Engineer
    (or anyone else outside the platform) without them ever touching
    CEIP itself - the token resolves directly to a read-only PDF of the
    claim (see api/claim_access.py's public_router and
    claim_service.get_claim_report_data), not to any page or JSON API of
    this app. There is nothing to log into and nothing to respond
    through: CEIP is Contractor-only, and this is the entire surface the
    Engineer ever sees. Scoped to one claim, until expires_at.
    """

    __tablename__ = "claim_access_tokens"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    claim_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("claims.id"),
        nullable=False,
    )

    token: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)

    recipient_email: Mapped[str] = mapped_column(String(255), nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    last_used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
