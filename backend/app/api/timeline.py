from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.timeline import TimelineResponse
from app.services.timeline_service import (
    get_timeline_service,
)

router = APIRouter(
    prefix="/timeline",
    tags=["Timeline"],
)


@router.get(
    "/{project_id}",
    response_model=TimelineResponse,
)
def read_timeline(
    project_id: UUID,
    start_date: date | None = None,
    end_date: date | None = None,
    event_type: str | None = None,
    severity: str | None = None,
    db: Session = Depends(get_db),
):
    return get_timeline_service(
        db,
        project_id,
        start_date,
        end_date,
        event_type,
        severity,
    )