"""
The one place anything in the platform is allowed to raise an alert.

Both engines write here and nothing else does, which is what lets the
bell menu answer a single question honestly: what is about to hurt me,
worst first.

The design problem this service solves is alert fatigue. A daily sweep
that re-announces the same deadline every morning gets muted inside a
week, and a muted alert stream is worse than none - it makes everyone
believe they're covered. So every alert carries a dedupe_key built from
what it is about plus how urgent it has become, and emit() is a no-op
when that key already exists. Re-running the tick five times on the same
day produces one alert. A deadline crossing from "10 days out" to "2
days out" produces a genuinely new one, because the key changed with the
severity. Escalation therefore needs no timers, no per-alert state and no
cleanup job - it falls out of the key.
"""

from datetime import date, datetime, timezone
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from app.constants.notifications import (
    ENGINE_BY_CATEGORY,
    SEVERITY_RANK,
    Engine,
    NotificationCategory,
    NotificationSeverity,
)
from app.models.notification import Notification


def build_dedupe_key(
    source_type: str,
    source_id: UUID | str | None,
    stage: str,
    severity: str,
    deadline: date | None = None,
) -> str:
    """
    Stable identity for "this alert, about this deadline, at this
    urgency".

    Severity is part of the key on purpose - see the module docstring.
    Stage is in there too so a claim that is simultaneously overdue on
    its notice and approaching its detailed-claim deadline can raise both
    rather than one silently swallowing the other.

    The deadline joined later, and it fixes a real bug. Without it, a
    milestone correction that re-dated an obligation raised no new alert
    (same source, same stage, same severity), so the PM was left staring
    at an alert quoting the OLD date with no indication anything had
    changed. With the deadline in the key, re-dating always raises a
    fresh alert - and emit() retires the superseded one, so there is
    still only ever a single live alert per stage.
    """
    suffix = f":{deadline.isoformat()}" if deadline is not None else ""
    return f"{source_type}:{source_id}:{stage}:{severity}{suffix}"


def emit(
    db: Session,
    *,
    project_id: UUID,
    category: NotificationCategory | str,
    severity: NotificationSeverity | str,
    title: str,
    dedupe_key: str,
    body: str | None = None,
    clause_code: str | None = None,
    source_type: str = "system",
    source_id: UUID | None = None,
    stage: str | None = None,
    link_path: str | None = None,
    due_date: date | None = None,
    days_remaining: int | None = None,
    user_id: UUID | None = None,
    commit: bool = False,
) -> bool:
    """
    Raise an alert unless one with the same dedupe_key already exists,
    and retire any earlier live alert about the same (source, stage).

    Returns True if a row was actually inserted.

    That second half is what keeps the stream honest. At most one alert
    per deadline is ever live: when a deadline escalates from WARNING to
    CRITICAL, or moves because a milestone was corrected, the new alert
    replaces the old one instead of stacking on top of it. Without that,
    a single obligation could accumulate half a dozen contradictory
    alerts quoting different dates, and the badge count became a measure
    of how long the system had been running rather than of how much work
    was outstanding.

    Uses ON CONFLICT DO NOTHING rather than a SELECT-then-INSERT because
    the tick can legitimately run concurrently with a user action that
    raises the same alert (submitting a claim notice while the sweep is
    mid-flight, say). A check-then-insert would raise IntegrityError and
    abort the surrounding transaction - taking the whole sweep down over
    a duplicate alert, which is the least important thing in it.
    """
    stmt = (
        pg_insert(Notification)
        .values(
            project_id=project_id,
            user_id=user_id,
            stage=stage,
            category=(
                category.value
                if isinstance(category, NotificationCategory)
                else category
            ),
            severity=(
                severity.value
                if isinstance(severity, NotificationSeverity)
                else severity
            ),
            title=title,
            body=body,
            clause_code=clause_code,
            source_type=source_type,
            source_id=source_id,
            link_path=link_path,
            due_date=due_date,
            days_remaining=days_remaining,
            dedupe_key=dedupe_key,
        )
        .on_conflict_do_nothing(index_elements=["dedupe_key"])
        .returning(Notification.id)
    )

    inserted = db.execute(stmt).scalar_one_or_none()

    if inserted is not None and source_id is not None and stage is not None:
        # Retire the previous live alert about this same deadline. Done
        # only on a genuine insert, so a deduplicated re-run doesn't
        # churn anything.
        _resolve(
            db,
            source_type=source_type,
            source_id=source_id,
            stage=stage,
            reason="Superseded by a newer alert",
            exclude_id=inserted,
        )

    if commit:
        db.commit()

    return inserted is not None


def _resolve(
    db: Session,
    *,
    source_type: str,
    source_id: UUID,
    stage: str | None = None,
    reason: str,
    exclude_id: UUID | None = None,
) -> int:
    stmt = select(Notification).where(
        Notification.source_type == source_type,
        Notification.source_id == source_id,
        Notification.is_resolved.is_(False),
    )

    if stage is not None:
        stmt = stmt.where(Notification.stage == stage)

    if exclude_id is not None:
        stmt = stmt.where(Notification.id != exclude_id)

    rows = list(db.scalars(stmt).all())
    now = datetime.now(timezone.utc)

    for row in rows:
        row.is_resolved = True
        row.resolved_at = now
        row.resolved_reason = reason[:255]

    return len(rows)


def resolve_source(
    db: Session,
    *,
    source_type: str,
    source_id: UUID,
    stage: str | None = None,
    reason: str = "No longer outstanding",
    commit: bool = False,
) -> int:
    """
    Retire every live alert about a record (or about one stage of it)
    because the thing it was warning about is done.

    Called the moment a user does the thing - records a submission,
    waives an obligation, gives a Notice - as well as from the daily
    sweep, so the badge drops immediately rather than at 06:00 tomorrow.
    Alerts are never deleted: a resolved alert stays in the history as
    evidence the system warned in time and the warning was acted on.
    """
    count = _resolve(
        db,
        source_type=source_type,
        source_id=source_id,
        stage=stage,
        reason=reason,
    )

    if commit:
        db.commit()

    return count


def revive_source(
    db: Session,
    *,
    source_type: str,
    source_id: UUID,
    stage: str | None = None,
    commit: bool = False,
) -> int:
    """
    The undo for resolve_source: bring back every alert that was retired
    about a record (or one stage of it) because a human is now saying the
    thing it warned about isn't actually done after all - see
    compliance_service.reopen(). Alerts are never deleted, so this is
    exact: the row that comes back is the one that existed, with the same
    title/body/severity it had, not a freshly-composed one.
    """
    stmt = select(Notification).where(
        Notification.source_type == source_type,
        Notification.source_id == source_id,
        Notification.is_resolved.is_(True),
    )

    if stage is not None:
        stmt = stmt.where(Notification.stage == stage)

    rows = list(db.scalars(stmt).all())

    for row in rows:
        row.is_resolved = False
        row.resolved_at = None
        row.resolved_reason = None

    if commit:
        db.commit()

    return len(rows)


def list_notifications(
    db: Session,
    *,
    project_id: UUID | None = None,
    unread_only: bool = False,
    category: str | None = None,
    engine: str | None = None,
    include_resolved: bool = False,
    limit: int = 50,
):
    """
    Live alerts, worst first then newest. A PM opening the bell menu on a
    bad morning should see the Notice of Dissatisfaction that expires
    tomorrow above the progress report that's due next week, regardless
    of which was raised more recently.

    Resolved alerts are excluded by default. They are still there - pass
    include_resolved=True to read the history, which is what shows that
    the system warned in time and the warning was acted on.
    """
    stmt = select(Notification)

    if project_id is not None:
        stmt = stmt.where(Notification.project_id == project_id)

    if not include_resolved:
        stmt = stmt.where(Notification.is_resolved.is_(False))

    if unread_only:
        stmt = stmt.where(Notification.is_read.is_(False))

    if category is not None:
        stmt = stmt.where(Notification.category == category)

    if engine is not None:
        wanted = [c for c, e in ENGINE_BY_CATEGORY.items() if e == engine]
        stmt = stmt.where(Notification.category.in_(wanted or ["__none__"]))

    rows = list(db.scalars(stmt.order_by(Notification.created_at.desc())).all())

    rows.sort(
        key=lambda n: (
            SEVERITY_RANK.get(n.severity, 99),
            -(n.created_at.timestamp() if n.created_at else 0),
        )
    )

    return rows[:limit]


def unread_count(db: Session, *, project_id: UUID | None = None) -> int:
    stmt = select(func.count(Notification.id)).where(
        Notification.is_resolved.is_(False),
    )

    if project_id is not None:
        stmt = stmt.where(Notification.project_id == project_id)

    return db.scalar(stmt) or 0


def unread_summary(db: Session, *, project_id: UUID | None = None) -> dict:
    """
    Counts for the bell badge: total, how many are critical, and how they
    split across the two engines.

    Counts LIVE alerts, not every alert ever raised. That is the whole
    point of resolution - a PM who has done everything asked of them must
    see zero, because a badge that only ever climbs is indistinguishable
    from a badge nobody is acting on.

    Deliberately NOT filtered by is_read. Opening the bell (or clicking
    through to look at something) is a human saying "I've seen this",
    not "this is handled" - an alert a PM viewed but didn't act on has to
    keep counting, or the badge stops meaning anything the moment
    someone glances at it. Only mark_submitted/waive/resolve_settled_alerts
    (i.e. actually recording, waiving, or fixing the underlying thing)
    should ever make this number drop.
    """
    base = [Notification.is_resolved.is_(False)]

    if project_id is not None:
        base.append(Notification.project_id == project_id)

    by_severity = dict(
        db.execute(
            select(Notification.severity, func.count(Notification.id))
            .where(*base)
            .group_by(Notification.severity)
        ).all()
    )

    by_category = dict(
        db.execute(
            select(Notification.category, func.count(Notification.id))
            .where(*base)
            .group_by(Notification.category)
        ).all()
    )

    engine_a = sum(
        count
        for category, count in by_category.items()
        if ENGINE_BY_CATEGORY.get(category) == Engine.A.value
    )

    return {
        "total": sum(by_severity.values()),
        "critical": by_severity.get(NotificationSeverity.CRITICAL.value, 0),
        "warning": by_severity.get(NotificationSeverity.WARNING.value, 0),
        "info": by_severity.get(NotificationSeverity.INFO.value, 0),
        "engine_a": engine_a,
        "engine_b": sum(by_severity.values()) - engine_a,
    }


def mark_read(db: Session, notification_id: UUID) -> Notification | None:
    notification = db.get(Notification, notification_id)

    if notification is None:
        return None

    if not notification.is_read:
        notification.is_read = True
        notification.read_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(notification)

    return notification


def mark_all_read(db: Session, *, project_id: UUID | None = None) -> int:
    stmt = select(Notification).where(
        Notification.is_read.is_(False),
        Notification.is_resolved.is_(False),
    )

    if project_id is not None:
        stmt = stmt.where(Notification.project_id == project_id)

    now = datetime.now(timezone.utc)
    rows = list(db.scalars(stmt).all())

    for notification in rows:
        notification.is_read = True
        notification.read_at = now

    db.commit()
    return len(rows)
