from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.project import Project
from app.schemas.claim_access import (
    ClaimAccessTokenCreate,
    ClaimAccessTokenOut,
    PublicEngineerDecisionRequest,
    PublicFactResponseRequest,
)
from app.schemas.claim_fact import ClaimFactRespond
from app.services.claim_access_service import create_access_token, resolve_access_token
from app.services.claim_clock_service import config_from_project, get_claim_clock
from app.services.claim_fact_service import get_claim_facts, get_fact_summary, respond_to_fact
from app.services.claim_service import (
    engineer_respond,
    get_claim,
    get_claim_events,
    get_claim_responses,
)
from app.services.event_service import attach_notice_periods
from app.schemas.claim import ClaimOut, ClaimResponseOut, EngineerDecisionRequest
from app.schemas.claim_fact import ClaimFactOut, ClaimFactSummaryOut
from app.schemas.event import EventResponse

router = APIRouter(prefix="/claims", tags=["Claim Access Links"])
public_router = APIRouter(prefix="/public/claims", tags=["Public Claim Access"])


@router.post("/{claim_id}/access-links", response_model=ClaimAccessTokenOut)
def create_claim_access_link(
    claim_id: UUID, payload: ClaimAccessTokenCreate, db: Session = Depends(get_db)
):
    """
    Generates a magic link the Contractor can send to the Engineer
    directly (email or otherwise) - there's no email-sending service
    wired up in this platform yet, so the link itself is returned here
    rather than dispatched automatically.
    """
    claim = get_claim(db, claim_id)
    if claim is None:
        raise HTTPException(status_code=404, detail="Claim not found")

    return create_access_token(
        db, claim_id, payload.recipient_email, payload.ttl_days
    )


def _resolve_or_404(db: Session, token: str):
    access = resolve_access_token(db, token)
    if access is None:
        raise HTTPException(
            status_code=404,
            detail="This link is invalid or has expired. Ask the Contractor "
            "for a new one.",
        )
    return access


@public_router.get("/{token}")
def public_claim_overview(token: str, db: Session = Depends(get_db)):
    access = _resolve_or_404(db, token)

    claim = get_claim(db, access.claim_id)
    if claim is None:
        raise HTTPException(status_code=404, detail="Claim not found")

    project = db.get(Project, claim.project_id)
    config = config_from_project(project)

    responses = get_claim_responses(db, claim.id)
    decision_responses = [
        r
        for r in responses
        if r.response_type
        in ("Agreement", "PartialAgreement", "Disagreement", "Determination")
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

    # Built from explicit schema conversions rather than returning raw
    # ORM objects: this endpoint has no response_model (the payload mixes
    # several different shapes), so without this the SQLAlchemy instances
    # below wouldn't serialize cleanly through FastAPI's JSON encoder.
    return {
        "claim": ClaimOut.model_validate(claim),
        "project_name": project.project_name if project else None,
        "clock": clock,
        "events": [EventResponse.model_validate(e) for e in events],
        "facts": [ClaimFactOut.model_validate(f) for f in facts],
        "fact_summary": ClaimFactSummaryOut(**get_fact_summary(db, claim.id)),
        "responses": [ClaimResponseOut.model_validate(r) for r in responses],
        "recipient_email": access.recipient_email,
    }


@public_router.patch("/{token}/facts/{fact_id}", response_model=ClaimFactOut)
def public_respond_to_fact(
    token: str,
    fact_id: UUID,
    payload: PublicFactResponseRequest,
    db: Session = Depends(get_db),
):
    access = _resolve_or_404(db, token)

    fact = respond_to_fact(
        db,
        fact_id,
        ClaimFactRespond(
            status=payload.status,
            agreed_days=payload.agreed_days,
            response_comment=payload.response_comment,
            responded_by=access.recipient_email,
        ),
    )
    if fact is None:
        raise HTTPException(status_code=404, detail="Fact not found")

    return fact


@public_router.patch("/{token}/response", response_model=ClaimOut)
def public_engineer_response(
    token: str,
    payload: PublicEngineerDecisionRequest,
    db: Session = Depends(get_db),
):
    access = _resolve_or_404(db, token)

    claim = engineer_respond(
        db,
        access.claim_id,
        EngineerDecisionRequest(
            response_type=payload.response_type,
            response_date=payload.response_date,
            days_granted=payload.days_granted,
            comment=payload.comment,
            responded_by=access.recipient_email,
        ),
    )
    if claim is None:
        raise HTTPException(status_code=404, detail="Claim not found")

    return claim
