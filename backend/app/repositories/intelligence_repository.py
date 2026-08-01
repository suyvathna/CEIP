from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models.daily_log import DailyLog
from app.models.event import Event
from app.models.evidence import Evidence


def search_events(
    db: Session,
    keyword: str,
):
    return (
        db.query(Event)
        .filter(
            or_(
                Event.title.ilike(f"%{keyword}%"),
                Event.description.ilike(f"%{keyword}%"),
            )
        )
        .all()
    )


def search_daily_logs(
    db: Session,
    keyword: str,
):
    return (
        db.query(DailyLog)
        .filter(
            or_(
                DailyLog.work_completed.ilike(f"%{keyword}%"),
                DailyLog.delays.ilike(f"%{keyword}%"),
                DailyLog.remarks.ilike(f"%{keyword}%"),
            )
        )
        .all()
    )


def search_evidence(
    db: Session,
    keyword: str,
):
    return (
        db.query(Evidence)
        .filter(
            Evidence.filename.ilike(f"%{keyword}%")
        )
        .all()
    )