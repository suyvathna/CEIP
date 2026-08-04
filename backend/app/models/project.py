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

    # Which FIDIC edition this contract is actually signed under. Clause
    # numbers move between editions (Progress Reports are Sub-Clause 4.20
    # in 2017 but 4.21 in 1999; Engineer's Instructions 3.5 vs 3.3), and
    # this platform prints clause numbers straight into Notices - citing
    # the wrong one is exactly the sort of small error an Engineer will
    # use to argue about a notice. See app.constants.contract_edition.
    contract_edition: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        server_default="FIDIC 2017",
    )

    # --- Contract milestones (Engine A anchors) ----------------------
    # Every one of these is nullable because it may genuinely not have
    # happened yet. Engine A silently skips any obligation anchored on a
    # milestone with no date rather than inventing one - a Statement at
    # Completion deadline computed from a guessed Taking-Over date would
    # be worse than no deadline at all.

    # Contract Data: starts the 28-day clocks for the Performance
    # Security (Sub-Clause 4.2) and the Advance Payment guarantee (14.2).
    letter_of_acceptance_date: Mapped[date | None] = mapped_column(Date)

    # Sub-Clause 10.1 Taking-Over Certificate. Starts the 84-day Statement
    # at Completion clock (14.10) and the Defects Notification Period.
    taking_over_date: Mapped[date | None] = mapped_column(Date)

    # Sub-Clause 11.9. Starts the 56-day Final Statement clock (14.11) -
    # the last door in the contract.
    performance_certificate_date: Mapped[date | None] = mapped_column(Date)

    defects_notification_period_days: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        server_default="365",
    )

    # --- Engine A submission periods ---------------------------------
    # Days after the last day of the reporting period. FIDIC fixes 7 for
    # progress reports; it fixes nothing at all for the monthly Statement
    # (14.3 just says "after the end of each month"), so that one really
    # does have to be set per contract.
    progress_report_due_days: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        server_default="7",
    )

    statement_due_days: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        server_default="7",
    )

    # --- Engine B periods (Sub-Clause 3.7 / 3.5 / 13.3) --------------
    # engineer_response_period_days above doubles as the 3.7.3 time limit
    # for AGREEMENT (20.2.5 sends the Engineer to 3.7 with the same 42
    # days), so it is deliberately not duplicated here. This is the
    # FURTHER period the Engineer then has to make a determination.
    engineer_determination_period_days: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        server_default="42",
    )

    # Sub-Clause 3.7.5: 28 days from RECEIPT of the determination to give
    # a Notice of Dissatisfaction. Miss it and the determination is final
    # and binding, with no appeal - the single most expensive deadline in
    # the contract.
    nod_period_days: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        server_default="28",
    )

    # Sub-Clause 3.5 says the Notice must be given "immediately, and
    # before commencing any work". "Immediately" is not a number, and a
    # platform cannot alert on a word - so this is the practical working
    # window the register uses to raise the alarm. It is NOT a contractual
    # grace period, and the UI says so: the real deadline is before work
    # starts, whenever that is.
    deemed_variation_notice_days: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        server_default="7",
    )

    # Sub-Clause 13.3.1: the Contractor responds to a Variation
    # instruction (or a request for proposal) within the period stated,
    # commonly 28 days.
    variation_proposal_period_days: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        server_default="28",
    )

    # How many days ahead of a deadline the engines start alerting.
    compliance_alert_lead_days: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        server_default="7",
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