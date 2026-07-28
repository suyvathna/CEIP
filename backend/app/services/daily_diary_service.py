from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.daily_diary import DailyDiary
from app.models.event import Event
from app.models.evidence import Evidence
from app.schemas.daily_diary import DailyDiaryCreate


def create_daily_diary(
    db: Session,
    diary: DailyDiaryCreate,
):
    db_diary = DailyDiary(**diary.model_dump())

    db.add(db_diary)
    db.commit()
    db.refresh(db_diary)

    return db_diary


def get_daily_diaries(db: Session):
    return (
        db.query(DailyDiary)
        .order_by(DailyDiary.diary_date.desc())
        .all()
    )


def get_daily_diary(
    db: Session,
    diary_id,
):
    return (
        db.query(DailyDiary)
        .filter(DailyDiary.id == diary_id)
        .first()
    )


def get_daily_report(db, diary_id):
    diary = (
        db.query(DailyDiary)
        .filter(DailyDiary.id == diary_id)
        .first()
    )

    if diary is None:
        return None

    event = (
        db.query(Event)
        .filter(Event.id == diary.event_id)
        .first()
    )

    evidence_count = (
        db.query(func.count(Evidence.id))
        .filter(Evidence.event_id == diary.event_id)
        .scalar()
    )

    return {
        "id": diary.id,
        "event_id": diary.event_id,
        "work_completed": diary.work_completed,
        "manpower": diary.manpower,
        "equipment": diary.equipment,
        "materials": diary.materials,
        "delays": diary.delays,
        "safety": diary.safety,
        "visitors": diary.visitors,
        "engineer_instruction": diary.engineer_instruction,
        "tomorrow_plan": diary.tomorrow_plan,
        "remarks": diary.remarks,
        "created_at": diary.created_at,
        "updated_at": diary.updated_at,
        "event": event,
        "evidence_count": evidence_count,
    }