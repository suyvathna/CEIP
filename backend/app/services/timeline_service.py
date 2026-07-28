from datetime import date

from sqlalchemy.orm import Session

from app.models.event import Event


def get_timeline_service(
    db: Session,
    project_id,
    start_date: date | None,
    end_date: date | None,
    event_type: str | None,
    severity: str | None,
):
    query = db.query(Event).filter(
        Event.project_id == project_id
    )

    if start_date:
        query = query.filter(
            Event.event_date >= start_date
        )

    if end_date:
        query = query.filter(
            Event.event_date <= end_date
        )

    if event_type:
        query = query.filter(
            Event.event_type == event_type
        )

    if severity:
        query = query.filter(
            Event.severity == severity
        )

    events = (
        query
        .order_by(
            Event.event_date,
            Event.event_time,
        )
        .all()
    )

    return {
        "project_id": project_id,
        "total_events": len(events),
        "events": events,
    }