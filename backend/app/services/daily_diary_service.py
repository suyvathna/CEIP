from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.daily_diary import DailyDiary, DiaryEventLink
from app.models.event import Event
from app.models.evidence import Evidence
from app.schemas.daily_diary import DailyDiaryCreate


def _linked_event_ids(db: Session, diary_id: UUID) -> list[UUID]:
    stmt = select(DiaryEventLink.event_id).where(DiaryEventLink.diary_id == diary_id)
    return list(db.scalars(stmt).all())


def _hydrate(db: Session, diary: DailyDiary) -> DailyDiary:
    diary.linked_event_ids = _linked_event_ids(db, diary.id)
    return diary


def create_daily_diary(
    db: Session,
    diary: DailyDiaryCreate,
):
    payload = diary.model_dump()
    additional_event_ids = payload.pop("additional_event_ids", [])

    db_diary = DailyDiary(**payload)

    db.add(db_diary)
    db.flush()

    for event_id in additional_event_ids:
        db.add(DiaryEventLink(diary_id=db_diary.id, event_id=event_id))

    db.commit()
    db.refresh(db_diary)

    return _hydrate(db, db_diary)


def get_daily_diaries(db: Session):
    statement = select(DailyDiary).order_by(DailyDiary.diary_date.desc())
    diaries = db.scalars(statement).all()
    return [_hydrate(db, d) for d in diaries]


def get_diaries_for_project(db: Session, project_id: UUID):
    statement = (
        select(DailyDiary)
        .where(DailyDiary.project_id == project_id)
        .order_by(DailyDiary.diary_date.desc())
    )
    diaries = db.scalars(statement).all()
    return [_hydrate(db, d) for d in diaries]


def get_diaries_for_event(db: Session, event_id: UUID):
    """
    A diary now "belongs" to an event either as its primary event_id or
    via a DiaryEventLink - both count as relevant here, since either way
    the diary is contemporaneous evidence for that event.
    """
    primary_stmt = select(DailyDiary).where(DailyDiary.event_id == event_id)
    primary = list(db.scalars(primary_stmt).all())

    linked_ids_stmt = select(DiaryEventLink.diary_id).where(
        DiaryEventLink.event_id == event_id
    )
    linked_diary_ids = set(db.scalars(linked_ids_stmt).all())
    primary_ids = {d.id for d in primary}

    extra = []
    remaining_ids = linked_diary_ids - primary_ids
    if remaining_ids:
        extra_stmt = select(DailyDiary).where(DailyDiary.id.in_(remaining_ids))
        extra = list(db.scalars(extra_stmt).all())

    combined = primary + extra
    combined.sort(key=lambda d: d.diary_date, reverse=True)
    return [_hydrate(db, d) for d in combined]

def get_daily_diary(db: Session, diary_id: UUID):
    diary = db.get(DailyDiary, diary_id)
    return _hydrate(db, diary) if diary else None


def update_daily_diary(db: Session, diary_id: UUID, diary: DailyDiaryCreate):
    db_diary = db.get(DailyDiary, diary_id)

    if not db_diary:
        return None

    payload = diary.model_dump()
    additional_event_ids = set(payload.pop("additional_event_ids", []))

    for key, value in payload.items():
        setattr(db_diary, key, value)

    existing_links = db.scalars(
        select(DiaryEventLink).where(DiaryEventLink.diary_id == diary_id)
    ).all()
    existing_event_ids = {link.event_id for link in existing_links}

    for link in existing_links:
        if link.event_id not in additional_event_ids:
            db.delete(link)

    for event_id in additional_event_ids - existing_event_ids:
        db.add(DiaryEventLink(diary_id=diary_id, event_id=event_id))

    db.commit()
    db.refresh(db_diary)

    return _hydrate(db, db_diary)


def delete_daily_diary(db: Session, diary_id: UUID):
    db_diary = db.get(DailyDiary, diary_id)

    if not db_diary:
        return None

    db.delete(db_diary)
    db.commit()

    return db_diary


def get_daily_report(db: Session, diary_id: UUID):
    diary = db.get(DailyDiary, diary_id)

    if diary is None:
        return None

    event = db.get(Event, diary.event_id) if diary.event_id else None

    evidence_count = 0
    if diary.event_id:
        evidence_count = db.scalar(
            select(func.count(Evidence.id)).where(
                Evidence.event_id == diary.event_id
            )
        )

    return {
        "id": diary.id,
        "project_id": diary.project_id,
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
