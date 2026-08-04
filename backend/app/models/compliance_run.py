import uuid
from datetime import date, datetime

from sqlalchemy import DateTime, Date, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class ComplianceRun(Base):
    """
    One execution of the daily sweep - the scheduler's own audit trail.

    Two reasons this exists rather than the job just running silently:

    1. If a PM says "the system never warned me", this answers it. Every
       run records what it generated and alerted on, and a run that
       crashed records the error instead of disappearing.
    2. It makes multi-worker deployment honest. The tick also takes a
       Postgres advisory lock (see compliance_service.run_daily_tick), so
       four uvicorn workers all firing at 06:00 produce one run, not
       four - but the lock leaves no trace once released, and this table
       does.

    Idempotency does NOT depend on this table. Obligations dedupe on
    (project, rule, period) and notifications on dedupe_key, so a
    duplicated run is harmless by construction; this is observability,
    not a mutex.
    """

    __tablename__ = "compliance_runs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    # The project-local calendar day the run was for (Asia/Phnom_Penh, in
    # line with notice_deadline_service) - not the server's UTC date.
    run_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)

    # "scheduled" | "manual" | "startup"
    trigger_source: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        server_default="scheduled",
    )

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        server_default="running",
    )

    projects_processed: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default="0"
    )

    obligations_created: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default="0"
    )

    obligations_updated: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default="0"
    )

    notifications_created: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default="0"
    )

    # How many standing alerts the sweep retired because the thing they
    # were about got done, waived, or re-dated. Recorded alongside the
    # created count so "Run sweep now" can report both - a sweep that
    # resolves twelve alerts and raises none has done real work, and
    # saying nothing at all is what made the button feel broken.
    notifications_resolved: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default="0"
    )

    error: Mapped[str | None] = mapped_column(Text)

    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
