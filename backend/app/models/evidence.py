import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Evidence(Base):
    __tablename__ = "evidence"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    # An attachment belongs to exactly one owner: an Event, a DailyLog
    # directly (for the Daily Log's own Photos section - a delivery photo,
    # an inspection photo, a general site photo), a Correspondence record
    # (the scanned letter/email itself), or a ComplianceObligation (the
    # scanned letter/transmittal proving a submission, or the basis for a
    # waiver). All four nullable - forcing every attachment through an
    # Event was exactly the friction that made the future camera-API
    # import awkward, and the same is true of a letter that predates any
    # Event it might relate to. Enforced as "exactly one of the four" in
    # the service layer.
    event_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("events.id"),
        nullable=True,
    )

    daily_log_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("daily_logs.id"),
        nullable=True,
    )

    correspondence_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("correspondence.id"),
        nullable=True,
    )

    obligation_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("compliance_obligations.id"),
        nullable=True,
    )

    # Which Daily Log section this photo documents (see PhotoCategory).
    # Nullable/free text rather than a hard enum column so a camera-API
    # import that can't confidently classify a photo can still land it as
    # "General" instead of failing the upload.
    category: Mapped[str | None] = mapped_column(String(50))

    # Short human caption, matching the template's per-photo caption line
    # (e.g. "V6 props (support) installation").
    caption: Mapped[str | None] = mapped_column(String(255))

    filename: Mapped[str] = mapped_column(String(255))

    object_name: Mapped[str] = mapped_column(String(255))

    content_type: Mapped[str] = mapped_column(String(100))

    # Captured at upload from the actual file bytes. This is what lets the
    # platform stand behind a piece of evidence as genuinely unaltered
    # since the moment it was submitted - a hash mismatch on re-download
    # would mean the underlying object was swapped after the fact.
    sha256_hash: Mapped[str | None] = mapped_column(String(64))

    # Set once evidence is attached to a submitted Notice of Claim or a
    # fully detailed claim (see claim_service.py). Locked evidence can
    # still be viewed/downloaded but the API refuses to delete it, so a
    # claim's supporting record can't quietly change after the Engineer
    # has started relying on it.
    is_locked: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default="false",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
