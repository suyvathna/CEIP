import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class EvidenceAccessLog(Base):
    """
    Chain-of-custody trail for evidence: who viewed or downloaded a given
    file, and when. user_id is nullable so a magic-link Engineer access
    (see claim_access_token.py) can still be logged by email instead of a
    user account.
    """

    __tablename__ = "evidence_access_log"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    evidence_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("evidence.id"),
        nullable=False,
    )

    action: Mapped[str] = mapped_column(String(20), nullable=False)

    accessed_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=True,
    )

    accessed_by_email: Mapped[str | None] = mapped_column(String(255))

    accessed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
