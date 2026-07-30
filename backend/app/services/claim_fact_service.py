from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.constants.claim_status import ClaimFactStatus
from app.models.claim import Claim
from app.models.claim_fact import ClaimFact, ClaimFactEvidence
from app.schemas.claim_fact import ClaimFactCreate, ClaimFactRespond


def _evidence_ids_for(db: Session, fact_id: UUID) -> list[UUID]:
    stmt = select(ClaimFactEvidence.evidence_id).where(
        ClaimFactEvidence.fact_id == fact_id
    )
    return list(db.scalars(stmt).all())


def create_fact(db: Session, claim_id: UUID, payload: ClaimFactCreate) -> ClaimFact:
    fact = ClaimFact(
        claim_id=claim_id,
        description=payload.description,
        proposed_by_party=payload.proposed_by_party,
        agreed_days=payload.agreed_days,
        status=ClaimFactStatus.PROPOSED.value,
    )
    db.add(fact)
    db.flush()

    for evidence_id in payload.evidence_ids:
        db.add(ClaimFactEvidence(fact_id=fact.id, evidence_id=evidence_id))

    db.commit()
    db.refresh(fact)

    fact.evidence_ids = _evidence_ids_for(db, fact.id)
    return fact


def get_claim_facts(db: Session, claim_id: UUID) -> list[ClaimFact]:
    stmt = (
        select(ClaimFact)
        .where(ClaimFact.claim_id == claim_id)
        .order_by(ClaimFact.created_at)
    )
    facts = list(db.scalars(stmt).all())

    for fact in facts:
        fact.evidence_ids = _evidence_ids_for(db, fact.id)

    return facts


def get_fact(db: Session, fact_id: UUID) -> ClaimFact | None:
    fact = db.get(ClaimFact, fact_id)
    if fact:
        fact.evidence_ids = _evidence_ids_for(db, fact.id)
    return fact


def respond_to_fact(
    db: Session, fact_id: UUID, payload: ClaimFactRespond
) -> ClaimFact | None:
    fact = db.get(ClaimFact, fact_id)
    if not fact:
        return None

    fact.status = payload.status
    fact.response_comment = payload.response_comment
    fact.responded_by = payload.responded_by
    fact.responded_at = datetime.now(timezone.utc)

    if payload.agreed_days is not None:
        fact.agreed_days = payload.agreed_days

    db.commit()
    db.refresh(fact)

    fact.evidence_ids = _evidence_ids_for(db, fact.id)
    return fact


def link_evidence(db: Session, fact_id: UUID, evidence_id: UUID) -> None:
    existing = db.scalar(
        select(ClaimFactEvidence).where(
            ClaimFactEvidence.fact_id == fact_id,
            ClaimFactEvidence.evidence_id == evidence_id,
        )
    )
    if existing:
        return

    db.add(ClaimFactEvidence(fact_id=fact_id, evidence_id=evidence_id))
    db.commit()


def get_fact_summary(db: Session, claim_id: UUID) -> dict:
    facts = get_claim_facts(db, claim_id)
    claim = db.get(Claim, claim_id)

    agreed = [f for f in facts if f.status == ClaimFactStatus.AGREED.value]
    disputed = [f for f in facts if f.status == ClaimFactStatus.DISPUTED.value]
    needs_evidence = [
        f for f in facts if f.status == ClaimFactStatus.NEEDS_EVIDENCE.value
    ]
    proposed = [f for f in facts if f.status == ClaimFactStatus.PROPOSED.value]

    return {
        "claim_id": claim_id,
        "total_facts": len(facts),
        "agreed_facts": len(agreed),
        "disputed_facts": len(disputed),
        "needs_evidence_facts": len(needs_evidence),
        "proposed_facts": len(proposed),
        "agreed_days_total": sum(f.agreed_days or 0 for f in agreed),
        "disputed_days_total": sum(f.agreed_days or 0 for f in disputed),
        "claimed_days": claim.claimed_days if claim else None,
    }
