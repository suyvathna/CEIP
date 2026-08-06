"""
Engine A - the "ALWAYS DO" scheduler.

Turns app.constants.compliance_rules into a live register of dated
obligations per project, keeps their statuses honest, and raises alerts
before deadlines rather than after them.

Three properties this is built around:

1. Idempotent. Every obligation is keyed on
   (project_id, rule_key, period_key) and every alert on a dedupe key,
   so the tick can run once a day, five times a day, or twice at the same
   instant from two uvicorn workers, and the result is identical. That is
   what makes it safe to also expose as POST /compliance/tick and to fire
   on application startup.

2. No baked deadlines. due_date is recomputed from anchor + offset on
   every tick. Correct a project's Taking-Over date six weeks after the
   fact and the whole close-out register re-dates itself overnight,
   rather than leaving a Statement at Completion deadline that quietly
   still refers to the wrong milestone. This mirrors the rule
   claim_clock_service already follows for Sub-Clause 20.2.

3. Human decisions win. WAIVED and SUPERSEDED are never recomputed. If a
   PM says this contract has no advance payment, the sweep does not get
   to argue with them tomorrow morning.
"""

import logging
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from app.constants.compliance import (
    FROZEN_STATUSES,
    HUMAN_FROZEN_STATUSES,
    MACHINE_CLOSED_STATUSES,
    OPEN_STATUSES,
    SETTLED_STATUSES,
    MilestoneAnchor,
    ObligationCadence,
    ObligationStatus,
)
from app.constants.compliance_rules import (
    COMPLIANCE_RULES,
    RULES_BY_KEY,
    ObligationRule,
    month_periods,
    resolve_clause_code,
    resolve_offset_days,
)
from app.constants.notifications import (
    NotificationCategory,
    NotificationSeverity,
    severity_for_days_remaining,
)
from app.models.compliance_obligation import ComplianceObligation
from app.models.compliance_run import ComplianceRun
from app.models.evidence import Evidence
from app.models.project import Project
from app.services import notification_service
from app.services.claim_clock_service import config_from_project, get_today

logger = logging.getLogger(__name__)

# How far into the future monthly obligations are materialised. Three
# months is enough for a PM to plan around and short enough that a
# contract whose milestones later change doesn't leave a long tail of
# obligations to supersede.
DEFAULT_HORIZON_DAYS = 90

# Period key used by one-off rules, which have no calendar period.
ONE_OFF_PERIOD = "once"

# Arbitrary but fixed application-level lock id, so N API workers running
# the sweep at the same moment produce one run rather than N. "CEIP" in
# ASCII hex. Advisory locks are session-scoped and released explicitly
# below (and automatically if the connection dies), so a crashed worker
# cannot wedge the scheduler permanently.
ADVISORY_LOCK_KEY = 0x43454950


@dataclass(frozen=True)
class PlannedObligation:
    """One instance a rule says should exist, before it's been written."""

    rule: ObligationRule
    period_key: str
    anchor_date: date
    offset_days: int
    due_date: date
    period_start: date | None = None
    period_end: date | None = None


# ---------------------------------------------------------------------
# Planning: what SHOULD exist
# ---------------------------------------------------------------------

def _milestone_date(project: Project, anchor: MilestoneAnchor) -> date | None:
    if anchor == MilestoneAnchor.COMMENCEMENT:
        # Prefers the actual Sub-Clause 8.1 Commencement Date once it's
        # known; falls back to the originally planned date beforehand, so
        # the register isn't empty before actual commencement is
        # recorded and re-dates itself the moment it is.
        return getattr(project, "actual_commencement_date", None) or project.planned_start
    if anchor == MilestoneAnchor.LETTER_OF_ACCEPTANCE:
        # Falls back to nothing rather than to the Commencement Date: a
        # Performance Security deadline computed from the wrong milestone
        # is worse than an absent one, because it looks authoritative.
        return getattr(project, "letter_of_acceptance_date", None)
    if anchor == MilestoneAnchor.TAKING_OVER:
        return getattr(project, "taking_over_date", None)
    if anchor == MilestoneAnchor.PERFORMANCE_CERTIFICATE:
        # Computed rather than stored: taking_over_date + DNP + 28 days
        # (Sub-Clause 11.9), same formula as
        # ProjectResponse.performance_certificate_date. Falls back to
        # nothing if the Taking-Over Certificate hasn't been entered yet.
        taking_over = getattr(project, "taking_over_date", None)
        if taking_over is None:
            return None
        dnp_days = getattr(project, "defects_notification_period_days", None) or 0
        return taking_over + timedelta(days=dnp_days) + timedelta(days=28)

    return None


def _monthly_window(project: Project, today: date, horizon_days: int):
    """
    The span of calendar months the monthly rules should cover.

    Starts at the Commencement Date. Ends at the Taking-Over Certificate
    where one has been issued; otherwise it keeps running to the planned
    Completion Date, or to today if the works have already overrun it -
    an overrunning project still owes its monthly progress report, and a
    register that quietly stopped generating them on the planned finish
    date would be wrong in exactly the situation where the paperwork
    matters most.
    """
    start = project.planned_start
    if start is None:
        return None, None

    taking_over = getattr(project, "taking_over_date", None)
    works_end = taking_over or max(project.planned_finish, today)

    end = min(today + timedelta(days=horizon_days), works_end)

    if end < start:
        return None, None

    return start, end


def plan_obligations(
    project: Project,
    today: date,
    horizon_days: int = DEFAULT_HORIZON_DAYS,
) -> list[PlannedObligation]:
    """
    Pure function: given a project and a date, what obligations should
    exist? Touches no database, which makes the whole rule book testable
    without one.

    Rules anchored on PARENT_OBLIGATION are not planned here - their
    anchor is another obligation's actual submission date, which is a
    stored fact, so they are resolved in generate_obligations once the
    parents are on disk.
    """
    edition = getattr(project, "contract_edition", None)
    planned: list[PlannedObligation] = []

    monthly_start, monthly_end = _monthly_window(project, today, horizon_days)

    for rule in COMPLIANCE_RULES:
        if rule.anchor == MilestoneAnchor.PARENT_OBLIGATION:
            continue

        offset = resolve_offset_days(rule, project)

        if rule.cadence == ObligationCadence.ONE_OFF:
            anchor = _milestone_date(project, rule.anchor)
            if anchor is None:
                # The milestone hasn't happened yet. Skip silently rather
                # than guessing a date.
                continue

            planned.append(
                PlannedObligation(
                    rule=rule,
                    period_key=ONE_OFF_PERIOD,
                    anchor_date=anchor,
                    offset_days=offset,
                    due_date=anchor + timedelta(days=offset),
                )
            )
            continue

        if rule.cadence == ObligationCadence.MONTHLY:
            if monthly_start is None:
                continue

            for period_key, period_start, period_end in month_periods(
                monthly_start, monthly_end
            ):
                planned.append(
                    PlannedObligation(
                        rule=rule,
                        period_key=period_key,
                        anchor_date=period_end,
                        offset_days=offset,
                        due_date=period_end + timedelta(days=offset),
                        period_start=period_start,
                        period_end=period_end,
                    )
                )

    # Deliberately unused for now, but resolved here so the clause code
    # snapshotted onto every row follows the project's edition.
    for item in planned:
        resolve_clause_code(item.rule, edition)

    return planned


# ---------------------------------------------------------------------
# Materialising: writing what should exist
# ---------------------------------------------------------------------

def _existing_index(db: Session, project_id: UUID) -> dict[tuple[str, str], ComplianceObligation]:
    rows = db.scalars(
        select(ComplianceObligation).where(
            ComplianceObligation.project_id == project_id
        )
    ).all()
    return {(row.rule_key, row.period_key): row for row in rows}


def generate_obligations(
    db: Session,
    project: Project,
    today: date | None = None,
    horizon_days: int = DEFAULT_HORIZON_DAYS,
) -> tuple[int, int]:
    """
    Materialise (and re-date) this project's register.

    Returns (created, updated). Does not commit - the caller owns the
    transaction, so a whole tick either lands or doesn't.
    """
    today = today or get_today()
    edition = getattr(project, "contract_edition", None)

    existing = _existing_index(db, project.id)
    created = 0
    updated = 0

    # --- Pass 1: everything anchored on a contract milestone ---------
    for item in plan_obligations(project, today, horizon_days):
        key = (item.rule.key, item.period_key)
        row = existing.get(key)

        if row is None:
            row = ComplianceObligation(
                project_id=project.id,
                rule_key=item.rule.key,
                period_key=item.period_key,
                clause_code=resolve_clause_code(item.rule, edition),
                title=item.rule.title,
                category=item.rule.category.value,
                owed_by=item.rule.owed_by.value,
                anchor_date=item.anchor_date,
                offset_days=item.offset_days,
                due_date=item.due_date,
                period_start=item.period_start,
                period_end=item.period_end,
                status=ObligationStatus.PENDING.value,
                rights_destroying=item.rule.rights_destroying,
                # Born overdue: this deadline passed before CEIP had ever
                # heard of the project. It belongs in the register, not in
                # the alert stream.
                is_historical=item.due_date < today,
            )
            db.add(row)
            existing[key] = row
            created += 1
            continue

        if row.status in HUMAN_FROZEN_STATUSES:
            # A waiver is a human decision about their own contract. The
            # sweep never overrules it.
            continue

        if row.status in MACHINE_CLOSED_STATUSES:
            # It's back in the plan, so the milestone that retired it has
            # moved back. Revive it.
            #
            # This is the fix for a one-way door: a mistyped Taking-Over
            # date used to retire every monthly obligation after it, and
            # correcting the typo did not bring them back, because
            # generation skipped superseded rows outright. The register
            # stayed permanently short and no amount of pressing Rebuild
            # helped.
            row.status = ObligationStatus.PENDING.value
            updated += 1

        # Re-date in place. This is the mechanism that makes a corrected
        # milestone propagate through the whole register.
        if (
            row.anchor_date != item.anchor_date
            or row.offset_days != item.offset_days
            or row.due_date != item.due_date
            or row.clause_code != resolve_clause_code(item.rule, edition)
        ):
            row.anchor_date = item.anchor_date
            row.offset_days = item.offset_days
            row.due_date = item.due_date
            row.clause_code = resolve_clause_code(item.rule, edition)
            # A milestone correction can move a deadline back into the
            # future, at which point it stops being history and becomes a
            # real task again.
            if row.is_historical and item.due_date >= today:
                row.is_historical = False
            updated += 1

    db.flush()

    # --- Pass 2: rules that run off another obligation ---------------
    # The Engineer's IPC (14.6) and the Employer's payment (14.7) run
    # from the date the Contractor's Statement (14.3) was actually
    # received - falling back to when it was due while it's outstanding,
    # so the register still shows a realistic payment date rather than
    # nothing at all.
    for rule in COMPLIANCE_RULES:
        if rule.anchor != MilestoneAnchor.PARENT_OBLIGATION or not rule.parent_key:
            continue

        offset = resolve_offset_days(rule, project)

        for (parent_key, period_key), parent in list(existing.items()):
            if parent_key != rule.parent_key:
                continue
            if parent.status in (
                ObligationStatus.WAIVED.value,
                ObligationStatus.SUPERSEDED.value,
            ):
                continue

            anchor = parent.submitted_date or parent.due_date
            due = anchor + timedelta(days=offset)

            key = (rule.key, period_key)
            row = existing.get(key)

            if row is None:
                row = ComplianceObligation(
                    project_id=project.id,
                    rule_key=rule.key,
                    period_key=period_key,
                    clause_code=resolve_clause_code(rule, edition),
                    title=rule.title,
                    category=rule.category.value,
                    owed_by=rule.owed_by.value,
                    anchor_date=anchor,
                    offset_days=offset,
                    due_date=due,
                    period_start=parent.period_start,
                    period_end=parent.period_end,
                    status=ObligationStatus.PENDING.value,
                    rights_destroying=rule.rights_destroying,
                    is_historical=due < today,
                )
                db.add(row)
                existing[key] = row
                created += 1
                continue

            if row.status in HUMAN_FROZEN_STATUSES:
                continue

            if row.status in MACHINE_CLOSED_STATUSES:
                row.status = ObligationStatus.PENDING.value
                updated += 1

            if row.anchor_date != anchor or row.due_date != due:
                row.anchor_date = anchor
                row.offset_days = offset
                row.due_date = due
                if row.is_historical and due >= today:
                    row.is_historical = False
                updated += 1

    db.flush()

    # --- Pass 3: supersede instances that no longer correspond -------
    # A Taking-Over Certificate entered today retires the monthly
    # obligations for months after it. They're marked SUPERSEDED rather
    # than deleted: the register is an audit trail, and rows vanishing
    # from it is exactly the behaviour that makes an audit trail
    # worthless.
    taking_over = getattr(project, "taking_over_date", None)
    if taking_over is not None:
        for row in existing.values():
            rule = RULES_BY_KEY.get(row.rule_key)
            if rule is None or rule.cadence != ObligationCadence.MONTHLY:
                continue
            if row.status not in OPEN_STATUSES:
                continue
            if row.period_start is not None and row.period_start > taking_over:
                row.status = ObligationStatus.SUPERSEDED.value
                updated += 1

    db.flush()
    return created, updated


# ---------------------------------------------------------------------
# Status
# ---------------------------------------------------------------------

def compute_status(
    obligation: ComplianceObligation, today: date, lead_days: int
) -> str:
    """
    The only place an obligation's status is decided.

    Note the deliberate split between SUBMITTED and SUBMITTED_LATE, the
    same distinction claim_clock_service draws between "met" and
    "missed": recording a late submission honestly is not the same as
    curing it, and a register that flattened the two would let a project
    look fully compliant when it wasn't.
    """
    if obligation.status in FROZEN_STATUSES:
        return obligation.status

    if obligation.submitted_date is not None:
        return (
            ObligationStatus.SUBMITTED.value
            if obligation.submitted_date <= obligation.due_date
            else ObligationStatus.SUBMITTED_LATE.value
        )

    days_remaining = (obligation.due_date - today).days

    if days_remaining < 0:
        return ObligationStatus.OVERDUE.value
    if days_remaining <= lead_days:
        return ObligationStatus.DUE_SOON.value

    return ObligationStatus.PENDING.value


def refresh_statuses(db: Session, project: Project, today: date | None = None) -> int:
    today = today or get_today()
    lead_days = config_from_project(project).alert_lead_days

    rows = db.scalars(
        select(ComplianceObligation).where(
            ComplianceObligation.project_id == project.id
        )
    ).all()

    changed = 0
    for row in rows:
        new_status = compute_status(row, today, lead_days)
        if new_status != row.status:
            row.status = new_status
            changed += 1

    db.flush()
    return changed


# ---------------------------------------------------------------------
# Alerting
# ---------------------------------------------------------------------

def _obligation_link(project_id: UUID, obligation_id: UUID | None = None) -> str:
    base = f"/projects/{project_id}/compliance"
    # Points the register straight at the row the alert was about - see
    # CompliancePage's scroll-to-and-flash handling of ?highlight=. Left
    # off for the historical-backlog summary alert below, which is about
    # many rows at once, not one.
    return f"{base}?highlight={obligation_id}" if obligation_id else base


def alert_obligations(
    db: Session, project: Project, today: date | None = None
) -> int:
    """
    Raise an alert for every open obligation inside the project's lead
    window (or already overdue). Deduplication and escalation are handled
    entirely by notification_service's dedupe key - see its docstring.
    """
    today = today or get_today()
    lead_days = config_from_project(project).alert_lead_days

    rows = db.scalars(
        select(ComplianceObligation).where(
            ComplianceObligation.project_id == project.id,
            ComplianceObligation.status.in_(tuple(OPEN_STATUSES)),
            ComplianceObligation.due_date <= today + timedelta(days=lead_days),
            # History does not alert. See ComplianceObligation.is_historical
            # and _alert_historical_backlog below.
            ComplianceObligation.is_historical.is_(False),
        )
    ).all()

    raised = _alert_historical_backlog(db, project, today)

    for row in rows:
        days_remaining = (row.due_date - today).days
        severity = severity_for_days_remaining(
            days_remaining,
            lead_days,
            rights_destroying=row.rights_destroying,
        )

        rule = RULES_BY_KEY.get(row.rule_key)
        period_label = f" ({row.period_key})" if row.period_key != ONE_OFF_PERIOD else ""

        if days_remaining < 0:
            when = f"was due {abs(days_remaining)} day(s) ago"
        elif days_remaining == 0:
            when = "is due today"
        else:
            when = f"is due in {days_remaining} day(s)"

        if row.owed_by != "Contractor":
            body = (
                f"{row.clause_code}: the {row.owed_by}'s obligation "
                f"\"{row.title}\"{period_label} {when} "
                f"({row.due_date.isoformat()}). A missed deadline here is "
                f"itself a claim ground - log an Event rather than only "
                f"chasing it informally."
            )
        else:
            body = (
                f"{row.clause_code}: \"{row.title}\"{period_label} {when} "
                f"({row.due_date.isoformat()})."
            )
            if rule is not None and rule.rights_destroying:
                body += " Missing this deadline forfeits an entitlement outright."

        if notification_service.emit(
            db,
            project_id=project.id,
            category=NotificationCategory.COMPLIANCE,
            severity=severity,
            title=f"{row.clause_code} - {row.title}{period_label}",
            body=body,
            clause_code=row.clause_code,
            source_type="obligation",
            source_id=row.id,
            stage="due",
            link_path=_obligation_link(project.id, row.id),
            due_date=row.due_date,
            days_remaining=days_remaining,
            dedupe_key=notification_service.build_dedupe_key(
                "obligation", row.id, "due", severity.value, row.due_date
            ),
        ):
            raised += 1

    return raised


def _alert_historical_backlog(
    db: Session, project: Project, today: date
) -> int:
    """
    One alert for the whole pre-CEIP backlog, instead of one per item.

    Onboarding a job that has already been running for months
    back-generates its register - correctly, because those obligations
    really did fall due. Alerting on each of them individually is what
    produced twenty-four CRITICAL notices on day one about progress
    reports that were late in March, none of which anyone could act on,
    and all of which buried the three things that were still live.

    So the backlog gets a single line stating the count and pointing at
    the register. The dedupe key carries the count, so it re-raises as
    the PM works through them and disappears when it reaches zero.
    """
    outstanding = db.scalar(
        select(func.count(ComplianceObligation.id)).where(
            ComplianceObligation.project_id == project.id,
            ComplianceObligation.is_historical.is_(True),
            ComplianceObligation.status.in_(tuple(OPEN_STATUSES)),
        )
    ) or 0

    if outstanding == 0:
        notification_service.resolve_source(
            db,
            source_type="project_backlog",
            source_id=project.id,
            reason="Backlog cleared",
        )
        return 0

    raised = notification_service.emit(
        db,
        project_id=project.id,
        category=NotificationCategory.COMPLIANCE,
        # Never CRITICAL. By definition none of this can still be saved,
        # and shouting about it is what made the real time-bars invisible.
        severity=NotificationSeverity.WARNING,
        title=f"{outstanding} obligation(s) fell due before this project was added",
        body=(
            f"These deadlines passed before CEIP was tracking this "
            f"contract, so they are recorded as history rather than "
            f"alerted individually. Open the Compliance tab to record "
            f"what was actually submitted, or waive the ones that never "
            f"applied - the register is only trustworthy once this "
            f"backlog has been dealt with."
        ),
        source_type="project_backlog",
        source_id=project.id,
        stage="historical_backlog",
        link_path=_obligation_link(project.id),
        dedupe_key=notification_service.build_dedupe_key(
            "project_backlog", project.id, "historical_backlog", str(outstanding)
        ),
    )

    return 1 if raised else 0


def resolve_settled_alerts(
    db: Session, project: Project, today: date | None = None
) -> int:
    """
    Retire alerts about obligations that are no longer outstanding -
    submitted, waived, superseded, or simply re-dated far enough out that
    they've left the alert window.

    Without this the alert stream is write-only. A PM who submits every
    report they owe still sees the same badge count they saw before, which
    is indistinguishable from having done nothing, and within a week
    nobody looks at the bell at all.
    """
    today = today or get_today()
    lead_days = config_from_project(project).alert_lead_days

    rows = db.scalars(
        select(ComplianceObligation).where(
            ComplianceObligation.project_id == project.id
        )
    ).all()

    resolved = 0

    for row in rows:
        if row.status in SETTLED_STATUSES:
            reason = {
                ObligationStatus.SUBMITTED.value: "Submitted on time",
                ObligationStatus.SUBMITTED_LATE.value: "Submitted (late)",
                ObligationStatus.WAIVED.value: "Waived - not applicable to this contract",
                ObligationStatus.SUPERSEDED.value: "Superseded by a milestone change",
            }.get(row.status, "No longer outstanding")

        elif (row.due_date - today).days > lead_days:
            # Re-dated out of the alert window - e.g. a milestone was
            # corrected and this is no longer imminent. The old alert
            # would otherwise sit there quoting a date that has moved.
            reason = "Deadline moved - no longer inside the alert window"

        else:
            continue

        resolved += notification_service.resolve_source(
            db, source_type="obligation", source_id=row.id, reason=reason
        )

    return resolved


# ---------------------------------------------------------------------
# The tick
# ---------------------------------------------------------------------

def _try_advisory_lock(db: Session) -> bool:
    return bool(
        db.execute(
            text("SELECT pg_try_advisory_lock(:key)"), {"key": ADVISORY_LOCK_KEY}
        ).scalar()
    )


def _release_advisory_lock(db: Session) -> None:
    db.execute(text("SELECT pg_advisory_unlock(:key)"), {"key": ADVISORY_LOCK_KEY})


def run_daily_tick(
    db: Session,
    *,
    today: date | None = None,
    trigger_source: str = "scheduled",
    horizon_days: int = DEFAULT_HORIZON_DAYS,
) -> ComplianceRun | None:
    """
    The whole sweep: regenerate every project's register, refresh
    statuses, alert on what's close, then hand over to Engine B for the
    event-driven clocks.

    Returns None if another worker already holds the lock - that is a
    normal outcome on a multi-worker deployment, not an error.
    """
    if not _try_advisory_lock(db):
        logger.info("Compliance tick skipped: another worker holds the lock.")
        return None

    today = today or get_today()

    run = ComplianceRun(
        run_date=today,
        trigger_source=trigger_source,
        status="running",
    )
    db.add(run)
    db.flush()

    try:
        projects = list(db.scalars(select(Project)).all())

        created = updated = alerts = resolved = 0

        for project in projects:
            c, u = generate_obligations(db, project, today, horizon_days)
            created += c
            updated += u
            updated += refresh_statuses(db, project, today)
            alerts += alert_obligations(db, project, today)
            # Order matters: resolve AFTER alerting, so an obligation that
            # is still open and still imminent keeps the alert that
            # alert_obligations just (re-)raised for it.
            resolved += resolve_settled_alerts(db, project, today)

        # Engine B's own sweep: claim time-bars, 3.7 NOD windows, 3.5
        # instruction notices. Imported here rather than at module level
        # so the two engines stay independently importable (Engine B must
        # not need Engine A to fire a trigger from an API request).
        from app.services.contract_engine import run_daily_sweep

        b_alerts, b_resolved = run_daily_sweep(db, today=today)
        alerts += b_alerts
        resolved += b_resolved

        run.projects_processed = len(projects)
        run.obligations_created = created
        run.obligations_updated = updated
        run.notifications_created = alerts
        run.notifications_resolved = resolved
        run.status = "completed"
        run.finished_at = datetime.now(timezone.utc)

        db.commit()
        return run

    except Exception as exc:  # noqa: BLE001 - the run ledger records it
        db.rollback()
        logger.exception("Compliance tick failed")

        # Re-record the failure on a clean transaction: a run that
        # crashed and left no trace is the one case this table exists to
        # prevent.
        failed = ComplianceRun(
            run_date=today,
            trigger_source=trigger_source,
            status="failed",
            error=str(exc)[:2000],
            finished_at=datetime.now(timezone.utc),
        )
        db.add(failed)
        db.commit()
        return failed

    finally:
        _release_advisory_lock(db)


# ---------------------------------------------------------------------
# Read / write API used by the routes
# ---------------------------------------------------------------------

def get_register(
    db: Session,
    project_id: UUID,
    *,
    status: str | None = None,
    category: str | None = None,
    include_closed: bool = True,
) -> list[ComplianceObligation]:
    stmt = select(ComplianceObligation).where(
        ComplianceObligation.project_id == project_id
    )

    if status:
        stmt = stmt.where(ComplianceObligation.status == status)

    if category:
        stmt = stmt.where(ComplianceObligation.category == category)

    if not include_closed:
        stmt = stmt.where(ComplianceObligation.status.in_(tuple(OPEN_STATUSES)))

    return list(db.scalars(stmt.order_by(ComplianceObligation.due_date)).all())


def get_register_summary(db: Session, project_id: UUID) -> dict:
    rows = db.execute(
        select(ComplianceObligation.status, func.count(ComplianceObligation.id))
        .where(ComplianceObligation.project_id == project_id)
        .group_by(ComplianceObligation.status)
    ).all()

    by_status = dict(rows)
    open_count = sum(by_status.get(s, 0) for s in OPEN_STATUSES)

    # Open obligations that fell due before CEIP saw this project. Broken
    # out because "18 open" reads very differently once you know 15 of
    # them are pre-onboarding history rather than work in flight.
    historical_open = db.scalar(
        select(func.count(ComplianceObligation.id)).where(
            ComplianceObligation.project_id == project_id,
            ComplianceObligation.is_historical.is_(True),
            ComplianceObligation.status.in_(tuple(OPEN_STATUSES)),
        )
    ) or 0

    return {
        "total": sum(by_status.values()),
        "open": open_count,
        "historical_open": historical_open,
        "live_open": open_count - historical_open,
        "pending": by_status.get(ObligationStatus.PENDING.value, 0),
        "due_soon": by_status.get(ObligationStatus.DUE_SOON.value, 0),
        "overdue": by_status.get(ObligationStatus.OVERDUE.value, 0),
        "submitted": by_status.get(ObligationStatus.SUBMITTED.value, 0),
        "submitted_late": by_status.get(ObligationStatus.SUBMITTED_LATE.value, 0),
        "waived": by_status.get(ObligationStatus.WAIVED.value, 0),
        "superseded": by_status.get(ObligationStatus.SUPERSEDED.value, 0),
    }


def get_obligation(db: Session, obligation_id: UUID) -> ComplianceObligation | None:
    return db.get(ComplianceObligation, obligation_id)


def mark_submitted(
    db: Session,
    obligation_id: UUID,
    *,
    submitted_date: date,
    submitted_reference: str | None = None,
    evidence_id: UUID | None = None,
    notes: str | None = None,
) -> ComplianceObligation | None:
    obligation = db.get(ComplianceObligation, obligation_id)
    if obligation is None:
        return None

    obligation.submitted_date = submitted_date
    obligation.submitted_reference = submitted_reference
    obligation.notes = notes

    if evidence_id is not None:
        obligation.evidence_id = evidence_id
        evidence = db.get(Evidence, evidence_id)
        if evidence is not None:
            # Same rule the platform already applies to a Notice of
            # Claim's evidence: once a document is the proof that a
            # contractual deadline was met, it stops being deletable.
            evidence.is_locked = True

    project = db.get(Project, obligation.project_id)
    lead_days = config_from_project(project).alert_lead_days
    obligation.status = compute_status(obligation, get_today(), lead_days)

    # Retire the alert immediately rather than at 06:00 tomorrow - a PM
    # who has just recorded the submission should watch the badge drop.
    notification_service.resolve_source(
        db,
        source_type="obligation",
        source_id=obligation.id,
        reason=(
            "Submitted on time"
            if obligation.status == ObligationStatus.SUBMITTED.value
            else "Submitted (late)"
        ),
    )

    db.commit()
    db.refresh(obligation)
    return obligation


def waive(
    db: Session,
    obligation_id: UUID,
    reason: str,
    *,
    evidence_id: UUID | None = None,
) -> ComplianceObligation | None:
    """
    Mark a rule as not applying to this contract. Survives every
    subsequent tick - the sweep is not allowed to overrule a human on
    whether their own contract contains an advance payment.
    """
    obligation = db.get(ComplianceObligation, obligation_id)
    if obligation is None:
        return None

    obligation.status = ObligationStatus.WAIVED.value
    obligation.waived_reason = reason

    if evidence_id is not None:
        obligation.evidence_id = evidence_id
        evidence = db.get(Evidence, evidence_id)
        if evidence is not None:
            # Same rule mark_submitted already applies: once a document is
            # the basis for a register decision, it stops being deletable.
            evidence.is_locked = True

    notification_service.resolve_source(
        db,
        source_type="obligation",
        source_id=obligation.id,
        reason="Waived - not applicable to this contract",
    )

    db.commit()
    db.refresh(obligation)
    return obligation


def reopen(db: Session, obligation_id: UUID) -> ComplianceObligation | None:
    """Undo a waiver, or clear a recorded submission that was entered in
    error, and let the next tick decide the status again."""
    obligation = db.get(ComplianceObligation, obligation_id)
    if obligation is None:
        return None

    obligation.status = ObligationStatus.PENDING.value
    obligation.waived_reason = None
    obligation.submitted_date = None
    obligation.submitted_reference = None

    project = db.get(Project, obligation.project_id)
    lead_days = config_from_project(project).alert_lead_days
    obligation.status = compute_status(obligation, get_today(), lead_days)

    db.commit()
    db.refresh(obligation)
    return obligation


def regenerate_for_project(
    db: Session, project_id: UUID, today: date | None = None
) -> dict:
    """
    Force a single project's register to rebuild - what the API calls
    after a milestone changes, so the PM sees the new dates immediately
    instead of tomorrow morning.
    """
    project = db.get(Project, project_id)
    if project is None:
        return {"created": 0, "updated": 0, "alerts": 0}

    today = today or get_today()

    created, updated = generate_obligations(db, project, today)
    updated += refresh_statuses(db, project, today)
    alerts = alert_obligations(db, project, today)
    resolved = resolve_settled_alerts(db, project, today)

    db.commit()

    return {
        "created": created,
        "updated": updated,
        "alerts": alerts,
        "resolved": resolved,
    }


def get_recent_runs(db: Session, limit: int = 20) -> list[ComplianceRun]:
    return list(
        db.scalars(
            select(ComplianceRun)
            .order_by(ComplianceRun.started_at.desc())
            .limit(limit)
        ).all()
    )
