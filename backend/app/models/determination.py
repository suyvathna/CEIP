import uuid
from datetime import date, datetime

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Determination(Base):
    """
    A matter referred to the Engineer under FIDIC 2017 Sub-Clause 3.7
    (1999: 3.5) - "Agreement or Determination".

    Why this is not just more columns on Claim: 3.7 governs "any matter
    or Claim". Engineers determine valuations, measurement disputes and
    rate adjustments that never became a Sub-Clause 20.2 Claim at all,
    and every one of those still opens a Notice of Dissatisfaction
    window. claim_id is therefore nullable, and a standalone
    determination is a first-class record.

    As with Claim, no deadline is stored. The three dates that matter -
    the 42-day agreement limit, the further 42-day determination window
    and the 28-day NOD window - are computed on read from
    referred_date / determination_received_date plus the owning
    Project's configured periods, so changing those periods re-dates
    every open determination instead of leaving stale values behind. See
    claim_clock_service.get_determination_clock.

    The one date that is captured with real care is
    determination_received_date. The NOD clock runs from RECEIPT of the
    Engineer's Notice, not from the date printed on it, and on Cambodian
    jobs those two are routinely a week or more apart. Recording the
    date on the letter and calling it the start of the clock quietly
    shortens the Contractor's window - so both are stored, and the clock
    only ever uses receipt.
    """

    __tablename__ = "determinations"

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

    # Null for a matter that is not a Sub-Clause 20.2 Claim.
    claim_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("claims.id"),
        index=True,
    )

    # "DET-001" style, sequential per project - mirrors Claim.claim_no.
    determination_no: Mapped[str | None] = mapped_column(String(50))

    matter_title: Mapped[str] = mapped_column(String(255), nullable=False)

    matter_description: Mapped[str | None] = mapped_column(Text)

    # The clause the underlying matter rests on, e.g. "Sub-Clause 12.3 -
    # Valuation of the Works". Free text: the range of things an Engineer
    # determines is wider than any curated list.
    subject_clause: Mapped[str | None] = mapped_column(String(255))

    # Date the Engineer received the Claim or the matter - start of the
    # 3.7.3 time limit for agreement.
    referred_date: Mapped[date] = mapped_column(Date, nullable=False)

    agreement_reached_date: Mapped[date | None] = mapped_column(Date)

    # The date printed on the Engineer's Notice of determination.
    determination_notice_date: Mapped[date | None] = mapped_column(Date)

    # The date the Contractor actually received it. THIS is what the
    # 28-day NOD clock runs from - see the class docstring.
    determination_received_date: Mapped[date | None] = mapped_column(Date)

    determination_summary: Mapped[str | None] = mapped_column(Text)

    outcome: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        server_default="NotYetDetermined",
    )

    days_determined: Mapped[int | None] = mapped_column(Integer)

    cost_determined: Mapped[float | None] = mapped_column(Numeric(18, 2))

    determination_evidence_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("evidence.id"),
    )

    # --- Notice of Dissatisfaction (3.7.5) --------------------------
    nod_given_date: Mapped[date | None] = mapped_column(Date)

    nod_reference: Mapped[str | None] = mapped_column(String(120))

    nod_grounds: Mapped[str | None] = mapped_column(Text)

    nod_evidence_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("evidence.id"),
    )

    # Set by Engine B once the NOD window closes with no Notice given.
    # Stored rather than computed because it is a terminal fact about the
    # contract, and because the moment it flips is exactly what the audit
    # trail needs to show.
    is_final_and_binding: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default="false",
    )

    became_final_on: Mapped[date | None] = mapped_column(Date)

    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        server_default="UnderConsultation",
        index=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )
