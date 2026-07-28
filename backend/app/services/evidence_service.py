from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.evidence import Evidence


def create_evidence(db: Session, evidence: Evidence):
    db.add(evidence)
    db.commit()
    db.refresh(evidence)

    return evidence


def get_evidences(db: Session):
    statement = select(Evidence).order_by(Evidence.created_at.desc())
    return db.scalars(statement).all()


def get_evidence(db: Session, evidence_id: UUID):
    return db.get(Evidence, evidence_id)


def delete_evidence(db: Session, evidence: Evidence):
    db.delete(evidence)
    db.commit()


def search_evidence(
    db: Session,
    filename: str | None = None,
    event_id: UUID | None = None,
):
    statement = select(Evidence)

    if filename:
        statement = statement.where(Evidence.filename.ilike(f"%{filename}%"))

    if event_id:
        statement = statement.where(Evidence.event_id == event_id)

    statement = statement.order_by(Evidence.created_at.desc())

    return db.scalars(statement).all()