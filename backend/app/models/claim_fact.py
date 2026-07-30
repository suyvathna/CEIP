import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class ClaimFact(Base):
    """
    The core differentiator: an atomic, individually-agreeable factual
    assertion within a claim ("Rebar delivery for Pour 14 was 3 days
    late, delivered 15 March instead of 12 March"). The Engineer marks
    each one Agreed / Disputed / NeedsEvidence independently, so the
    claim's day-count can separate out exactly what both parties already
    agree on from what's still contested, instead of the whole claim
    being one all-or-nothing yes/no.
    """

    __tablename__ = "claim_facts"

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

    description: Mapped[str] = mapped_column(Text, nullable=False)

    proposed_by_party: Mapped[str] = mapped_column(String(20), nullable=False)

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        server_default="Proposed",
    )

    # Days attributable to this specific fact, if it's a delay-bearing
    # fact - summed across Agreed facts to produce the fact-register day
    # total shown alongside the Contractor's own ask and the CPM figure.
    agreed_days: Mapped[int | None] = mapped_column(Integer)

    response_comment: Mapped[str | None] = mapped_column(Text)

    responded_by: Mapped[str | None] = mapped_column(String(255))

    responded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )


class ClaimFactEvidence(Base):
    """Many-to-many: which Evidence records substantiate a given fact."""

    __tablename__ = "claim_fact_evidence"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    fact_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("claim_facts.id"),
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
