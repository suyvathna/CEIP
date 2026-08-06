from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models.daily_log import DailyLog, DailyLogEventLink
from app.services.evidence_service import search_evidence
from app.models.daily_log_entries import (
    DeliveryEntry,
    EquipmentEntry,
    HSEEntry,
    InspectionEntry,
    ManpowerEntry,
    VisitorEntry,
    WeatherObservation,
)
from app.models.event import Event
from app.models.evidence import Evidence
from app.schemas.daily_log import DailyLogCreate

# Every child-table relationship, keyed by the field name on
# DailyLogCreate/DailyLogResponse that carries it. Iterating this table
# (rather than repeating the same seven blocks seven times) is what keeps
# create/update/hydrate from drifting out of sync as sections get added.
_CHILD_TABLES = {
    "weather_observations": WeatherObservation,
    "manpower_entries": ManpowerEntry,
    "equipment_entries": EquipmentEntry,
    "delivery_entries": DeliveryEntry,
    "inspection_entries": InspectionEntry,
    "hse_entries": HSEEntry,
    "visitor_entries": VisitorEntry,
}


def _linked_event_ids(db: Session, daily_log_id: UUID) -> list[UUID]:
    stmt = select(DailyLogEventLink.event_id).where(
        DailyLogEventLink.daily_log_id == daily_log_id
    )
    return list(db.scalars(stmt).all())


def _child_rows(db: Session, daily_log_id: UUID, model) -> list:
    stmt = select(model).where(model.daily_log_id == daily_log_id)
    return list(db.scalars(stmt).all())


def _hydrate(db: Session, daily_log: DailyLog) -> DailyLog:
    daily_log.linked_event_ids = _linked_event_ids(db, daily_log.id)

    for field, model in _CHILD_TABLES.items():
        setattr(daily_log, field, _child_rows(db, daily_log.id, model))

    daily_log.total_workers = sum(
        row.workers_count or 0 for row in daily_log.manpower_entries
    )
    daily_log.total_man_hours = sum(
        (row.workers_count or 0) * float(row.hours or 0)
        for row in daily_log.manpower_entries
    )

    daily_log.photo_count = db.scalar(
        select(func.count(Evidence.id)).where(Evidence.daily_log_id == daily_log.id)
    ) or 0

    return daily_log


def _auto_link_same_day_events(db: Session, db_daily_log: DailyLog) -> None:
    """
    A log entry and an Event logged for the same project on the same
    calendar date are almost always describing the same working day, so
    they're linked automatically the moment either one is saved - no
    manual "attach this log to that event" step required. Skips
    db_daily_log's own primary event_id (already linked) and anything
    already linked via DailyLogEventLink.
    """
    same_day_event_ids = set(
        db.scalars(
            select(Event.id).where(
                Event.project_id == db_daily_log.project_id,
                Event.event_date == db_daily_log.diary_date,
            )
        ).all()
    )

    if db_daily_log.event_id:
        same_day_event_ids.discard(db_daily_log.event_id)

    if not same_day_event_ids:
        return

    already_linked = set(
        db.scalars(
            select(DailyLogEventLink.event_id).where(
                DailyLogEventLink.daily_log_id == db_daily_log.id
            )
        ).all()
    )

    for event_id in same_day_event_ids - already_linked:
        db.add(DailyLogEventLink(daily_log_id=db_daily_log.id, event_id=event_id))


def _replace_children(db: Session, daily_log_id: UUID, payload: dict) -> None:
    """
    Full replace-on-save for every structured child log (Observed Weather
    Conditions, Manpower, Equipment, Delivery, Inspection, HSE, Visitors) -
    the same semantics DailyLogEventLink already uses. A daily log is
    edited as one form/one save, not as independently-CRUD'd rows, so this
    keeps the service layer to one call site per section instead of eight
    near-duplicate add/remove endpoints. Mutates payload (pops each field).
    """
    for field, model in _CHILD_TABLES.items():
        rows = payload.pop(field, [])

        db.query(model).filter(model.daily_log_id == daily_log_id).delete()

        for row in rows:
            db.add(model(daily_log_id=daily_log_id, **row))


def create_daily_log(
    db: Session,
    daily_log: DailyLogCreate,
):
    payload = daily_log.model_dump()
    additional_event_ids = payload.pop("additional_event_ids", [])

    db_daily_log = DailyLog(
        **{k: v for k, v in payload.items() if k not in _CHILD_TABLES}
    )

    db.add(db_daily_log)
    db.flush()

    _replace_children(db, db_daily_log.id, payload)

    for event_id in additional_event_ids:
        db.add(DailyLogEventLink(daily_log_id=db_daily_log.id, event_id=event_id))

    _auto_link_same_day_events(db, db_daily_log)

    db.commit()
    db.refresh(db_daily_log)

    return _hydrate(db, db_daily_log)


def get_daily_logs(db: Session):
    statement = select(DailyLog).order_by(DailyLog.diary_date.desc())
    logs = db.scalars(statement).all()
    return [_hydrate(db, d) for d in logs]


def hydrate_daily_logs(db: Session, daily_logs) -> list[DailyLog]:
    """Public entry point for callers outside this module (e.g.
    claim_service, for the Claim -> linked Daily Logs list) that already
    have DailyLog rows from elsewhere and just need them hydrated the
    same way every other read path here does."""
    return [_hydrate(db, d) for d in daily_logs]


def get_logs_for_project(db: Session, project_id: UUID):
    statement = (
        select(DailyLog)
        .where(DailyLog.project_id == project_id)
        .order_by(DailyLog.diary_date.desc())
    )
    logs = db.scalars(statement).all()
    return [_hydrate(db, d) for d in logs]


def get_logs_for_event(db: Session, event_id: UUID):
    """
    A log now "belongs" to an event either as its primary event_id or via
    a DailyLogEventLink - both count as relevant here, since either way
    the log is contemporaneous evidence for that event.
    """
    primary_stmt = select(DailyLog).where(DailyLog.event_id == event_id)
    primary = list(db.scalars(primary_stmt).all())

    linked_ids_stmt = select(DailyLogEventLink.daily_log_id).where(
        DailyLogEventLink.event_id == event_id
    )
    linked_ids = set(db.scalars(linked_ids_stmt).all())
    primary_ids = {d.id for d in primary}

    extra = []
    remaining_ids = linked_ids - primary_ids
    if remaining_ids:
        extra_stmt = select(DailyLog).where(DailyLog.id.in_(remaining_ids))
        extra = list(db.scalars(extra_stmt).all())

    combined = primary + extra
    combined.sort(key=lambda d: d.diary_date, reverse=True)
    return [_hydrate(db, d) for d in combined]


def get_daily_log(db: Session, daily_log_id: UUID):
    daily_log = db.get(DailyLog, daily_log_id)
    return _hydrate(db, daily_log) if daily_log else None


def update_daily_log(db: Session, daily_log_id: UUID, daily_log: DailyLogCreate):
    db_daily_log = db.get(DailyLog, daily_log_id)

    if not db_daily_log:
        return None

    payload = daily_log.model_dump()
    additional_event_ids = set(payload.pop("additional_event_ids", []))

    _replace_children(db, daily_log_id, payload)

    for key, value in payload.items():
        setattr(db_daily_log, key, value)

    existing_links = db.scalars(
        select(DailyLogEventLink).where(DailyLogEventLink.daily_log_id == daily_log_id)
    ).all()
    existing_event_ids = {link.event_id for link in existing_links}

    for link in existing_links:
        if link.event_id not in additional_event_ids:
            db.delete(link)

    for event_id in additional_event_ids - existing_event_ids:
        db.add(DailyLogEventLink(daily_log_id=daily_log_id, event_id=event_id))

    db.commit()
    db.refresh(db_daily_log)

    return _hydrate(db, db_daily_log)


def delete_daily_log(db: Session, daily_log_id: UUID):
    db_daily_log = db.get(DailyLog, daily_log_id)

    if not db_daily_log:
        return None

    db.query(DailyLogEventLink).filter(
        DailyLogEventLink.daily_log_id == daily_log_id
    ).delete()

    db.delete(db_daily_log)
    db.commit()

    return db_daily_log


def get_daily_report(db: Session, daily_log_id: UUID):
    daily_log = get_daily_log(db, daily_log_id)

    if daily_log is None:
        return None

    event = db.get(Event, daily_log.event_id) if daily_log.event_id else None

    # A report's evidence covers both photos attached directly to this
    # Daily Log and any attached to its primary linked Event.
    owner_filter = Evidence.daily_log_id == daily_log.id
    if daily_log.event_id:
        owner_filter = or_(owner_filter, Evidence.event_id == daily_log.event_id)

    evidence_count = db.scalar(
        select(func.count(Evidence.id)).where(owner_filter)
    )

    column_names = daily_log.__table__.columns.keys()
    report = {c: getattr(daily_log, c) for c in column_names}
    report.update({field: getattr(daily_log, field) for field in _CHILD_TABLES})
    report["linked_event_ids"] = daily_log.linked_event_ids
    report["total_workers"] = daily_log.total_workers
    report["total_man_hours"] = daily_log.total_man_hours
    report["photo_count"] = daily_log.photo_count
    report["event"] = event
    report["evidence_count"] = evidence_count or 0

    # Not part of DailyReportResponse (dropped on serialization there) -
    # used by the PDF/Excel report generators below, which need the
    # actual Evidence rows (filename/caption/category, and the object to
    # fetch photo bytes from for a PDF thumbnail), not just a count.
    daily_log_evidence = list(search_evidence(db, daily_log_id=daily_log.id))
    event_evidence = (
        list(search_evidence(db, event_id=daily_log.event_id))
        if daily_log.event_id
        else []
    )
    seen_ids = {e.id for e in daily_log_evidence}
    report["evidence"] = daily_log_evidence + [
        e for e in event_evidence if e.id not in seen_ids
    ]

    return report


def get_daily_reports_for_project(
    db: Session,
    project_id: UUID,
    start_date=None,
    end_date=None,
    dates=None,
):
    """
    Every Daily Log for a project, in the same shape get_daily_report
    returns for one - the data source for the Report tab's compiled
    Daily Log PDF/Excel export. Bounded either to a contiguous date range
    (start_date/end_date - "this week", "this month") or to an explicit
    list of specific, possibly non-contiguous dates (dates - "just these
    three days"). dates wins if both are given.
    """
    stmt = (
        select(DailyLog)
        .where(DailyLog.project_id == project_id)
        .order_by(DailyLog.diary_date)
    )
    if dates:
        stmt = stmt.where(DailyLog.diary_date.in_(dates))
    else:
        if start_date is not None:
            stmt = stmt.where(DailyLog.diary_date >= start_date)
        if end_date is not None:
            stmt = stmt.where(DailyLog.diary_date <= end_date)

    logs = db.scalars(stmt).all()
    return [get_daily_report(db, log.id) for log in logs]
