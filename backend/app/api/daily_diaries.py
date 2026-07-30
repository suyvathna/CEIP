from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.daily_diary import (
    DailyDiaryCreate,
    DailyDiaryResponse,
)

from app.schemas.daily_report import DailyReportResponse
from app.services.daily_diary_service import (
    create_daily_diary,
    delete_daily_diary,
    get_daily_diaries,
    get_daily_diary,
    get_daily_report,
    update_daily_diary,
    get_diaries_for_event,
    get_diaries_for_project,
)

router = APIRouter(
    prefix="/daily-diaries",
    tags=["Daily Diaries"],
)

@router.post("/", response_model=DailyDiaryResponse)
def create_daily_diary_endpoint(
    diary: DailyDiaryCreate,
    db: Session = Depends(get_db),
):
    return create_daily_diary(db, diary)


@router.get("/", response_model=list[DailyDiaryResponse])
def read_daily_diaries_endpoint(
    db: Session = Depends(get_db),
):
    return get_daily_diaries(db)

@router.get("/event/{event_id}", response_model=list[DailyDiaryResponse])
def read_diaries_for_event_endpoint(
    event_id: UUID,
    db: Session = Depends(get_db),
):
    return get_diaries_for_event(db, event_id)

@router.get("/project/{project_id}", response_model=list[DailyDiaryResponse])
def read_diaries_for_project_endpoint(
    project_id: UUID,
    db: Session = Depends(get_db),
):
    return get_diaries_for_project(db, project_id)

@router.get("/{diary_id}", response_model=DailyDiaryResponse)
def read_daily_diary_endpoint(
    diary_id: UUID,
    db: Session = Depends(get_db),
):
    diary = get_daily_diary(db, diary_id)

    if diary is None:
        raise HTTPException(
            status_code=404,
            detail="Daily diary not found",
        )

    return diary


@router.put("/{diary_id}", response_model=DailyDiaryResponse)
def update_daily_diary_endpoint(
    diary_id: UUID,
    diary: DailyDiaryCreate,
    db: Session = Depends(get_db),
):
    updated = update_daily_diary(db, diary_id, diary)

    if updated is None:
        raise HTTPException(
            status_code=404,
            detail="Daily diary not found",
        )

    return updated


@router.delete("/{diary_id}")
def delete_daily_diary_endpoint(
    diary_id: UUID,
    db: Session = Depends(get_db),
):
    deleted = delete_daily_diary(db, diary_id)

    if deleted is None:
        raise HTTPException(
            status_code=404,
            detail="Daily diary not found",
        )

    return {"message": "Daily diary deleted successfully"}


@router.get(
    "/{diary_id}/report",
    response_model=DailyReportResponse,
)
def daily_report_endpoint(
    diary_id: UUID,
    db: Session = Depends(get_db),
):
    report = get_daily_report(db, diary_id)

    if report is None:
        raise HTTPException(
            status_code=404,
            detail="Daily diary not found",
        )

    return report