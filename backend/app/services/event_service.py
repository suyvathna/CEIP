from uuid import UUID

from sqlalchemy.orm import Session

from app.repositories.event_repository import (
    create_event,
    delete_event,
    get_event,
    get_events,
    update_event,
)
from app.schemas.event import EventCreate


def create_event_service(db: Session, event: EventCreate):
    return create_event(db, event)


def get_events_service(db: Session):
    return get_events(db)


def get_event_service(db: Session, event_id: UUID):
    return get_event(db, event_id)


def update_event_service(db: Session, event_id: UUID, event: EventCreate):
    return update_event(db, event_id, event)


def delete_event_service(db: Session, event_id: UUID):
    return delete_event(db, event_id)