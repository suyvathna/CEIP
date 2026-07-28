from uuid import UUID

from sqlalchemy.orm import Session

from app.models.evidence import Evidence


def create_evidence(
    db: Session,
    evidence: Evidence,
):
    db.add(evidence)
    db.commit()
    db.refresh(evidence)

    return evidence


def get_evidences(db: Session):
    return (
        db.query(Evidence)
        .order_by(Evidence.created_at.desc())
        .all()
    )


def get_evidence(
    db: Session,
    evidence_id: UUID,
):
    return (
        db.query(Evidence)
        .filter(Evidence.id == evidence_id)
        .first()
    )


def delete_evidence(
    db: Session,
    evidence: Evidence,
):
    db.delete(evidence)
    db.commit()


def search_evidence(
    db: Session,
    filename: str | None = None,
    event_id: UUID | None = None,
):
    query = db.query(Evidence)

    if filename:
        query = query.filter(
            Evidence.filename.ilike(f"%{filename}%")
        )

    if event_id:
        query = query.filter(
            Evidence.event_id == event_id
        )

    return (
        query.order_by(Evidence.created_at.desc())
        .all()
    )