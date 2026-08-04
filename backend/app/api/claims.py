from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.constants.fidic_clauses import DISCLAIMER, FIDIC_CLAUSE_REFERENCE
from app.db.session import get_db
from app.models.project import Project
from app.schemas.claim import (
    ClaimClauseOptionsOut,
    ClaimClockOut,
    ClaimCreate,
    ClaimDailyLogLinkRequest,
    ClaimEventLinkRequest,
    ClaimEvidenceLinkRequest,
    ClaimOut,
    ClaimRequirementsOut,
    ClaimResponseOut,
    DetailedClaimSubmitRequest,
    EngineerDecisionRequest,
    EngineerDeterminationOut,
    EngineerLateNoticeFlagRequest,
    NoticeSubmitRequest,
)
from app.schemas.daily_log import DailyLogResponse
from app.schemas.event import EventResponse
from app.schemas.evidence import EvidenceResponse
from app.services.claim_clock_service import config_from_project, get_claim_clock
from app.services.claim_service import (
    DECISION_RESPONSE_TYPES,
    create_claim,
    engineer_flag_late_notice,
    engineer_respond,
    get_claim,
    get_claim_daily_logs,
    get_claim_events,
    get_claim_evidence,
    get_claim_report_data,
    get_claim_requirements,
    get_claim_responses,
    get_engineer_determination,
    get_project_claims,
    link_daily_log,
    link_event,
    link_evidence,
    mark_deemed_rejected_if_overdue,
    submit_detailed_claim,
    submit_notice,
    unlink_daily_log,
    unlink_event,
    unlink_evidence,
)
from app.services.daily_log_service import hydrate_daily_logs
from app.services.event_service import attach_notice_periods
from app.services.pdf_service import generate_claim_report_pdf

router = APIRouter(prefix="/claims", tags=["Claims"])


@router.get("/clause-options", response_model=ClaimClauseOptionsOut)
def read_clause_options():
    """
    The "Applicable Governing Clause" dropdown's option list - every
    EventType that maps to a specific, citable FIDIC Red Book 2017
    Sub-Clause (see app.constants.fidic_clauses) - plus the disclaimer
    that must be surfaced alongside it. Static reference data, not
    project-specific, so it's safe to cache client-side for the session.
    """
    return {
        "disclaimer": DISCLAIMER,
        "options": [
            {"event_type": event_type.value, **info}
            for event_type, info in FIDIC_CLAUSE_REFERENCE.items()
        ],
    }


@router.post("/", response_model=ClaimOut)
def create_claim_endpoint(payload: ClaimCreate, db: Session = Depends(get_db)):
    return create_claim(db, payload)


@router.get("/project/{project_id}", response_model=list[ClaimOut])
def list_project_claims(project_id: UUID, db: Session = Depends(get_db)):
    claims = get_project_claims(db, project_id)
    for claim in claims:
        mark_deemed_rejected_if_overdue(db, claim)
    return claims


@router.get("/{claim_id}", response_model=ClaimOut)
def read_claim(claim_id: UUID, db: Session = Depends(get_db)):
    claim = get_claim(db, claim_id)
    if claim is None:
        raise HTTPException(status_code=404, detail="Claim not found")
    return mark_deemed_rejected_if_overdue(db, claim)


@router.get("/{claim_id}/events", response_model=list[EventResponse])
def read_claim_events(claim_id: UUID, db: Session = Depends(get_db)):
    return attach_notice_periods(db, get_claim_events(db, claim_id))


@router.post("/{claim_id}/events", response_model=EventResponse)
def link_claim_event(
    claim_id: UUID,
    payload: ClaimEventLinkRequest,
    db: Session = Depends(get_db),
):
    link_event(db, claim_id, payload.event_id)
    events = get_claim_events(db, claim_id)
    matching = next((e for e in events if e.id == payload.event_id), None)
    if matching is None:
        raise HTTPException(status_code=404, detail="Event not found")
    return attach_notice_periods(db, matching)


@router.delete("/{claim_id}/events/{event_id}")
def unlink_claim_event(claim_id: UUID, event_id: UUID, db: Session = Depends(get_db)):
    removed = unlink_event(db, claim_id, event_id)
    if not removed:
        raise HTTPException(status_code=404, detail="Link not found")
    return {"message": "Event unlinked from claim"}


@router.get("/{claim_id}/daily-logs", response_model=list[DailyLogResponse])
def read_claim_daily_logs(claim_id: UUID, db: Session = Depends(get_db)):
    return hydrate_daily_logs(db, get_claim_daily_logs(db, claim_id))


@router.post("/{claim_id}/daily-logs", response_model=list[DailyLogResponse])
def link_claim_daily_log(
    claim_id: UUID,
    payload: ClaimDailyLogLinkRequest,
    db: Session = Depends(get_db),
):
    link_daily_log(db, claim_id, payload.daily_log_id)
    return hydrate_daily_logs(db, get_claim_daily_logs(db, claim_id))


@router.delete("/{claim_id}/daily-logs/{daily_log_id}")
def unlink_claim_daily_log(
    claim_id: UUID, daily_log_id: UUID, db: Session = Depends(get_db)
):
    removed = unlink_daily_log(db, claim_id, daily_log_id)
    if not removed:
        raise HTTPException(status_code=404, detail="Link not found")
    return {"message": "Daily Log unlinked from claim"}


@router.get("/{claim_id}/evidence", response_model=list[EvidenceResponse])
def read_claim_evidence(claim_id: UUID, db: Session = Depends(get_db)):
    return get_claim_evidence(db, claim_id)


@router.post("/{claim_id}/evidence", response_model=list[EvidenceResponse])
def link_claim_evidence(
    claim_id: UUID,
    payload: ClaimEvidenceLinkRequest,
    db: Session = Depends(get_db),
):
    link_evidence(db, claim_id, payload.evidence_id)
    return get_claim_evidence(db, claim_id)


@router.delete("/{claim_id}/evidence/{evidence_id}")
def unlink_claim_evidence(
    claim_id: UUID, evidence_id: UUID, db: Session = Depends(get_db)
):
    removed = unlink_evidence(db, claim_id, evidence_id)
    if not removed:
        raise HTTPException(status_code=404, detail="Link not found")
    return {"message": "Evidence unlinked from claim"}


@router.get("/{claim_id}/requirements", response_model=ClaimRequirementsOut)
def read_claim_requirements(claim_id: UUID, db: Session = Depends(get_db)):
    """
    Rolled-up required-records checklist across every Event linked to
    this claim - what the Claim Detail page shows as the claim's
    "readiness" state, and what submit_detailed_claim enforces before a
    fully detailed claim can go in.
    """
    requirements = get_claim_requirements(db, claim_id)
    if requirements is None:
        raise HTTPException(status_code=404, detail="Claim not found")
    return requirements


@router.get("/{claim_id}/engineer-determination", response_model=EngineerDeterminationOut | None)
def read_engineer_determination(claim_id: UUID, db: Session = Depends(get_db)):
    """
    The claim's latest substantive Engineer decision (Agreement, Partial
    Agreement, Disagreement, or Determination) - response_date,
    eot_awarded_days, cost_awarded_amount, and the Engineer's comment -
    for the Claim Detail page's Engineer's Determination summary. Returns
    null (not 404) if the Engineer hasn't issued a decision yet - that's
    an expected, common state, not an error.
    """
    claim = get_claim(db, claim_id)
    if claim is None:
        raise HTTPException(status_code=404, detail="Claim not found")

    response = get_engineer_determination(db, claim_id)
    if response is None:
        return None

    return {
        "response_date": response.response_date,
        "eot_awarded_days": response.days_granted,
        "cost_awarded_amount": response.cost_awarded_amount,
        "comment": response.comment,
        "responded_by": response.responded_by,
        "response_type": response.response_type,
    }


@router.get("/{claim_id}/clock", response_model=ClaimClockOut)
def read_claim_clock(claim_id: UUID, db: Session = Depends(get_db)):
    claim = get_claim(db, claim_id)
    if claim is None:
        raise HTTPException(status_code=404, detail="Claim not found")

    claim = mark_deemed_rejected_if_overdue(db, claim)
    project = db.get(Project, claim.project_id)
    config = config_from_project(project)

    engineer_responded_date = None
    responses = get_claim_responses(db, claim_id)
    decision_responses = [
        r for r in responses if r.response_type in DECISION_RESPONSE_TYPES
    ]
    if decision_responses:
        engineer_responded_date = decision_responses[-1].response_date

    return get_claim_clock(
        awareness_date=claim.awareness_date,
        notice_submitted_date=claim.notice_submitted_date,
        detailed_claim_submitted_date=claim.detailed_claim_submitted_date,
        engineer_responded_date=engineer_responded_date,
        config=config,
    )


@router.patch("/{claim_id}/notice", response_model=ClaimOut)
def submit_notice_endpoint(
    claim_id: UUID, payload: NoticeSubmitRequest, db: Session = Depends(get_db)
):
    claim = submit_notice(db, claim_id, payload)
    if claim is None:
        raise HTTPException(status_code=404, detail="Claim not found")
    return claim


@router.patch("/{claim_id}/engineer-flag", response_model=ClaimOut)
def engineer_flag_endpoint(
    claim_id: UUID,
    payload: EngineerLateNoticeFlagRequest,
    db: Session = Depends(get_db),
):
    claim = engineer_flag_late_notice(db, claim_id, payload)
    if claim is None:
        raise HTTPException(status_code=404, detail="Claim not found")
    return claim


@router.patch("/{claim_id}/detailed-claim", response_model=ClaimOut)
def submit_detailed_claim_endpoint(
    claim_id: UUID,
    payload: DetailedClaimSubmitRequest,
    db: Session = Depends(get_db),
):
    try:
        claim = submit_detailed_claim(db, claim_id, payload)
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))

    if claim is None:
        raise HTTPException(status_code=404, detail="Claim not found")
    return claim


@router.patch("/{claim_id}/engineer-response", response_model=ClaimOut)
def engineer_response_endpoint(
    claim_id: UUID,
    payload: EngineerDecisionRequest,
    db: Session = Depends(get_db),
):
    claim = engineer_respond(db, claim_id, payload)
    if claim is None:
        raise HTTPException(status_code=404, detail="Claim not found")
    return claim


@router.get("/{claim_id}/responses", response_model=list[ClaimResponseOut])
def read_claim_responses(claim_id: UUID, db: Session = Depends(get_db)):
    return get_claim_responses(db, claim_id)


@router.get("/{claim_id}/report/pdf")
def claim_report_pdf_endpoint(claim_id: UUID, db: Session = Depends(get_db)):
    """
    The Contractor's own direct download of this claim as a PDF - the
    same document a share link (see api/claim_access.py) would hand the
    Engineer, generated here without needing to create a link first, for
    printing or attaching to an email/Telegram message by hand.
    """
    data = get_claim_report_data(db, claim_id)
    if data is None:
        raise HTTPException(status_code=404, detail="Claim not found")

    pdf = generate_claim_report_pdf(data)

    return StreamingResponse(
        pdf,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'inline; filename="claim_report_{claim_id}.pdf"'
        },
    )
