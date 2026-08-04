import uuid
from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Correspondence(Base):
    __tablename__ = "correspondence"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id"),
        nullable=False,
    )

    # "COR-001" style, auto-generated sequentially per project - mirrors
    # Event.event_no / Claim.claim_no (see _next_correspondence_no in
    # correspondence_service.py).
    correspondence_no: Mapped[str | None] = mapped_column(String(50))

    # Outgoing (Contractor -> Engineer) or Incoming (Engineer -> Contractor).
    direction: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    correspondence_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )

    # The letter/transmittal/email reference printed on the document
    # itself - ours if Outgoing, theirs if Incoming.
    reference: Mapped[str | None] = mapped_column(String(100))

    subject: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )

    method: Mapped[str | None] = mapped_column(String(30))

    # Free-text pointer to what this is about - e.g. "VO-003", "CLM-002",
    # "Sub-Clause 20.2.1 Notice". No FK on purpose: correspondence is
    # frequently about something that isn't (yet, or ever) a record in
    # this platform, and forcing a link would make logging a letter
    # depend on first finding the right claim/variation to attach it to.
    related_to: Mapped[str | None] = mapped_column(String(200))

    summary: Mapped[str | None] = mapped_column(Text)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )
