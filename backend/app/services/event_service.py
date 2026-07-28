from datetime import date
from uuid import UUID

from sqlalchemy.orm import Session

from app.repositories.event_repository import (
    create_event,
    delete_event,
    get_event,
    get_events,
    search_events_by_date,
    update_event,
    search_events,
    get_event_timeline,
    get_timeline,
    get_project_timeline,
    get_project_events,
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


def search_events_service(
    db: Session,
    keyword: str,
):
    return search_events(db, keyword)

def search_events_by_date_service(
    db: Session,
    start_date: date,
    end_date: date,
):
    return search_events_by_date(
        db,
        start_date,
        end_date,
    )

def get_event_timeline_service(db: Session):
    return get_event_timeline(db)

def get_timeline_service(
    db: Session,
    project_id: UUID,
):
    return get_timeline(
        db,
        project_id,
    )

def get_project_timeline_service(
    db: Session,
    project_id: UUID,
):
    return get_project_timeline(
        db,
        project_id,
    )

def get_project_events_service(
    db: Session,
    project_id: UUID,
):
    return get_project_events(
        db,
        project_id,
    )