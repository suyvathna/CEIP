from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.claim_fact import (
    ClaimFactCreate,
    ClaimFactOut,
    ClaimFactRespond,
    ClaimFactSummaryOut,
)
from app.services.claim_fact_service import (
    create_fact,
    get_claim_facts,
    get_fact,
    get_fact_summary,
    link_evidence,
    respond_to_fact,
)

router = APIRouter(tags=["Claim Facts"])


@router.post("/claims/{claim_id}/facts", response_model=ClaimFactOut)
def create_claim_fact(
    claim_id: UUID, payload: ClaimFactCreate, db: Session = Depends(get_db)
):
    return create_fact(db, claim_id, payload)


@router.get("/claims/{claim_id}/facts", response_model=list[ClaimFactOut])
def list_claim_facts(claim_id: UUID, db: Session = Depends(get_db)):
    return get_claim_facts(db, claim_id)


@router.get("/claims/{claim_id}/facts/summary", response_model=ClaimFactSummaryOut)
def claim_fact_summary(claim_id: UUID, db: Session = Depends(get_db)):
    return get_fact_summary(db, claim_id)


@router.get("/facts/{fact_id}", response_model=ClaimFactOut)
def read_claim_fact(fact_id: UUID, db: Session = Depends(get_db)):
    fact = get_fact(db, fact_id)
    if fact is None:
        raise HTTPException(status_code=404, detail="Fact not found")
    return fact


@router.patch("/facts/{fact_id}", response_model=ClaimFactOut)
def respond_to_claim_fact(
    fact_id: UUID, payload: ClaimFactRespond, db: Session = Depends(get_db)
):
    fact = respond_to_fact(db, fact_id, payload)
    if fact is None:
        raise HTTPException(status_code=404, detail="Fact not found")
    return fact


@router.post("/facts/{fact_id}/evidence/{evidence_id}")
def link_fact_evidence(
    fact_id: UUID, evidence_id: UUID, db: Session = Depends(get_db)
):
    link_evidence(db, fact_id, evidence_id)
    return {"message": "Evidence linked to fact"}
