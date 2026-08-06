from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models.evidence import Evidence
from app.models.evidence_access_log import EvidenceAccessLog


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
    """
    Raises ValueError instead of deleting when the evidence has been
    locked (attached to a submitted Notice of Claim or fully detailed
    claim - see claim_service.submit_notice) so a claim's supporting
    record can't quietly disappear once the Engineer may already be
    relying on it.
    """
    if evidence.is_locked:
        raise ValueError(
            "This evidence is locked because it's attached to a submitted "
            "claim and can no longer be deleted."
        )

    # Every upload/view/download logs an EvidenceAccessLog row (see
    # log_access below), and that FK has no ON DELETE clause - so without
    # clearing these first, db.delete(evidence) below fails its very
    # first commit for literally every piece of evidence, every time
    # (the "UPLOAD" log row alone guarantees at least one match). The
    # audit trail itself isn't worth keeping once the file it's about is
    # gone.
    db.execute(delete(EvidenceAccessLog).where(EvidenceAccessLog.evidence_id == evidence.id))

    db.delete(evidence)
    db.commit()


def search_evidence(
    db: Session,
    filename: str | None = None,
    event_id: UUID | None = None,
    daily_log_id: UUID | None = None,
    correspondence_id: UUID | None = None,
    obligation_id: UUID | None = None,
):
    statement = select(Evidence)

    if filename:
        statement = statement.where(Evidence.filename.ilike(f"%{filename}%"))

    if event_id:
        statement = statement.where(Evidence.event_id == event_id)

    if daily_log_id:
        statement = statement.where(Evidence.daily_log_id == daily_log_id)

    if correspondence_id:
        statement = statement.where(Evidence.correspondence_id == correspondence_id)

    if obligation_id:
        statement = statement.where(Evidence.obligation_id == obligation_id)

    statement = statement.order_by(Evidence.created_at.desc())

    return db.scalars(statement).all()


def log_access(
    db: Session,
    evidence_id: UUID,
    action: str,
    accessed_by_email: str | None = None,
):
    db.add(
        EvidenceAccessLog(
            evidence_id=evidence_id,
            action=action,
            accessed_by_email=accessed_by_email,
        )
    )
    db.commit()


def get_access_log(db: Session, evidence_id: UUID):
    statement = (
        select(EvidenceAccessLog)
        .where(EvidenceAccessLog.evidence_id == evidence_id)
        .order_by(EvidenceAccessLog.accessed_at.desc())
    )
    return db.scalars(statement).all()
