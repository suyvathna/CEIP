from uuid import UUID

from sqlalchemy.orm import Session

from app.repositories.daily_diary_repository import (
    create_daily_diary,
    get_daily_diaries,
    get_daily_diary,
)
from app.schemas.daily_diary import DailyDiaryCreate


def create_daily_diary_service(
    db: Session,
    diary: DailyDiaryCreate,
):
    return create_daily_diary(db, diary)


def get_daily_diaries_service(db: Session):
    return get_daily_diaries(db)


def get_daily_diary_service(
    db: Session,
    diary_id: UUID,
):
    return get_daily_diary(db, diary_id)