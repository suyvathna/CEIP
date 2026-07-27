from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.daily_diary import DailyDiary
from app.schemas.daily_diary import DailyDiaryCreate


def create_daily_diary(db: Session, diary: DailyDiaryCreate):
    db_diary = DailyDiary(**diary.model_dump())

    db.add(db_diary)
    db.commit()
    db.refresh(db_diary)

    return db_diary


def get_daily_diaries(db: Session):
    return db.scalars(select(DailyDiary)).all()


def get_daily_diary(db: Session, diary_id: UUID):
    return db.get(DailyDiary, diary_id)