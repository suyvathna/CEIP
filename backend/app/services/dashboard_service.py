from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.daily_diary import DailyDiary
from app.models.event import Event
from app.models.evidence import Evidence
from app.models.project import Project


def get_dashboard_service(
    db: Session,
    project_id,
):
    project = (
        db.query(Project)
        .filter(Project.id == project_id)
        .first()
    )

    if project is None:
        return None

    total_events = (
        db.query(func.count(Event.id))
        .filter(Event.project_id == project_id)
        .scalar()
    )

    open_events = (
        db.query(func.count(Event.id))
        .filter(
            Event.project_id == project_id,
            Event.status == "Open",
        )
        .scalar()
    )

    closed_events = (
        db.query(func.count(Event.id))
        .filter(
            Event.project_id == project_id,
            Event.status == "Closed",
        )
        .scalar()
    )

    high_events = (
        db.query(func.count(Event.id))
        .filter(
            Event.project_id == project_id,
            Event.severity == "High",
        )
        .scalar()
    )

    medium_events = (
        db.query(func.count(Event.id))
        .filter(
            Event.project_id == project_id,
            Event.severity == "Medium",
        )
        .scalar()
    )

    low_events = (
        db.query(func.count(Event.id))
        .filter(
            Event.project_id == project_id,
            Event.severity == "Low",
        )
        .scalar()
    )

    total_daily_diaries = (
        db.query(func.count(DailyDiary.id))
        .join(Event, Event.id == DailyDiary.event_id)
        .filter(Event.project_id == project_id)
        .scalar()
    )

    total_evidence = (
        db.query(func.count(Evidence.id))
        .join(Event, Event.id == Evidence.event_id)
        .filter(Event.project_id == project_id)
        .scalar()
    )

    event_type_statistics = (
        db.query(
            Event.event_type,
            func.count(Event.id).label("total"),
        )
        .filter(
            Event.project_id == project_id,
        )
        .group_by(
            Event.event_type,
        )
        .order_by(
            Event.event_type,
        )
        .all()
    )



    

    recent_events = (
        db.query(Event)
        .filter(Event.project_id == project_id)
        .order_by(Event.created_at.desc())
        .limit(5)
        .all()
    )

    return {
        "project_id": project.id,
        "project_name": project.project_name,

        "total_events": total_events,
        "total_daily_diaries": total_daily_diaries,
        "total_evidence": total_evidence,

        "open_events": open_events,
        "closed_events": closed_events,

        "high_severity_events": high_events,
        "medium_severity_events": medium_events,
        "low_severity_events": low_events,

        "event_type_statistics": [
            {
                "event_type": row.event_type,
                "total": row.total,
            }
            for row in event_type_statistics
        ],

        "recent_events": recent_events,
    }