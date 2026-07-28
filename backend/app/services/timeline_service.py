from datetime import date
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.event import Event


def get_filtered_project_timeline_service(
    db: Session,
    project_id: UUID,
    start_date: date | None,
    end_date: date | None,
    event_type: str | None,
    severity: str | None,
):
    statement = select(Event).where(Event.project_id == project_id)

    if start_date:
        statement = statement.where(Event.event_date >= start_date)

    if end_date:
        statement = statement.where(Event.event_date <= end_date)

    if event_type:
        statement = statement.where(Event.event_type == event_type)

    if severity:
        statement = statement.where(Event.severity == severity)

    statement = statement.order_by(
        Event.event_date,
        Event.event_time,
    )

    events = db.scalars(statement).all()

    return {
        "project_id": project_id,
        "total_events": len(events),
        "events": events,
    }