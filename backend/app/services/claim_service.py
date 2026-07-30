from datetime import date
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.constants.claim_status import ClaimResponseType, ClaimStatus
from app.models.claim import Claim, ClaimEvent, ClaimResponse
from app.models.evidence import Evidence
from app.models.event import Event
from app.models.project import Project
from app.schemas.claim import (
    ClaimCreate,
    DetailedClaimSubmitRequest,
    EngineerDecisionRequest,
    EngineerLateNoticeFlagRequest,
    NoticeSubmitRequest,
)
from app.services.claim_clock_service import config_from_project, get_today


def _get_project(db: Session, project_id: UUID) -> Project | None:
    return db.get(Project, project_id)


def create_claim(db: Session, payload: ClaimCreate) -> Claim:
    claim = Claim(
        project_id=payload.project_id,
        claim_type=payload.claim_type,
        claiming_party=payload.claiming_party,
        title=payload.title,
        description=payload.description,
        awareness_date=payload.awareness_date,
        claimed_days=payload.claimed_days,
        status=ClaimStatus.NOTIFIED.value,
    )

    db.add(claim)
    db.flush()

    for event_id in payload.event_ids:
        db.add(ClaimEvent(claim_id=claim.id, event_id=event_id))

    db.commit()
    db.refresh(claim)

    return claim


def get_claim(db: Session, claim_id: UUID) -> Claim | None:
    return db.get(Claim, claim_id)


def get_project_claims(db: Session, project_id: UUID):
    stmt = (
        select(Claim)
        .where(Claim.project_id == project_id)
        .order_by(Claim.created_at.desc())
    )
    return db.scalars(stmt).all()


def get_claim_events(db: Session, claim_id: UUID):
    stmt = (
        select(Event)
        .join(ClaimEvent, ClaimEvent.event_id == Event.id)
        .where(ClaimEvent.claim_id == claim_id)
        .order_by(Event.event_date)
    )
    return db.scalars(stmt).all()


def link_event(db: Session, claim_id: UUID, event_id: UUID) -> ClaimEvent:
    existing = db.scalar(
        select(ClaimEvent).where(
            ClaimEvent.claim_id == claim_id,
            ClaimEvent.event_id == event_id,
        )
    )
    if existing:
        return existing

    link = ClaimEvent(claim_id=claim_id, event_id=event_id)
    db.add(link)
    db.commit()
    db.refresh(link)
    return link


def unlink_event(db: Session, claim_id: UUID, event_id: UUID) -> bool:
    link = db.scalar(
        select(ClaimEvent).where(
            ClaimEvent.claim_id == claim_id,
            ClaimEvent.event_id == event_id,
        )
    )
    if not link:
        return False

    db.delete(link)
    db.commit()
    return True


def get_claim_responses(db: Session, claim_id: UUID):
    stmt = (
        select(ClaimResponse)
        .where(ClaimResponse.claim_id == claim_id)
        .order_by(ClaimResponse.response_date, ClaimResponse.created_at)
    )
    return db.scalars(stmt).all()


def _latest_response_of_type(
    db: Session, claim_id: UUID, response_type: str
) -> ClaimResponse | None:
    stmt = (
        select(ClaimResponse)
        .where(
            ClaimResponse.claim_id == claim_id,
            ClaimResponse.response_type == response_type,
        )
        .order_by(ClaimResponse.response_date.desc())
    )
    return db.scalars(stmt).first()


def submit_notice(
    db: Session, claim_id: UUID, payload: NoticeSubmitRequest
) -> Claim | None:
    claim = db.get(Claim, claim_id)
    if not claim:
        return None

    if payload.notice_evidence_id is not None:
        evidence = db.get(Evidence, payload.notice_evidence_id)
        if evidence is not None:
            # Locking ties the deadline-clock's evidence permanently to
            # this claim - the record a dispute would actually rely on
            # can't quietly be deleted or swapped afterwards.
            evidence.is_locked = True

    claim.notice_submitted_date = payload.notice_submitted_date
    claim.notice_evidence_id = payload.notice_evidence_id
    claim.status = ClaimStatus.NOTIFIED.value

    db.commit()
    db.refresh(claim)
    return claim


def engineer_flag_late_notice(
    db: Session, claim_id: UUID, payload: EngineerLateNoticeFlagRequest
) -> Claim | None:
    claim = db.get(Claim, claim_id)
    if not claim:
        return None

    db.add(
        ClaimResponse(
            claim_id=claim.id,
            response_type=ClaimResponseType.ENGINEER_LATE_NOTICE_FLAG.value,
            response_date=payload.response_date,
            comment=payload.comment,
            responded_by=payload.responded_by,
        )
    )
    claim.status = ClaimStatus.NOTICE_FLAGGED_LATE.value

    db.commit()
    db.refresh(claim)
    return claim


def submit_detailed_claim(
    db: Session, claim_id: UUID, payload: DetailedClaimSubmitRequest
) -> Claim | None:
    claim = db.get(Claim, claim_id)
    if not claim:
        return None

    claim.detailed_claim_submitted_date = payload.detailed_claim_submitted_date
    claim.legal_basis_statement = payload.legal_basis_statement
    claim.particulars = payload.particulars

    if payload.claimed_days is not None:
        claim.claimed_days = payload.claimed_days

    # 20.2.4: a fully detailed claim missing the statement of legal basis
    # is deemed to have lapsed. We don't silently accept it as complete.
    if not payload.legal_basis_statement or not payload.legal_basis_statement.strip():
        claim.status = ClaimStatus.LAPSED.value
    else:
        claim.status = ClaimStatus.AWAITING_ENGINEER_RESPONSE.value

    db.commit()
    db.refresh(claim)
    return claim


_RESPONSE_TYPE_TO_STATUS = {
    ClaimResponseType.AGREEMENT.value: ClaimStatus.AGREED.value,
    ClaimResponseType.PARTIAL_AGREEMENT.value: ClaimStatus.PARTIALLY_AGREED.value,
    ClaimResponseType.DISAGREEMENT.value: ClaimStatus.DETERMINED.value,
    ClaimResponseType.DETERMINATION.value: ClaimStatus.DETERMINED.value,
}


def engineer_respond(
    db: Session, claim_id: UUID, payload: EngineerDecisionRequest
) -> Claim | None:
    claim = db.get(Claim, claim_id)
    if not claim:
        return None

    db.add(
        ClaimResponse(
            claim_id=claim.id,
            response_type=payload.response_type,
            response_date=payload.response_date,
            days_granted=payload.days_granted,
            comment=payload.comment,
            responded_by=payload.responded_by,
        )
    )

    if payload.response_type == ClaimResponseType.REQUEST_FOR_PARTICULARS.value:
        # Doesn't advance the status - the Contractor still owes a
        # (possibly re-submitted) detailed claim.
        pass
    else:
        claim.status = _RESPONSE_TYPE_TO_STATUS.get(
            payload.response_type, ClaimStatus.DETERMINED.value
        )

    db.commit()
    db.refresh(claim)
    return claim


def mark_deemed_rejected_if_overdue(db: Session, claim: Claim) -> Claim:
    """
    Sub-Clause 20.2.5: if the Engineer doesn't respond within the
    response period, that's treated as a rejection the claiming party can
    act on (escalate under Clause 21) rather than the claim disappearing
    into silence. This is called from the clock endpoint rather than a
    background job, since the platform has no scheduler - status is
    brought up to date lazily whenever the claim is viewed.
    """
    if claim.status != ClaimStatus.AWAITING_ENGINEER_RESPONSE.value:
        return claim

    if claim.detailed_claim_submitted_date is None:
        return claim

    project = _get_project(db, claim.project_id)
    config = config_from_project(project)

    from app.services.claim_clock_service import engineer_response_deadline

    deadline = engineer_response_deadline(
        claim.detailed_claim_submitted_date, config
    )

    if get_today() > deadline:
        claim.status = ClaimStatus.DEEMED_REJECTED.value
        db.commit()
        db.refresh(claim)

    return claim
