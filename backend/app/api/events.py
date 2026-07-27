from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import SessionLocal
from app.schemas.event import EventCreate, EventResponse
from app.services.event_service import (
    create_event_service,
    delete_event_service,
    get_event_service,
    get_events_service,
    update_event_service,
)

router = APIRouter(
    prefix="/events",
    tags=["Events"],
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/", response_model=EventResponse)
def create_event(
    event: EventCreate,
    db: Session = Depends(get_db),
):
    return create_event_service(db, event)


@router.get("/", response_model=list[EventResponse])
def read_events(
    db: Session = Depends(get_db),
):
    return get_events_service(db)


@router.get("/{event_id}", response_model=EventResponse)
def read_event(
    event_id: UUID,
    db: Session = Depends(get_db),
):
    event = get_event_service(db, event_id)

    if event is None:
        raise HTTPException(404, "Event not found")

    return event


@router.put("/{event_id}", response_model=EventResponse)
def update_event(
    event_id: UUID,
    event: EventCreate,
    db: Session = Depends(get_db),
):
    updated = update_event_service(db, event_id, event)

    if updated is None:
        raise HTTPException(404, "Event not found")

    return updated


@router.delete("/{event_id}")
def delete_event(
    event_id: UUID,
    db: Session = Depends(get_db),
):
    deleted = delete_event_service(db, event_id)

    if deleted is None:
        raise HTTPException(404, "Event not found")

    return {"message": "Event deleted successfully"}