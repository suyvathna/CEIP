from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.event import EventCreate, EventResponse
from app.services.event_service import (
    create_event_service,
    delete_event_service,
    get_event_service,
    search_events_by_date_service,
    search_events_service,
    update_event_service,
    get_project_events_service,
    get_project_activity_service,
    filter_events_service,
    get_timeline_analytics_service,
)
from app.schemas.activity import ActivityResponse
from app.schemas.timeline_analytics import TimelineDay
from app.services.auth_service import (get_current_user)

router = APIRouter(
    prefix="/events",
    tags=["Events"],
    #dependencies=[Depends(get_current_user)]    # this line ensures that all endpoints in this router require authentication
)


@router.post("/", response_model=EventResponse)
def create_event(
    event: EventCreate,
    db: Session = Depends(get_db),
):
    return create_event_service(db, event)


@router.get("/search", response_model=list[EventResponse])
def search_event(
    keyword: str,
    db: Session = Depends(get_db),
):
    return search_events_service(db, keyword)


@router.get("/search-by-date", response_model=list[EventResponse])
def search_event_by_date(
    start_date: date,
    end_date: date,
    db: Session = Depends(get_db),
):
    return search_events_by_date_service(
        db,
        start_date,
        end_date,
    )


@router.get(
    "/project/{project_id}",
    response_model=list[EventResponse],
)
def read_project_events(
    project_id: UUID,
    db: Session = Depends(get_db),
):
    return get_project_events_service(
        db,
        project_id,
    )

@router.get(
    "/project/{project_id}/activity",
    response_model=list[ActivityResponse],
)
def project_activity(
    project_id: UUID,
    db: Session = Depends(get_db),
):
    return get_project_activity_service(
        db,
        project_id,
    )

@router.get(
    "/filter",
    response_model=list[EventResponse],
)
def filter_events(
    project_id: UUID | None = None,
    event_type: str | None = None,
    severity: str | None = None,
    status: str | None = None,
    db: Session = Depends(get_db),
):
    return filter_events_service(
        db=db,
        project_id=project_id,
        event_type=event_type,
        severity=severity,
        status=status,
    )

@router.get(
    "/project/{project_id}/timeline-analytics",
    response_model=list[TimelineDay],
)
def timeline_analytics(
    project_id: UUID,
    db: Session = Depends(get_db),
):
    return get_timeline_analytics_service(
        db,
        project_id,
    )






@router.get("/{event_id}", response_model=EventResponse)
def read_event(
    event_id: UUID,
    db: Session = Depends(get_db),
):
    event = get_event_service(db, event_id)

    if event is None:
        raise HTTPException(
            status_code=404,
            detail="Event not found",
        )

    return event


@router.put("/{event_id}", response_model=EventResponse)
def update_event(
    event_id: UUID,
    event: EventCreate,
    db: Session = Depends(get_db),
):
    updated = update_event_service(
        db,
        event_id,
        event,
    )

    if updated is None:
        raise HTTPException(
            status_code=404,
            detail="Event not found",
        )

    return updated


@router.delete("/{event_id}")
def delete_event(
    event_id: UUID,
    db: Session = Depends(get_db),
):
    deleted = delete_event_service(
        db,
        event_id,
    )

    if deleted is None:
        raise HTTPException(
            status_code=404,
            detail="Event not found",
        )

    return {
        "message": "Event deleted successfully",
    }