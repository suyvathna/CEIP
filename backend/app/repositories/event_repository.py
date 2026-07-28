from uuid import UUID
from datetime import date, datetime
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.event import Event
from app.schemas.event import EventCreate
from sqlalchemy import func


from app.models.evidence import Evidence

from app.models.daily_diary import DailyDiary



def create_event(db: Session, event: EventCreate) -> Event:
    db_event = Event(**event.model_dump())

    db.add(db_event)
    db.commit()
    db.refresh(db_event)

    return db_event


def get_events(db: Session):
    return db.scalars(select(Event)).all()


def get_event(db: Session, event_id: UUID):
    return db.get(Event, event_id)


def update_event(db: Session, event_id: UUID, event: EventCreate):
    db_event = db.get(Event, event_id)

    if not db_event:
        return None

    for key, value in event.model_dump().items():
        setattr(db_event, key, value)

    db.commit()
    db.refresh(db_event)

    return db_event


def delete_event(db: Session, event_id: UUID):
    db_event = db.get(Event, event_id)

    if not db_event:
        return None

    db.delete(db_event)
    db.commit()

    return db_event

def search_events(db: Session, keyword: str):
    statement = (
        select(Event)
        .where(Event.title.ilike(f"%{keyword}%"))
    )

    return db.scalars(statement).all()

def search_events_by_date(
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

def get_event_timeline(db: Session):
    return (
        db.query(Event)
        .order_by(
            Event.event_date.asc(),
            Event.event_time.asc(),
        )
        .all()
    )

def get_timeline(
    db: Session,
    project_id: UUID,
):
    return (
        db.query(Event)
        .filter(Event.project_id == project_id)
        .order_by(
            Event.event_date,
            Event.event_time,
        )
        .all()
    )

def get_project_timeline(
    db: Session,
    project_id: UUID,
):
    return (
        db.query(
            Event.id.label("event_id"),
            Event.title,
            Event.event_type,
            Event.event_date,
            Event.event_time,
            func.count(Evidence.id).label(
                "evidence_count"
            ),
        )
        .outerjoin(
            Evidence,
            Event.id == Evidence.event_id,
        )
        .filter(
            Event.project_id == project_id,
        )
        .group_by(
            Event.id,
            Event.title,
            Event.event_type,
            Event.event_date,
            Event.event_time,
        )
        .order_by(
            Event.event_date.desc(),
            Event.event_time.desc(),
        )
        .all()
    )

def get_project_events(
    db: Session,
    project_id: UUID,
):
    return (
        db.query(Event)
        .filter(Event.project_id == project_id)
        .order_by(
            Event.event_date,
            Event.event_time,
        )
        .all()
    )

def get_project_activity(
    db: Session,
    project_id: UUID,
):
    return (
        db.query(
            Event.id.label("event_id"),
            Event.title,
            Event.event_date,
            Event.event_time,
            Event.created_at,
            func.count(Evidence.id).label(
                "evidence_count"
            ),
            func.count(DailyDiary.id).label(
                "diary_exists"
            ),
        )
        .outerjoin(
            Evidence,
            Evidence.event_id == Event.id,
        )
        .outerjoin(
            DailyDiary,
            DailyDiary.event_id == Event.id,
        )
        .filter(
            Event.project_id == project_id,
        )
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
        .all()
    )