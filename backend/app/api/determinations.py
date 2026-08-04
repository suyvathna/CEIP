from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.determination import (
    AgreementRequest,
    DeterminationCreate,
    DeterminationDetailOut,
    DeterminationOut,
    DeterminationReceivedRequest,
    DeterminationUpdate,
    NoticeOfDissatisfactionRequest,
)
from app.services import determination_service

router = APIRouter(
    prefix="/determinations",
    tags=["Determinations (Sub-Clause 3.7)"],
)


@router.post("/", response_model=DeterminationOut)
def create_determination(
    payload: DeterminationCreate,
    db: Session = Depends(get_db),
):
    """
    Open a Sub-Clause 3.7 matter.

    claim_id is optional because 3.7 governs "any matter or Claim" - an
    Engineer determines valuations, measurement disputes and rate
    adjustments that never became a Sub-Clause 20.2 Claim, and each of
    those still opens its own 28-day Notice of Dissatisfaction window.
    Determinations arising from a claim are opened automatically by
    Engine B when the fully detailed claim goes in; this endpoint is for
    the standalone ones.
    """
    return determination_service.create_determination(db, payload)


@router.get("/project/{project_id}", response_model=list[DeterminationOut])
def list_project_determinations(project_id: UUID, db: Session = Depends(get_db)):
    return determination_service.get_project_determinations(db, project_id)


@router.get("/claim/{claim_id}", response_model=DeterminationDetailOut | None)
def read_claim_determination(claim_id: UUID, db: Session = Depends(get_db)):
    """The Sub-Clause 3.7 record attached to a claim, for the claim
    detail screen's determination panel. Returns null where the claim
    hasn't reached 3.7 yet."""
    determination = determination_service.get_claim_determination(db, claim_id)

    if determination is None:
        return None

    return determination_service.get_determination_detail(db, determination.id)


@router.get("/{determination_id}", response_model=DeterminationDetailOut)
def read_determination(determination_id: UUID, db: Session = Depends(get_db)):
    detail = determination_service.get_determination_detail(db, determination_id)

    if detail is None:
        raise HTTPException(status_code=404, detail="Determination not found")

    return detail


@router.put("/{determination_id}", response_model=DeterminationOut)
def update_determination(
    determination_id: UUID,
    payload: DeterminationUpdate,
    db: Session = Depends(get_db),
):
    determination = determination_service.update_determination(
        db, determination_id, payload
    )

    if determination is None:
        raise HTTPException(status_code=404, detail="Determination not found")

    return determination


@router.patch("/{determination_id}/agreement", response_model=DeterminationOut)
def record_agreement(
    determination_id: UUID,
    payload: AgreementRequest,
    db: Session = Depends(get_db),
):
    """
    Sub-Clause 3.7.2: the Parties agreed. Binding, and no Notice of
    Dissatisfaction window ever opens - recording it here is what stops
    the platform watching for a NOD that will never be due.
    """
    determination = determination_service.record_agreement(
        db,
        determination_id,
        agreement_reached_date=payload.agreement_reached_date,
        summary=payload.summary,
    )

    if determination is None:
        raise HTTPException(status_code=404, detail="Determination not found")

    return determination


@router.patch("/{determination_id}/received", response_model=DeterminationOut)
def record_determination_received(
    determination_id: UUID,
    payload: DeterminationReceivedRequest,
    db: Session = Depends(get_db),
):
    """
    Record the Engineer's Notice of determination.

    Two dates, and they are not interchangeable: the date on the letter,
    and the date it actually reached the Contractor. The 28-day
    Sub-Clause 3.7.5 clock runs from RECEIPT. On a job where the Notice
    is dated the 1st and lands on the 9th, running it from the letter
    date silently costs eight of the twenty-eight days - with no relief
    afterwards, because the determination is final and binding the moment
    the window shuts.
    """
    determination = determination_service.record_determination_received(
        db, determination_id, payload
    )

    if determination is None:
        raise HTTPException(status_code=404, detail="Determination not found")

    return determination


@router.patch("/{determination_id}/nod", response_model=DeterminationOut)
def give_notice_of_dissatisfaction(
    determination_id: UUID,
    payload: NoticeOfDissatisfactionRequest,
    db: Session = Depends(get_db),
):
    """
    Give a Notice of Dissatisfaction under Sub-Clause 3.7.5.

    Accepted even if it is late. A NOD on day 30 is worthless
    contractually, but the record needs to be honest - the clock decides
    whether it was in time, not whether the platform let you type it in.
    """
    determination = determination_service.give_notice_of_dissatisfaction(
        db, determination_id, payload
    )

    if determination is None:
        raise HTTPException(status_code=404, detail="Determination not found")

    return determination
