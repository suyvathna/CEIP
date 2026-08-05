from uuid import UUID

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models.correspondence import Correspondence
from app.models.daily_log import DailyLog
from app.models.event import Event
from app.models.evidence import Evidence


def search_events(
    db: Session,
    keyword: str,
    project_id: UUID | None = None,
):
    query = db.query(Event).filter(
        or_(
            Event.title.ilike(f"%{keyword}%"),
            Event.description.ilike(f"%{keyword}%"),
        )
    )
    if project_id is not None:
        query = query.filter(Event.project_id == project_id)
    return query.all()


def search_daily_logs(
    db: Session,
    keyword: str,
    project_id: UUID | None = None,
):
    query = db.query(DailyLog).filter(
        or_(
            DailyLog.work_completed.ilike(f"%{keyword}%"),
            DailyLog.delays.ilike(f"%{keyword}%"),
            DailyLog.remarks.ilike(f"%{keyword}%"),
        )
    )
    if project_id is not None:
        query = query.filter(DailyLog.project_id == project_id)
    return query.all()


def search_evidence(
    db: Session,
    keyword: str,
    project_id: UUID | None = None,
):
    query = db.query(Evidence).filter(Evidence.filename.ilike(f"%{keyword}%"))

    if project_id is not None:
        # Evidence has no project_id of its own - it belongs to exactly one
        # of an Event, a DailyLog or a Correspondence, each of which does
        # carry project_id, so the filter has to reach through whichever
        # one is actually set.
        query = (
            query.outerjoin(Event, Evidence.event_id == Event.id)
            .outerjoin(DailyLog, Evidence.daily_log_id == DailyLog.id)
            .outerjoin(Correspondence, Evidence.correspondence_id == Correspondence.id)
            .filter(
                or_(
                    Event.project_id == project_id,
                    DailyLog.project_id == project_id,
                    Correspondence.project_id == project_id,
                )
            )
        )

    return query.all()
