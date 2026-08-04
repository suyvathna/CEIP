import uuid
from datetime import date, datetime

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class ComplianceObligation(Base):
    """
    One materialised instance of an Engine A rule - "the April 2026
    progress report", "the initial programme", "the Statement at
    Completion".

    Why these are stored rows rather than computed on read (which is how
    claim_clock_service deliberately handles Sub-Clause 20.2): an
    obligation carries per-instance human state - it was submitted on
    this date, with this evidence, or it was waived because this contract
    has no advance payment. That state has nowhere to live in a computed
    view. The deadline itself is still never authored by a human: due_date
    is recomputed from anchor_date + the rule's offset on every scheduler
    tick, so retuning a project's periods or correcting its Taking-Over
    date re-dates the whole register instead of leaving stale dates
    behind.

    Idempotency comes from (project_id, rule_key, period_key): the tick
    can run a hundred times a day and produce the same rows.
    """

    __tablename__ = "compliance_obligations"

    __table_args__ = (
        UniqueConstraint(
            "project_id",
            "rule_key",
            "period_key",
            name="uq_compliance_obligation_project_rule_period",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id"),
        nullable=False,
        index=True,
    )

    # Key into app.constants.compliance_rules.RULES_BY_KEY.
    rule_key: Mapped[str] = mapped_column(String(80), nullable=False)

    # "2026-04" for a monthly instance, "once" for a one-off. Second half
    # of the uniqueness key.
    period_key: Mapped[str] = mapped_column(String(20), nullable=False)

    # Clause number as it reads in THIS project's edition - snapshotted at
    # generation so a register printed today still matches what the PM saw
    # (Progress Reports are 4.20 under 2017 and 4.21 under 1999).
    clause_code: Mapped[str] = mapped_column(String(40), nullable=False)

    title: Mapped[str] = mapped_column(String(255), nullable=False)

    category: Mapped[str] = mapped_column(String(30), nullable=False)

    owed_by: Mapped[str] = mapped_column(String(20), nullable=False)

    # The contract milestone the deadline is measured from. Kept on the
    # row (not just on the rule) so the register can show its own working:
    # "due 84 days after Taking-Over on 12 Mar 2026".
    anchor_date: Mapped[date | None] = mapped_column(Date)

    offset_days: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default="0"
    )

    # Recomputed from anchor_date + offset_days on every tick. Stored so
    # the alerting sweep can filter in SQL instead of loading every
    # obligation in the system into Python.
    due_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)

    # Period covered, for monthly instances (null for one-offs).
    period_start: Mapped[date | None] = mapped_column(Date)
    period_end: Mapped[date | None] = mapped_column(Date)

    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        server_default="Pending",
        index=True,
    )

    # Missing this forfeits an entitlement rather than merely being a
    # breach - drives CRITICAL alerting. Copied from the rule so a
    # historical row keeps the severity it was generated under.
    rights_destroying: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default="false"
    )

    # True when this obligation was ALREADY past its due date the moment
    # the register first generated it - i.e. it fell due before CEIP had
    # ever heard of this project.
    #
    # These are facts about the past, not tasks. A job that had been
    # running five months before anyone typed it into the platform
    # back-generates twenty-odd of them, and alerting on each one
    # produced a wall of CRITICAL notices about progress reports that
    # were late in March, drowning the three things the PM could
    # actually still act on. They stay in the register - visible,
    # recordable, waivable, and counted in one summary alert - but they
    # never raise an alert of their own.
    #
    # Cleared automatically if a milestone correction moves the deadline
    # back into the future, because then it is a real task again.
    is_historical: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default="false"
    )

    submitted_date: Mapped[date | None] = mapped_column(Date)

    submitted_reference: Mapped[str | None] = mapped_column(String(120))

    # The document that proves it went in. Locked on attach, same rule
    # Evidence follows for a Notice of Claim.
    evidence_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("evidence.id"),
    )

    waived_reason: Mapped[str | None] = mapped_column(Text)

    notes: Mapped[str | None] = mapped_column(Text)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )
