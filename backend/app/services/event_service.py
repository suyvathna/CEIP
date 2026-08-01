from datetime import date
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.models.daily_log import DailyLog, DailyLogEventLink
from app.models.evidence import Evidence
from app.models.event import Event
from app.models.project import Project
from app.schemas.event import EventCreate
from app.services.event_requirements_service import event_requirements_summary
from app.services.notice_deadline_service import NOTICE_PERIOD_DAYS


def _auto_link_same_day_logs(db: Session, db_event: Event) -> None:
    """
    Mirror of daily_log_service._auto_link_same_day_events: an Event and
    any Daily Log already logged for the same project on the same date
    are linked automatically, in whichever order they happen to be
    created. This removes the need for the old "add a log entry from
    inside this event" flow - the two records find each other by date on
    their own.
    """
    same_day_logs = list(
        db.scalars(
            select(DailyLog).where(
                DailyLog.project_id == db_event.project_id,
                DailyLog.diary_date == db_event.event_date,
            )
        ).all()
    )

    for daily_log in same_day_logs:
        if daily_log.event_id == db_event.id:
            continue

        existing_link = db.scalar(
            select(DailyLogEventLink).where(
                DailyLogEventLink.daily_log_id == daily_log.id,
                DailyLogEventLink.event_id == db_event.id,
            )
        )
        if existing_link is None:
            db.add(DailyLogEventLink(daily_log_id=daily_log.id, event_id=db_event.id))


def attach_notice_periods(db: Session, events):
    """
    Hydrates the transient notice_period_days attribute EventResponse's
    computed fields read from, so the deadline math respects each event's
    owning project's configured period instead of always assuming the
    FIDIC unamended 28 days. Not a DB column - just carried on the ORM
    instance for the duration of this request/response cycle.
    """
    single = isinstance(events, Event)
    event_list = [events] if single else list(events)

    project_ids = {e.project_id for e in event_list}

    if project_ids:
        projects = {
            p.id: p
            for p in db.scalars(
                select(Project).where(Project.id.in_(project_ids))
            ).all()
        }
    else:
        projects = {}

    for e in event_list:
        project = projects.get(e.project_id)
        e.notice_period_days = (
            project.notice_period_days if project else NOTICE_PERIOD_DAYS
        )

    return event_list[0] if single else event_list


def _next_event_no(db: Session, project_id: UUID) -> str:
    """
    "EVT-001", "EVT-002", ... scoped per project - mirrors Claim's
    _next_claim_no. Only used when the Contractor leaves Event No. blank.
    """
    count = db.scalar(
        select(func.count()).select_from(Event).where(Event.project_id == project_id)
    )
    return f"EVT-{(count or 0) + 1:03d}"


def create_event_service(db: Session, event: EventCreate) -> Event:
    payload = event.model_dump()
    payload["event_no"] = payload.get("event_no") or _next_event_no(db, event.project_id)

    db_event = Event(**payload)

    db.add(db_event)
    db.flush()

    _auto_link_same_day_logs(db, db_event)

    db.commit()
    db.refresh(db_event)

    return attach_notice_periods(db, db_event)


def get_event_service(db: Session, event_id: UUID):
    event = db.get(Event, event_id)
    return attach_notice_periods(db, event) if event else None


def get_event_requirements_service(db: Session, event_id: UUID):
    event = db.get(Event, event_id)
    if not event:
        return None

    return event_requirements_summary(db, event)

def mark_notice_given_service(db: Session, event_id: UUID, notice_given_date: date):
    event = db.get(Event, event_id)

    if not event:
        return None

    event.notice_given_date = notice_given_date

    db.commit()
    db.refresh(event)

    return attach_notice_periods(db, event)

def update_event_service(db: Session, event_id: UUID, event: EventCreate):
    db_event = db.get(Event, event_id)

    if not db_event:
        return None

    payload = event.model_dump()
    # Never blank out an already-generated Event No. from an edit form
    # that submits it empty - only overwrite when the caller actually
    # supplied a new value.
    if not payload.get("event_no"):
        payload.pop("event_no", None)

    for key, value in payload.items():
        setattr(db_event, key, value)

    db.commit()
    db.refresh(db_event)

    return attach_notice_periods(db, db_event)


def delete_event_service(db: Session, event_id: UUID):
    db_event = db.get(Event, event_id)

    if not db_event:
        return None

    try:
        db.delete(db_event)
        db.commit()
    except IntegrityError:
        db.rollback()
        raise ValueError(
            "This event still has daily log entries or evidence recorded "
            "under it. Delete those first, or keep the event as a record."
        )

    return db_event


def search_events_service(db: Session, keyword: str):
    statement = select(Event).where(Event.title.ilike(f"%{keyword}%"))
    return attach_notice_periods(db, db.scalars(statement).all())


def search_events_by_date_service(
    db: Session,
    start_date: date,
    end_date: date,
):
    statement = (
        select(Event)
        .where(
            Event.event_date >= start_date,
            Event.event_date <= end_date,
        )
        .order_by(Event.event_date)
    )

    return attach_notice_periods(db, db.scalars(statement).all())

def get_project_events_service(db: Session, project_id: UUID):
    stmt = (
        select(Event)
        .where(Event.project_id == project_id)
        .order_by(
            Event.event_date,
            Event.event_time,
        )
    )
    return attach_notice_periods(db, db.scalars(stmt).all())


def get_project_activity_service(db: Session, project_id: UUID):
    stmt = (
        select(
            Event.id.label("event_id"),
            Event.title,
            Event.event_date,
            Event.event_time,
            Event.created_at,
            func.count(Evidence.id).label("evidence_count"),
            func.count(DailyLog.id).label("daily_log_exists"),
        )
        .outerjoin(Evidence, Evidence.event_id == Event.id)
        .outerjoin(DailyLog, DailyLog.event_id == Event.id)
        .where(Event.project_id == project_id)
        .group_by(
            Event.id,
            Event.title,
            Event.event_date,
            Event.event_time,
            Event.created_at,
        )
        .order_by(
            Event.event_date.desc(),
            Event.event_time.desc(),
        )
    )

    activities = db.execute(stmt).all()

    return [
        {
            "activity_type": "EVENT",
            "event_id": activity.event_id,
            "title": activity.title,
            "event_date": activity.event_date,
            "event_time": activity.event_time,
            "evidence_count": activity.evidence_count,
            "daily_log_exists": activity.daily_log_exists > 0,
            "created_at": activity.created_at,
        }
        for activity in activities
    ]


def filter_events_service(
    db: Session,
    project_id: UUID | None = None,
    event_type: str | None = None,
    severity: str | None = None,
    status: str | None = None,
):
    stmt = select(Event)

    if project_id:
        stmt = stmt.where(Event.project_id == project_id)

    if event_type:
        stmt = stmt.where(Event.event_type == event_type)

    if severity:
        stmt = stmt.where(Event.severity == severity)

    if status:
        stmt = stmt.where(Event.status == status)

    stmt = stmt.order_by(
        Event.event_date.desc(),
        Event.event_time.desc(),
    )

    return attach_notice_periods(db, db.scalars(stmt).all())


def get_timeline_analytics_service(
    db: Session,
    project_id: UUID,
):
    stmt = (
        select(Event)
        .where(Event.project_id == project_id)
        .order_by(
            Event.event_date,
            Event.event_time,
        )
    )
    events = db.scalars(stmt).all()

    grouped = {}

    for event in events:
        if event.event_date not in grouped:
            grouped[event.event_date] = []

        grouped[event.event_date].append(event)

    return [
        {
            "event_date": event_date,
            "total_events": len(day_events),
            "events": day_events,
        }
        for event_date, day_events in grouped.items()
    ]
