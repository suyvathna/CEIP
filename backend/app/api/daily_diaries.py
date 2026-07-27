from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import SessionLocal
from app.schemas.daily_diary import (
    DailyDiaryCreate,
    DailyDiaryResponse,
)
from app.services.daily_diary_service import (
    create_daily_diary_service,
    get_daily_diaries_service,
    get_daily_diary_service,
)

router = APIRouter(
    prefix="/daily-diaries",
    tags=["Daily Diaries"],
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/", response_model=DailyDiaryResponse)
def create_daily_diary(
    diary: DailyDiaryCreate,
    db: Session = Depends(get_db),
):
    return create_daily_diary_service(db, diary)


@router.get("/", response_model=list[DailyDiaryResponse])
def read_daily_diaries(
    db: Session = Depends(get_db),
):
    return get_daily_diaries_service(db)


@router.get("/{diary_id}", response_model=DailyDiaryResponse)
def read_daily_diary(
    diary_id: UUID,
    db: Session = Depends(get_db),
):
    diary = get_daily_diary_service(db, diary_id)

    if diary is None:
        raise HTTPException(
            status_code=404,
            detail="Daily diary not found",
        )

    return diary