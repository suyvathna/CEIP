import uuid
from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Claim(Base):
    """
    The FIDIC Sub-Clause 20.2 governed process an Event (or several) turns
    into once someone decides to actually claim EOT and/or cost for it.
    Deadline dates (notice, fully-detailed-claim, Engineer response) are
    NOT stored here - they're computed on read from awareness_date /
    notice_submitted_date / detailed_claim_submitted_date plus the owning
    Project's configured periods (see services/claim_clock_service.py), so
    changing a project's periods retroactively re-dates every open claim
    correctly instead of leaving stale baked-in deadlines.
    """

    __tablename__ = "claims"

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

    claim_type: Mapped[str] = mapped_column(String(20), nullable=False)

    claiming_party: Mapped[str] = mapped_column(String(20), nullable=False)

    title: Mapped[str] = mapped_column(String(255), nullable=False)

    description: Mapped[str | None] = mapped_column(Text)

    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        server_default="Notified",
    )

    # The Sub-Clause 20.2.1 test is "became aware, or should have become
    # aware" - a legal/factual question, not automatically today's date or
    # the linked event's date, so it's captured explicitly rather than
    # inferred.
    awareness_date: Mapped[date] = mapped_column(Date, nullable=False)

    notice_submitted_date: Mapped[date | None] = mapped_column(Date)

    # The actual Notice of Claim document, as Evidence - see the strategy
    # note on notice_given_date being unverifiable as a bare typed date.
    # The upload timestamp on this Evidence row, not this date field, is
    # what a dispute would actually rely on.
    notice_evidence_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("evidence.id"),
    )

    detailed_claim_submitted_date: Mapped[date | None] = mapped_column(Date)

    legal_basis_statement: Mapped[str | None] = mapped_column(Text)

    particulars: Mapped[str | None] = mapped_column(Text)

    # The Contractor's own ask, entered by hand. Kept distinct from the
    # fact-register total (ClaimFact.agreed_days summed) and the
    # CPM-calculated figure (see programme delay-analysis endpoint) so all
    # three can be shown side by side rather than the platform silently
    # picking one.
    claimed_days: Mapped[int | None] = mapped_column(Integer)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )


class ClaimEvent(Base):
    """Many-to-many: a claim is very often built from more than one
    logged Event (e.g. three weather-day entries plus a late-instruction
    event combined into one continuous-effect EOT claim)."""

    __tablename__ = "claim_events"

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

    event_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("events.id"),
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )


class ClaimResponse(Base):
    """
    Every dated Engineer (or Employer's Representative) action against a
    claim - this is both what drives the 14-day / 42-day clocks forward
    and the audit trail a DAAB or arbitrator would want if the claim
    escalates under Clause 21.
    """

    __tablename__ = "claim_responses"

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

    response_type: Mapped[str] = mapped_column(String(30), nullable=False)

    response_date: Mapped[date] = mapped_column(Date, nullable=False)

    days_granted: Mapped[int | None] = mapped_column(Integer)

    comment: Mapped[str | None] = mapped_column(Text)

    # Free-text identity of whoever responded - a full user account
    # (authenticated Engineer) or an email captured via a magic-link
    # response (see claim_access_token.py). Not a FK on purpose: the
    # magic-link path is explicitly meant to work without the Engineer
    # ever having a User row.
    responded_by: Mapped[str | None] = mapped_column(String(255))

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
