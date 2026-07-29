from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models.daily_diary import DailyDiary
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


def search_daily_diaries(
    db: Session,
    keyword: str,
):
    return (
        db.query(DailyDiary)
        .filter(
            or_(
                DailyDiary.work_completed.ilike(f"%{keyword}%"),
                DailyDiary.delays.ilike(f"%{keyword}%"),
                DailyDiary.remarks.ilike(f"%{keyword}%"),
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