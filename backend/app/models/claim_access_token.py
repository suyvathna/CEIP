import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class ClaimAccessToken(Base):
    """
    A low-friction path for the Engineer to participate in a claim
    without needing a CEIP user account - a real adoption-risk mitigation,
    since the Engineer will rarely be willing to register on a platform
    the Contractor's side deployed. The token grants read access to one
    claim (facts, evidence, delay analysis) plus the ability to respond
    to facts and submit an overall Engineer response, scoped to that
    claim only, until expires_at.
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
