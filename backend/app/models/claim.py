import uuid
from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, Integer, Numeric, String, Text, func
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

    # The Contractor's own claim reference, as it would appear on the
    # Notice of Claim itself (e.g. "NOC-014") - auto-generated sequentially
    # per project if left blank, but editable since many Cambodian
    # contractors tie claim numbering to their own correspondence/RFI
    # register rather than a bare sequence.
    claim_no: Mapped[str | None] = mapped_column(String(50))

    # The substantive entitlement clause (e.g. "Sub-Clause 8.5(c) -
    # Exceptionally Adverse Climatic Conditions", "Sub-Clause 13.1 -
    # Variation"). Deliberately separate from the Sub-Clause 20.2 process
    # this whole claim record already tracks: 20.2 is HOW you claim,
    # governing_clause is WHY you're entitled to claim at all, and an
    # Engineer's first question on any claim is exactly that "why".
    governing_clause: Mapped[str | None] = mapped_column(String(255))

    # The app.constants.event_types.EventType value the Contractor picked
    # from the "Applicable Governing Clause" dropdown on the New Claim
    # form (e.g. "Late Access to Site") - what governing_clause's text
    # was auto-populated FROM. Kept alongside the free-text
    # governing_clause (which stays editable/overridable) so the claim
    # can still look up the full clause reference/basis/summary from
    # app.constants.fidic_clauses for display, without re-parsing text.
    # Nullable: a claim can still be raised on a ground outside the
    # curated FIDIC reference list, typed directly into governing_clause.
    claim_basis: Mapped[str | None] = mapped_column(String(100))

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

    # The Contractor's own Cost ask, entered by hand - the same "one side
    # of a three-way comparison" role claimed_days plays for time, except
    # Cost previously had no Contractor-side figure captured anywhere at
    # all (only the Engineer's eventual cost_awarded_amount would have
    # existed). Nullable: plenty of claims are EOT-only.
    claimed_cost_amount: Mapped[float | None] = mapped_column(Numeric(18, 2))

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )


class ClaimDailyLog(Base):
    """Many-to-many: the specific Daily Log entries a Contractor is
    pointing to as contemporaneous corroboration for this claim - distinct
    from ClaimEvent, since a claim often rests on several days' logs even
    when built from a single Event."""

    __tablename__ = "claim_daily_logs"

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

    daily_log_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("daily_logs.id"),
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )


class ClaimEvidence(Base):
    """Many-to-many: Evidence (photos/documents) attached directly as
    supporting material for this claim, on top of whatever came in via
    its linked Events/Daily Logs - e.g. a scanned Notice letter or a
    cost breakdown that doesn't belong to any single Event."""

    __tablename__ = "claim_evidence"

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

    evidence_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("evidence.id"),
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
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

    # The Engineer's Cost determination on this response, mirroring
    # days_granted for Cost/EOT+Cost claims. Nullable since most response
    # types (e.g. a plain acknowledgement) carry no cost decision at all.
    cost_awarded_amount: Mapped[float | None] = mapped_column(Numeric(18, 2))

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
