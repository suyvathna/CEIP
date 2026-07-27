from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.event import Event
from app.schemas.event import EventCreate


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