from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.constants.contract_edition import DEFAULT_EDITION, clause_code
from app.constants.fidic_clauses import DISCLAIMER
from app.constants.variation import DISGUISED_INSTRUCTION_ORIGINS, VariationOrigin
from app.db.session import get_db
from app.models.project import Project
from app.schemas.variation import (
    VariationCreate,
    VariationDetailOut,
    VariationNoticeRequest,
    VariationOriginOptionsOut,
    VariationOut,
    VariationProposalRequest,
    VariationUpdate,
    VariationValuationRequest,
)
from app.services import variation_service

router = APIRouter(
    prefix="/variations",
    tags=["Variations (Clause 13 / Sub-Clause 3.5)"],
)


ORIGIN_LABELS = {
    VariationOrigin.ENGINEER_INSTRUCTION: (
        "Engineer's Instruction, issued as a Variation",
        "The Engineer instructed the change and called it a Variation. "
        "Clause 13 valuation applies and there is no Sub-Clause 3.5 trap.",
    ),
    VariationOrigin.REQUEST_FOR_PROPOSAL: (
        "Engineer's request for a proposal (13.3.2)",
        "The Engineer asked for a proposal before instructing. The "
        "response is due within the period stated in the request.",
    ),
    VariationOrigin.VALUE_ENGINEERING: (
        "Contractor's proposal (13.2 Value Engineering)",
        "The Contractor initiated the change. No instruction clock runs.",
    ),
    VariationOrigin.UNLABELLED_INSTRUCTION: (
        "Instruction that changes the Works but was NOT called a Variation",
        "A letter, site memo, marked-up drawing or minute that changes "
        "the Works without using the word Variation. Sub-Clause 3.5 "
        "requires Notice IMMEDIATELY and BEFORE any related work starts - "
        "this is the one that costs money when it is missed.",
    ),
    VariationOrigin.CONSTRUCTIVE: (
        "Constructive variation - no instruction at all",
        "The Employer or Engineer behaved in a way that varied the Works "
        "without instructing anything. Same immediate-notice requirement "
        "applies, and the evidential burden is heavier - log it and give "
        "Notice straight away.",
    ),
}


@router.get("/origin-options", response_model=VariationOriginOptionsOut)
def read_origin_options(
    project_id: UUID | None = None,
    db: Session = Depends(get_db),
):
    """
    The "how did this change arrive" dropdown, with the Sub-Clause 3.5
    trap spelled out on the two options that trigger it.

    This wording matters more than most reference data on the platform:
    the whole point is that a site engineer logging "the Engineer sent a
    revised drawing" should be able to see, at the moment of logging,
    that this is the category with an immediate notice requirement.
    """
    edition = DEFAULT_EDITION.value

    if project_id is not None:
        project = db.get(Project, project_id)
        if project is not None:
            edition = getattr(project, "contract_edition", None) or edition

    return {
        "clause_code": clause_code("engineers_instructions", edition),
        "disclaimer": DISCLAIMER,
        "options": [
            {
                "value": origin.value,
                "label": label,
                "description": description,
                "triggers_immediate_notice": (
                    origin.value in DISGUISED_INSTRUCTION_ORIGINS
                ),
            }
            for origin, (label, description) in ORIGIN_LABELS.items()
        ],
    }


@router.post("/", response_model=VariationOut)
def create_variation(payload: VariationCreate, db: Session = Depends(get_db)):
    """
    Log a Variation, or an instruction that might be one.

    Logging an unlabelled instruction raises a CRITICAL alert
    immediately, not when a deadline approaches: under Sub-Clause 3.5 the
    real deadline is "before any related work begins", and on a live site
    that can be tomorrow morning.
    """
    return variation_service.create_variation(db, payload)


@router.get("/project/{project_id}", response_model=list[VariationOut])
def list_project_variations(project_id: UUID, db: Session = Depends(get_db)):
    return variation_service.get_project_variations(db, project_id)


@router.get("/{variation_id}", response_model=VariationDetailOut)
def read_variation(variation_id: UUID, db: Session = Depends(get_db)):
    detail = variation_service.get_variation_detail(db, variation_id)

    if detail is None:
        raise HTTPException(status_code=404, detail="Variation not found")

    return detail


@router.put("/{variation_id}", response_model=VariationOut)
def update_variation(
    variation_id: UUID,
    payload: VariationUpdate,
    db: Session = Depends(get_db),
):
    variation = variation_service.update_variation(db, variation_id, payload)

    if variation is None:
        raise HTTPException(status_code=404, detail="Variation not found")

    return variation


@router.patch("/{variation_id}/notice", response_model=VariationOut)
def give_notice(
    variation_id: UUID,
    payload: VariationNoticeRequest,
    db: Session = Depends(get_db),
):
    """
    Record the Sub-Clause 3.5 Notice that the Contractor considers the
    instruction a Variation.

    Accepted whether or not work has already started. It was due before
    commencement, so a Notice given afterwards is late and the clock says
    so - but a late Notice on the record is worth considerably more in a
    later argument than no Notice at all.
    """
    variation = variation_service.give_notice(db, variation_id, payload)

    if variation is None:
        raise HTTPException(status_code=404, detail="Variation not found")

    return variation


@router.patch("/{variation_id}/proposal", response_model=VariationOut)
def submit_proposal(
    variation_id: UUID,
    payload: VariationProposalRequest,
    db: Session = Depends(get_db),
):
    variation = variation_service.submit_proposal(db, variation_id, payload)

    if variation is None:
        raise HTTPException(status_code=404, detail="Variation not found")

    return variation


@router.patch("/{variation_id}/valuation", response_model=VariationOut)
def record_valuation(
    variation_id: UUID,
    payload: VariationValuationRequest,
    db: Session = Depends(get_db),
):
    """
    Record the agreed (or determined) valuation, or mark the Variation
    Disputed where the Engineer refused to treat the instruction as one -
    in which case it becomes a Sub-Clause 20.2 Claim, and the Variation's
    claim_id should be pointed at it.
    """
    variation = variation_service.record_valuation(db, variation_id, payload)

    if variation is None:
        raise HTTPException(status_code=404, detail="Variation not found")

    return variation
