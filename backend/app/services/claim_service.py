from datetime import date
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.constants.claim_status import ClaimResponseType, ClaimStatus
from app.models.claim import Claim, ClaimDailyLog, ClaimEvent, ClaimEvidence, ClaimResponse
from app.models.daily_log import DailyLog
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
from app.services.claim_clock_service import config_from_project, get_claim_clock, get_today
from app.services.claim_fact_service import get_claim_facts, get_fact_summary
from app.services.event_requirements_service import get_event_requirements
from app.services.event_service import attach_notice_periods

# Response types that represent a substantive Engineer decision (as
# opposed to a procedural note like a late-notice flag or a request for
# particulars) - the ones an "Engineer's Determination" summary panel, or
# a report, should look at.
DECISION_RESPONSE_TYPES = (
    ClaimResponseType.AGREEMENT.value,
    ClaimResponseType.PARTIAL_AGREEMENT.value,
    ClaimResponseType.DISAGREEMENT.value,
    ClaimResponseType.DETERMINATION.value,
)


def _get_project(db: Session, project_id: UUID) -> Project | None:
    return db.get(Project, project_id)


def _next_claim_no(db: Session, project_id: UUID) -> str:
    """
    "CLM-001", "CLM-002", ... scoped per project. Only used when the
    Contractor leaves Claim No. blank - if they type their own reference
    (matching their own correspondence/RFI numbering) that's kept as-is.
    """
    count = db.scalar(
        select(func.count()).select_from(Claim).where(Claim.project_id == project_id)
    )
    return f"CLM-{(count or 0) + 1:03d}"


def create_claim(db: Session, payload: ClaimCreate) -> Claim:
    claim = Claim(
        project_id=payload.project_id,
        claim_no=payload.claim_no or _next_claim_no(db, payload.project_id),
        governing_clause=payload.governing_clause,
        claim_basis=payload.claim_basis,
        claim_type=payload.claim_type,
        claiming_party=payload.claiming_party,
        title=payload.title,
        description=payload.description,
        awareness_date=payload.awareness_date,
        claimed_days=payload.claimed_days,
        claimed_cost_amount=payload.claimed_cost_amount,
        status=ClaimStatus.NOTIFIED.value,
    )

    db.add(claim)
    db.flush()

    for event_id in payload.event_ids:
        db.add(ClaimEvent(claim_id=claim.id, event_id=event_id))

    for daily_log_id in payload.daily_log_ids:
        db.add(ClaimDailyLog(claim_id=claim.id, daily_log_id=daily_log_id))

    for evidence_id in payload.evidence_ids:
        db.add(ClaimEvidence(claim_id=claim.id, evidence_id=evidence_id))

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


def get_claim_daily_logs(db: Session, claim_id: UUID):
    stmt = (
        select(DailyLog)
        .join(ClaimDailyLog, ClaimDailyLog.daily_log_id == DailyLog.id)
        .where(ClaimDailyLog.claim_id == claim_id)
        .order_by(DailyLog.diary_date)
    )
    return db.scalars(stmt).all()


def link_daily_log(db: Session, claim_id: UUID, daily_log_id: UUID) -> ClaimDailyLog:
    existing = db.scalar(
        select(ClaimDailyLog).where(
            ClaimDailyLog.claim_id == claim_id,
            ClaimDailyLog.daily_log_id == daily_log_id,
        )
    )
    if existing:
        return existing

    link = ClaimDailyLog(claim_id=claim_id, daily_log_id=daily_log_id)
    db.add(link)
    db.commit()
    db.refresh(link)
    return link


def unlink_daily_log(db: Session, claim_id: UUID, daily_log_id: UUID) -> bool:
    link = db.scalar(
        select(ClaimDailyLog).where(
            ClaimDailyLog.claim_id == claim_id,
            ClaimDailyLog.daily_log_id == daily_log_id,
        )
    )
    if not link:
        return False

    db.delete(link)
    db.commit()
    return True


def get_claim_evidence(db: Session, claim_id: UUID):
    stmt = (
        select(Evidence)
        .join(ClaimEvidence, ClaimEvidence.evidence_id == Evidence.id)
        .where(ClaimEvidence.claim_id == claim_id)
        .order_by(Evidence.created_at)
    )
    return db.scalars(stmt).all()


def link_evidence(db: Session, claim_id: UUID, evidence_id: UUID) -> ClaimEvidence:
    existing = db.scalar(
        select(ClaimEvidence).where(
            ClaimEvidence.claim_id == claim_id,
            ClaimEvidence.evidence_id == evidence_id,
        )
    )
    if existing:
        return existing

    link = ClaimEvidence(claim_id=claim_id, evidence_id=evidence_id)
    db.add(link)
    db.commit()
    db.refresh(link)

    evidence = db.get(Evidence, evidence_id)
    if evidence is not None:
        # Same "attached to a submitted claim is locked" rule Evidence
        # already follows for notice_evidence_id.
        evidence.is_locked = True
        db.commit()

    return link


def unlink_evidence(db: Session, claim_id: UUID, evidence_id: UUID) -> bool:
    link = db.scalar(
        select(ClaimEvidence).where(
            ClaimEvidence.claim_id == claim_id,
            ClaimEvidence.evidence_id == evidence_id,
        )
    )
    if not link:
        return False

    db.delete(link)
    db.commit()
    return True


def get_claim_requirements(db: Session, claim_id: UUID) -> dict | None:
    """
    Rolls up the required-records checklist (see
    event_requirements_service) across every Event linked to this claim.
    Drives both the New Claim / Claim Detail page's readiness panel and
    the Sub-Clause 20.2.4 submission gate in submit_detailed_claim below.
    """
    claim = db.get(Claim, claim_id)
    if claim is None:
        return None

    events = get_claim_events(db, claim_id)
    event_summaries = []
    for event in events:
        checklist = get_event_requirements(db, event)
        if not checklist:
            continue
        event_summaries.append(
            {
                "event_id": event.id,
                "event_no": event.event_no,
                "title": event.title,
                "checklist": checklist,
                "all_satisfied": all(item["satisfied"] for item in checklist),
            }
        )

    missing_count = sum(
        1
        for summary in event_summaries
        for item in summary["checklist"]
        if not item["satisfied"]
    )

    return {
        "events": event_summaries,
        "all_satisfied": all(s["all_satisfied"] for s in event_summaries),
        "missing_count": missing_count,
    }


def get_engineer_determination(db: Session, claim_id: UUID) -> ClaimResponse | None:
    """Latest substantive decision response - see DECISION_RESPONSE_TYPES."""
    stmt = (
        select(ClaimResponse)
        .where(
            ClaimResponse.claim_id == claim_id,
            ClaimResponse.response_type.in_(DECISION_RESPONSE_TYPES),
        )
        .order_by(ClaimResponse.response_date.desc(), ClaimResponse.created_at.desc())
    )
    return db.scalars(stmt).first()


def get_claim_responses(db: Session, claim_id: UUID):
    stmt = (
        select(ClaimResponse)
        .where(ClaimResponse.claim_id == claim_id)
        .order_by(ClaimResponse.response_date, ClaimResponse.created_at)
    )
    return db.scalars(stmt).all()


def get_claim_report_data(db: Session, claim_id: UUID) -> dict | None:
    """
    Assembles everything the claim report PDF needs to stand alone as a
    document: the claim itself, its owning project's name, the computed
    Sub-Clause 20.2 deadline clock, the linked events, the fact-agreement
    register and its summary, and the full response history.

    Used by both the Contractor's own authenticated download
    (GET /claims/{claim_id}/report/pdf) and the no-account public share
    link (GET /public/claims/{token}/pdf) - deliberately the same
    document either way, since a report that said something different
    depending on who asked for it wouldn't be worth handing to anyone.
    """
    claim = get_claim(db, claim_id)
    if claim is None:
        return None

    project = _get_project(db, claim.project_id)
    config = config_from_project(project)

    responses = get_claim_responses(db, claim.id)
    decision_responses = [
        r for r in responses if r.response_type in DECISION_RESPONSE_TYPES
    ]
    engineer_responded_date = (
        decision_responses[-1].response_date if decision_responses else None
    )

    clock = get_claim_clock(
        awareness_date=claim.awareness_date,
        notice_submitted_date=claim.notice_submitted_date,
        detailed_claim_submitted_date=claim.detailed_claim_submitted_date,
        engineer_responded_date=engineer_responded_date,
        config=config,
    )

    events = attach_notice_periods(db, get_claim_events(db, claim.id))
    facts = get_claim_facts(db, claim.id)
    fact_summary = get_fact_summary(db, claim.id)

    return {
        "claim": claim,
        "project_name": project.project_name if project else None,
        "clock": clock,
        "events": events,
        "facts": facts,
        "fact_summary": fact_summary,
        "responses": responses,
    }


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

    # Required-records gate: don't let a fully detailed claim go in under
    # Sub-Clause 20.2.4 if a linked Event is still missing the records its
    # event_type requires (e.g. an Adverse Weather claim with no Official
    # Weather Data attached yet) - see event_requirements_service. Raised
    # as ValueError so the API layer can surface it as a 409 with the
    # specific missing items, rather than silently accepting an
    # under-evidenced claim.
    requirements = get_claim_requirements(db, claim_id)
    if requirements and not requirements["all_satisfied"]:
        missing = [
            f"{event['event_no'] or event['title']}: {item['label']}"
            for event in requirements["events"]
            for item in event["checklist"]
            if not item["satisfied"]
        ]
        raise ValueError(
            "This claim's linked events are missing required records before "
            "a fully detailed claim can be submitted: " + "; ".join(missing)
        )

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
            cost_awarded_amount=payload.cost_awarded_amount,
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
