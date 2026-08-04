from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.notification import (
    EnginesOut,
    MarkAllReadOut,
    NotificationOut,
    NotificationSummaryOut,
    engine_reference,
)
from app.services import notification_service

router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.get("/engines", response_model=EnginesOut)
def read_engines():
    """What "Engine A" and "Engine B" mean, for the UI's labels.

    Served from the backend so the product and the code can never end up
    describing the two loops differently."""
    return engine_reference()


@router.get("/", response_model=list[NotificationOut])
def list_notifications(
    project_id: UUID | None = None,
    unread_only: bool = False,
    category: str | None = None,
    engine: str | None = Query(
        default=None,
        pattern="^[AB]$",
        description='"A" for compliance obligations, "B" for the event-driven clocks.',
    ),
    include_resolved: bool = False,
    limit: int = 50,
    db: Session = Depends(get_db),
):
    """
    The alert stream, worst first then newest.

    Ordering is by severity before recency on purpose: a PM opening this
    on a bad morning needs the Notice of Dissatisfaction that expires
    tomorrow above the progress report due next week, regardless of which
    was raised more recently.

    Resolved alerts are hidden by default. They are not deleted -
    include_resolved=true reads the history, which is the evidence that
    the system warned in time and the warning was acted on.
    """
    return notification_service.list_notifications(
        db,
        project_id=project_id,
        unread_only=unread_only,
        category=category,
        engine=engine,
        include_resolved=include_resolved,
        limit=limit,
    )


@router.get("/summary", response_model=NotificationSummaryOut)
def read_summary(
    project_id: UUID | None = None,
    db: Session = Depends(get_db),
):
    """Bell badge counts. Split by severity because "12 unread" means
    something very different depending on whether any of them are
    time-bars."""
    return notification_service.unread_summary(db, project_id=project_id)


@router.patch("/{notification_id}/read", response_model=NotificationOut)
def mark_read(notification_id: UUID, db: Session = Depends(get_db)):
    notification = notification_service.mark_read(db, notification_id)

    if notification is None:
        raise HTTPException(status_code=404, detail="Notification not found")

    return notification


@router.patch("/read-all", response_model=MarkAllReadOut)
def mark_all_read(
    project_id: UUID | None = None,
    db: Session = Depends(get_db),
):
    return {"marked": notification_service.mark_all_read(db, project_id=project_id)}
