from datetime import date
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.models.daily_diary import DailyDiary
from app.models.evidence import Evidence
from app.models.event import Event
from app.schemas.event import EventCreate





def create_event_service(db: Session, event: EventCreate) -> Event:
    db_event = Event(**event.model_dump())

    db.add(db_event)
    db.commit()
    db.refresh(db_event)

    return db_event


def get_event_service(db: Session, event_id: UUID):
    return db.get(Event, event_id)

def mark_notice_given_service(db: Session, event_id: UUID, notice_given_date: date):
    event = db.get(Event, event_id)

    if not event:
        return None

    event.notice_given_date = notice_given_date

    db.commit()
    db.refresh(event)

    return event

def update_event_service(db: Session, event_id: UUID, event: EventCreate):
    db_event = db.get(Event, event_id)

    if not db_event:
        return None

    for key, value in event.model_dump().items():
        setattr(db_event, key, value)

    db.commit()
    db.refresh(db_event)

    return db_event


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
            "This event still has diary entries or evidence recorded "
            "under it. Delete those first, or keep the event as a record."
        )

    return db_event


def search_events_service(db: Session, keyword: str):
    statement = select(Event).where(Event.title.ilike(f"%{keyword}%"))
    return db.scalars(statement).all()


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

    return db.scalars(statement).all()

def get_project_events_service(db: Session, project_id: UUID):
    stmt = (
        select(Event)
        .where(Event.project_id == project_id)
        .order_by(
            Event.event_date,
            Event.event_time,
        )
    )
    return db.scalars(stmt).all()


def get_project_activity_service(db: Session, project_id: UUID):
    stmt = (
        select(
            Event.id.label("event_id"),
            Event.title,
            Event.event_date,
            Event.event_time,
            Event.created_at,
            func.count(Evidence.id).label("evidence_count"),
            func.count(DailyDiary.id).label("diary_exists"),
        )
        .outerjoin(Evidence, Evidence.event_id == Event.id)
        .outerjoin(DailyDiary, DailyDiary.event_id == Event.id)
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
            "diary_exists": activity.diary_exists > 0,
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

    return db.scalars(stmt).all()


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
