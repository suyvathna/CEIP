from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.project import Project
from app.schemas.claim import (
    ClaimClockOut,
    ClaimCreate,
    ClaimEventLinkRequest,
    ClaimOut,
    ClaimResponseOut,
    DetailedClaimSubmitRequest,
    EngineerDecisionRequest,
    EngineerLateNoticeFlagRequest,
    NoticeSubmitRequest,
)
from app.schemas.event import EventResponse
from app.services.claim_clock_service import config_from_project, get_claim_clock
from app.services.claim_service import (
    create_claim,
    engineer_flag_late_notice,
    engineer_respond,
    get_claim,
    get_claim_events,
    get_claim_responses,
    get_project_claims,
    link_event,
    mark_deemed_rejected_if_overdue,
    submit_detailed_claim,
    submit_notice,
    unlink_event,
)
from app.services.event_service import attach_notice_periods

router = APIRouter(prefix="/claims", tags=["Claims"])


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
        r
        for r in responses
        if r.response_type
        in ("Agreement", "PartialAgreement", "Disagreement", "Determination")
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
    claim = submit_detailed_claim(db, claim_id, payload)
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
