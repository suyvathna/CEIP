from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.models.correspondence import Correspondence
from app.schemas.correspondence import CorrespondenceCreate


def _next_correspondence_no(db: Session, project_id: UUID) -> str:
    """
    "COR-001", "COR-002", ... scoped per project - mirrors
    event_service._next_event_no. Only used when the Contractor leaves
    Correspondence No. blank.
    """
    count = db.scalar(
        select(func.count())
        .select_from(Correspondence)
        .where(Correspondence.project_id == project_id)
    )
    return f"COR-{(count or 0) + 1:03d}"


def create_correspondence_service(
    db: Session, correspondence: CorrespondenceCreate
) -> Correspondence:
    payload = correspondence.model_dump()
    payload["correspondence_no"] = payload.get("correspondence_no") or (
        _next_correspondence_no(db, correspondence.project_id)
    )

    db_correspondence = Correspondence(**payload)

    db.add(db_correspondence)
    db.commit()
    db.refresh(db_correspondence)

    return db_correspondence


def get_correspondence_service(db: Session, correspondence_id: UUID):
    return db.get(Correspondence, correspondence_id)


def get_project_correspondence_service(db: Session, project_id: UUID):
    stmt = (
        select(Correspondence)
        .where(Correspondence.project_id == project_id)
        .order_by(Correspondence.correspondence_date.desc())
    )
    return db.scalars(stmt).all()


def update_correspondence_service(
    db: Session, correspondence_id: UUID, correspondence: CorrespondenceCreate
):
    db_correspondence = db.get(Correspondence, correspondence_id)

    if db_correspondence is None:
        return None

    payload = correspondence.model_dump()
    if not payload.get("correspondence_no"):
        payload.pop("correspondence_no", None)

    for key, value in payload.items():
        setattr(db_correspondence, key, value)

    db.commit()
    db.refresh(db_correspondence)

    return db_correspondence


def delete_correspondence_service(db: Session, correspondence_id: UUID):
    db_correspondence = db.get(Correspondence, correspondence_id)

    if db_correspondence is None:
        return None

    try:
        db.delete(db_correspondence)
        db.commit()
    except IntegrityError:
        db.rollback()
        raise ValueError(
            "This correspondence record still has attachments linked to "
            "it and can't be deleted."
        )

    return db_correspondence
