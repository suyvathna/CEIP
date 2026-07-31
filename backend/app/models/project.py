import uuid
from datetime import date, datetime

from sqlalchemy import Date, DateTime, Integer, Numeric, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    project_code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)

    project_name: Mapped[str] = mapped_column(String(255), nullable=False)

    client_name: Mapped[str] = mapped_column(String(255), nullable=False)

    contractor_name: Mapped[str | None] = mapped_column(String(255))

    engineer_name: Mapped[str | None] = mapped_column(String(255))

    contract_type: Mapped[str] = mapped_column(String(100), nullable=False)

    # The Contractor's own contract/agreement reference number - what a PM
    # actually calls the job in correspondence with the Employer/Engineer,
    # distinct from the platform's internal project_code.
    contract_no: Mapped[str | None] = mapped_column(String(100))

    site_address: Mapped[str | None] = mapped_column(String(500))

    country: Mapped[str] = mapped_column(String(100), nullable=False)

    city: Mapped[str] = mapped_column(String(100), nullable=False)

    # FIDIC terms: planned_start is the Commencement Date (Sub-Clause 8.1);
    # planned_finish is the Completion Date implied by the Time for
    # Completion. planned_finish is never entered directly - it's always
    # server-computed as planned_start + duration_days (see
    # project_service.py) so the two can never silently disagree.
    planned_start: Mapped[date] = mapped_column(Date)

    planned_finish: Mapped[date] = mapped_column(Date)

    # Time for Completion (Sub-Clause 8.2), in days from the Commencement
    # Date. This is the number the Contractor actually negotiates and the
    # EOT clock runs against - planned_finish is derived from it, not the
    # other way around.
    duration_days: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        server_default="0",
    )

    currency: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        server_default="USD",
    )

    contract_value: Mapped[float | None] = mapped_column(Numeric(18, 2))

    # "Planning" / "In Progress" are computed on read from today's date
    # against planned_start (see project_service.compute_effective_status)
    # and are NOT what's stored here for those two states. "Completed" and
    # "On Hold" ARE deliberately stored - actual completion is a business
    # decision (e.g. Taking-Over Certificate issued under Sub-Clause 10.1),
    # not something that should flip automatically just because
    # planned_finish has passed. A delayed project that overruns its
    # planned completion date must NOT silently show as "Completed" - it
    # should show "In Progress" with an overdue flag, since that overrun is
    # very often exactly what a FIDIC claim on this platform is about.
    status: Mapped[str] = mapped_column(
        String(50),
        default="Planning",
    )

    # FIDIC 2017 Sub-Clause 20.2 default periods. These are contract
    # defaults, not law - Particular Conditions (and the MDB Harmonised
    # Edition commonly used on ADB/World Bank-funded work in Cambodia)
    # frequently amend them, so they live per-project rather than as a
    # hardcoded constant.
    notice_period_days: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        server_default="28",
    )

    detailed_claim_period_days: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        server_default="84",
    )

    engineer_late_notice_flag_days: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        server_default="14",
    )

    engineer_response_period_days: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        server_default="42",
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