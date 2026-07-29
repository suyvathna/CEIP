from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.daily_diary import DailyDiary
from app.models.event import Event
from app.models.evidence import Evidence
from app.models.project import Project


def _get_project_event_counts(db: Session, project_id: UUID) -> dict:
    """
    Shared counts used by BOTH the dashboard and the project report.
    Previously this exact set of queries was copy-pasted in two functions
    below and could silently drift out of sync with each other.
    """
    total_events = db.scalar(
        select(func.count(Event.id)).where(Event.project_id == project_id)
    )

    open_events = db.scalar(
        select(func.count(Event.id)).where(
            Event.project_id == project_id,
            Event.status == "Open",
        )
    )

    closed_events = db.scalar(
        select(func.count(Event.id)).where(
            Event.project_id == project_id,
            Event.status == "Closed",
        )
    )

    high_events = db.scalar(
        select(func.count(Event.id)).where(
            Event.project_id == project_id,
            Event.severity == "High",
        )
    )

    medium_events = db.scalar(
        select(func.count(Event.id)).where(
            Event.project_id == project_id,
            Event.severity == "Medium",
        )
    )

    low_events = db.scalar(
        select(func.count(Event.id)).where(
            Event.project_id == project_id,
            Event.severity == "Low",
        )
    )

    total_daily_diaries = db.scalar(
        select(func.count(DailyDiary.id))
        .join(Event, Event.id == DailyDiary.event_id)
        .where(Event.project_id == project_id)
    )

    total_evidence = db.scalar(
        select(func.count(Evidence.id))
        .join(Event, Event.id == Evidence.event_id)
        .where(Event.project_id == project_id)
    )

    return {
        "total_events": total_events or 0,
        "total_daily_diaries": total_daily_diaries or 0,
        "total_evidence": total_evidence or 0,
        "open_events": open_events or 0,
        "closed_events": closed_events or 0,
        "high_events": high_events or 0,
        "medium_events": medium_events or 0,
        "low_events": low_events or 0,
    }


def get_dashboard_service(db: Session, project_id: UUID):
    project = db.get(Project, project_id)

    if project is None:
        return None

    counts = _get_project_event_counts(db, project_id)

    event_type_statistics = db.execute(
        select(
            Event.event_type.label("event_type"),
            func.count(Event.id).label("total"),
        )
        .where(Event.project_id == project_id)
        .group_by(Event.event_type)
        .order_by(Event.event_type)
    ).all()

    recent_events = db.scalars(
        select(Event)
        .where(Event.project_id == project_id)
        .order_by(Event.created_at.desc())
        .limit(5)
    ).all()

    return {
        "project_id": project.id,
        "project_name": project.project_name,
        "total_events": counts["total_events"],
        "total_daily_diaries": counts["total_daily_diaries"],
        "total_evidence": counts["total_evidence"],
        "open_events": counts["open_events"],
        "closed_events": counts["closed_events"],
        "high_severity_events": counts["high_events"],
        "medium_severity_events": counts["medium_events"],
        "low_severity_events": counts["low_events"],
        "event_type_statistics": [
            {"event_type": row.event_type, "total": row.total}
            for row in event_type_statistics
        ],
        "recent_events": recent_events or [],
    }


def get_project_report_service(db: Session, project_id: UUID):
    project = db.get(Project, project_id)

    if project is None:
        return None

    counts = _get_project_event_counts(db, project_id)

    latest_event = db.scalars(
        select(Event)
        .where(Event.project_id == project_id)
        .order_by(
            Event.event_date.desc(),
            Event.event_time.desc(),
        )
    ).first()

    return {
        "project_id": project.id,
        "project_name": project.project_name,
        "total_events": counts["total_events"],
        "total_daily_diaries": counts["total_daily_diaries"],
        "total_evidence": counts["total_evidence"],
        "open_events": counts["open_events"],
        "closed_events": counts["closed_events"],
        "high_severity": counts["high_events"],
        "medium_severity": counts["medium_events"],
        "low_severity": counts["low_events"],
        "latest_event": latest_event.title if latest_event else None,
        "generated_at": datetime.now(timezone.utc),
    }
