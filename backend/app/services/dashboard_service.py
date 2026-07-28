from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.daily_diary import DailyDiary
from app.models.event import Event
from app.models.evidence import Evidence
from app.models.project import Project
from datetime import datetime

def get_dashboard_service(db: Session, project_id: UUID):
    project = db.get(Project, project_id)

    if project is None:
        return None

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

    # 1. ADD THIS MISSING QUERY HERE
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

        "total_events": total_events or 0,
        "total_daily_diaries": total_daily_diaries or 0,
        "total_evidence": total_evidence or 0,

        "open_events": open_events or 0,
        "closed_events": closed_events or 0,

        "high_severity_events": high_events or 0,
        "medium_severity_events": medium_events or 0,
        "low_severity_events": low_events or 0,

        # 2. NOW THIS CAN ACCESS event_type_statistics WITHOUT ERROR
        "event_type_statistics": [
            {
                "event_type": row.event_type,
                "total": row.total,
            }
            for row in event_type_statistics
        ],

        "recent_events": recent_events or [],
    }

def get_project_report_service(
    db: Session,
    project_id: UUID,
):
    # Fetch primary entity by PK
    project = db.get(Project, project_id)

    if project is None:
        return None

    # Scalar counts using select().where()
    total_events = db.scalar(
        select(func.count(Event.id)).where(Event.project_id == project_id)
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

    high_severity = db.scalar(
        select(func.count(Event.id)).where(
            Event.project_id == project_id,
            Event.severity == "High",
        )
    )

    medium_severity = db.scalar(
        select(func.count(Event.id)).where(
            Event.project_id == project_id,
            Event.severity == "Medium",
        )
    )

    low_severity = db.scalar(
        select(func.count(Event.id)).where(
            Event.project_id == project_id,
            Event.severity == "Low",
        )
    )

    # Fetch scalar entity result using db.scalars().first()
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
        "total_events": total_events or 0,
        "total_daily_diaries": total_daily_diaries or 0,
        "total_evidence": total_evidence or 0,
        "open_events": open_events or 0,
        "closed_events": closed_events or 0,
        "high_severity": high_severity or 0,
        "medium_severity": medium_severity or 0,
        "low_severity": low_severity or 0,
        "latest_event": (
            latest_event.title
            if latest_event
            else None
        ),
        "generated_at": datetime.utcnow(),
    }