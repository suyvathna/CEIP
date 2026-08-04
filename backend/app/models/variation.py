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


class Variation(Base):
    """
    A Clause 13 Variation, and - more importantly - the register of
    instructions that might be one.

    The record this platform exists to force is the second kind. FIDIC
    2017 Sub-Clause 3.5 (1999: 3.3) requires that where the Contractor
    considers an instruction constitutes a Variation, it gives Notice
    "immediately, and before commencing any work related to the
    instruction". Engineers change the Works constantly without writing
    the word Variation anywhere - a marked-up drawing, a site memo, a
    line in minutes of meeting. A Contractor who simply builds what was
    asked and raises it at the next valuation has already lost: the
    Notice had to come first.

    So origin and is_labelled_as_variation are the two fields that matter
    most here. An instruction logged with
    is_labelled_as_variation = False starts a clock that Engine B treats
    as rights-destroying from the first alert, because in contractual
    terms it very nearly is.

    Deadlines are computed on read from instruction_received_date /
    proposal_requested_date plus the project's configured periods (see
    claim_clock_service.get_variation_clock), the same rule the rest of
    the platform follows. As with Determination, RECEIPT is what the
    clock runs from, not the date printed on the instruction.
    """

    __tablename__ = "variations"

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

    # "VO-001" style, sequential per project - mirrors Claim.claim_no and
    # Event.event_no so it can be cited in correspondence.
    variation_no: Mapped[str | None] = mapped_column(String(50))

    title: Mapped[str] = mapped_column(String(255), nullable=False)

    description: Mapped[str | None] = mapped_column(Text)

    origin: Mapped[str] = mapped_column(String(30), nullable=False)

    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        server_default="Logged",
        index=True,
    )

    # The Engineer's own reference for the instruction, drawing revision
    # or memo this came in on.
    instruction_reference: Mapped[str | None] = mapped_column(String(120))

    # Date printed on the instruction.
    instruction_date: Mapped[date | None] = mapped_column(Date)

    # Date the Contractor actually received it - what the Sub-Clause 3.5
    # clock runs from.
    instruction_received_date: Mapped[date | None] = mapped_column(Date)

    # False is the alarm condition: an instruction that changes the Works
    # but never used the word "Variation".
    is_labelled_as_variation: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default="false",
    )

    # True once work under the instruction has actually started. Recorded
    # because Sub-Clause 3.5 requires the Notice BEFORE commencement -
    # if this is set and notice_given_date is not, the Contractor is
    # already on the wrong side of the clause and needs to know that
    # plainly rather than be told a deadline is "approaching".
    work_commenced: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default="false",
    )

    work_commenced_date: Mapped[date | None] = mapped_column(Date)

    # --- Sub-Clause 3.5 Notice --------------------------------------
    notice_given_date: Mapped[date | None] = mapped_column(Date)

    notice_reference: Mapped[str | None] = mapped_column(String(120))

    notice_evidence_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("evidence.id"),
    )

    # --- Sub-Clause 13.3 proposal -----------------------------------
    proposal_requested_date: Mapped[date | None] = mapped_column(Date)

    proposal_submitted_date: Mapped[date | None] = mapped_column(Date)

    quoted_days: Mapped[int | None] = mapped_column(Integer)

    quoted_cost: Mapped[float | None] = mapped_column(Numeric(18, 2))

    agreed_days: Mapped[int | None] = mapped_column(Integer)

    agreed_cost: Mapped[float | None] = mapped_column(Numeric(18, 2))

    # --- Links -------------------------------------------------------
    # Set when the Engineer refuses to treat the instruction as a
    # Variation and it has to be pursued as a Sub-Clause 20.2 Claim
    # instead.
    claim_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("claims.id"),
    )

    # The site Event this arose from, where there was one.
    event_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("events.id"),
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
