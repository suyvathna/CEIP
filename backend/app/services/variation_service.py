"""
CRUD and workflow for Clause 13 Variations and the Sub-Clause 3.5
instructions that might become one.

Same shape as determination_service: record dated facts, then let
contract_engine (Engine B) decide what the contract has just started
running.
"""

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.constants.contract_triggers import TriggerType
from app.constants.variation import (
    DISGUISED_INSTRUCTION_ORIGINS,
    VARIATION_CLOSED_STATUSES,
    VariationOrigin,
    VariationStatus,
)
from app.models.evidence import Evidence
from app.models.project import Project
from app.models.variation import Variation
from app.schemas.variation import (
    VariationCreate,
    VariationNoticeRequest,
    VariationProposalRequest,
    VariationUpdate,
    VariationValuationRequest,
)
from app.services import contract_engine, notification_service
from app.services.claim_clock_service import config_from_project, get_variation_clock


def next_variation_no(db: Session, project_id: UUID) -> str:
    """"VO-001", "VO-002", ... per project - mirrors Claim._next_claim_no
    and Event._next_event_no so it can be cited in correspondence."""
    count = db.scalar(
        select(func.count())
        .select_from(Variation)
        .where(Variation.project_id == project_id)
    )
    return f"VO-{(count or 0) + 1:03d}"


def _project(db: Session, project_id: UUID) -> Project | None:
    return db.get(Project, project_id)


def create_variation(db: Session, payload: VariationCreate) -> Variation:
    """
    Log an instruction or a Variation.

    is_labelled_as_variation is forced to False for the origins that mean
    "an instruction that changes the Works but never said Variation" -
    the flag and the origin cannot be allowed to disagree, because the
    whole Sub-Clause 3.5 alarm hangs off them.
    """
    origin = payload.origin.value
    labelled = payload.is_labelled_as_variation

    if origin in DISGUISED_INSTRUCTION_ORIGINS:
        labelled = False
    elif origin == VariationOrigin.ENGINEER_INSTRUCTION.value:
        labelled = True

    variation = Variation(
        project_id=payload.project_id,
        variation_no=payload.variation_no or next_variation_no(db, payload.project_id),
        title=payload.title,
        description=payload.description,
        origin=origin,
        status=VariationStatus.LOGGED.value,
        instruction_reference=payload.instruction_reference,
        instruction_date=payload.instruction_date,
        instruction_received_date=payload.instruction_received_date
        or payload.instruction_date,
        is_labelled_as_variation=labelled,
        work_commenced=payload.work_commenced,
        work_commenced_date=payload.work_commenced_date,
        proposal_requested_date=payload.proposal_requested_date,
        event_id=payload.event_id,
        claim_id=payload.claim_id,
    )

    db.add(variation)
    db.flush()

    contract_engine.dispatch(
        db,
        TriggerType.VARIATION_LOGGED,
        variation_id=variation.id,
        project_id=variation.project_id,
    )

    db.commit()
    db.refresh(variation)
    return variation


def get_variation(db: Session, variation_id: UUID) -> Variation | None:
    return db.get(Variation, variation_id)


def get_project_variations(db: Session, project_id: UUID):
    return list(
        db.scalars(
            select(Variation)
            .where(Variation.project_id == project_id)
            .order_by(Variation.created_at.desc())
        ).all()
    )


def get_clock(db: Session, variation: Variation) -> dict:
    project = _project(db, variation.project_id)
    config = config_from_project(project)

    return get_variation_clock(
        instruction_received_date=variation.instruction_received_date,
        is_labelled_as_variation=variation.is_labelled_as_variation,
        notice_given_date=variation.notice_given_date,
        work_commenced=variation.work_commenced,
        work_commenced_date=variation.work_commenced_date,
        proposal_requested_date=variation.proposal_requested_date,
        proposal_submitted_date=variation.proposal_submitted_date,
        config=config,
    )


def update_variation(
    db: Session, variation_id: UUID, payload: VariationUpdate
) -> Variation | None:
    variation = db.get(Variation, variation_id)
    if variation is None:
        return None

    data = payload.model_dump(exclude_unset=True)

    if "origin" in data and data["origin"] is not None:
        data["origin"] = (
            data["origin"].value
            if hasattr(data["origin"], "value")
            else data["origin"]
        )
        if data["origin"] in DISGUISED_INSTRUCTION_ORIGINS:
            data["is_labelled_as_variation"] = False

    if "status" in data and data["status"] is not None:
        data["status"] = (
            data["status"].value
            if hasattr(data["status"], "value")
            else data["status"]
        )

    for field, value in data.items():
        setattr(variation, field, value)

    contract_engine.advance_variation(variation, get_clock(db, variation))

    db.commit()
    db.refresh(variation)
    return variation


def give_notice(
    db: Session, variation_id: UUID, payload: VariationNoticeRequest
) -> Variation | None:
    """
    Record the Sub-Clause 3.5 Notice that the Contractor considers the
    instruction a Variation.

    Accepted regardless of whether work has already started. Under 3.5
    the Notice was due before commencement, so a Notice given afterwards
    is late and the clock will say so - but a late Notice on the record
    is worth considerably more in a later argument than no Notice at all,
    and refusing the entry would only push the Contractor into pretending
    it never happened.
    """
    variation = db.get(Variation, variation_id)
    if variation is None:
        return None

    variation.notice_given_date = payload.notice_given_date
    variation.notice_reference = payload.notice_reference

    if payload.notice_evidence_id is not None:
        variation.notice_evidence_id = payload.notice_evidence_id
        evidence = db.get(Evidence, payload.notice_evidence_id)
        if evidence is not None:
            # Same rule as a Notice of Claim's evidence: once a document
            # is the proof a contractual deadline was met, it stops being
            # deletable.
            evidence.is_locked = True

    variation.status = VariationStatus.NOTICE_GIVEN.value

    notification_service.resolve_source(
        db,
        source_type="variation",
        source_id=variation.id,
        stage="deemed_variation_notice",
        reason="Sub-Clause 3.5 Notice recorded",
    )

    db.flush()

    contract_engine.dispatch(
        db,
        TriggerType.VARIATION_NOTICE_GIVEN,
        variation_id=variation.id,
        project_id=variation.project_id,
    )

    db.commit()
    db.refresh(variation)
    return variation


def submit_proposal(
    db: Session, variation_id: UUID, payload: VariationProposalRequest
) -> Variation | None:
    variation = db.get(Variation, variation_id)
    if variation is None:
        return None

    variation.proposal_submitted_date = payload.proposal_submitted_date
    variation.quoted_days = payload.quoted_days
    variation.quoted_cost = payload.quoted_cost
    variation.status = VariationStatus.PROPOSAL_SUBMITTED.value
    db.flush()

    contract_engine.dispatch(
        db,
        TriggerType.VARIATION_PROPOSAL_SUBMITTED,
        variation_id=variation.id,
        project_id=variation.project_id,
    )

    db.commit()
    db.refresh(variation)
    return variation


def record_valuation(
    db: Session, variation_id: UUID, payload: VariationValuationRequest
) -> Variation | None:
    variation = db.get(Variation, variation_id)
    if variation is None:
        return None

    variation.agreed_days = payload.agreed_days
    variation.agreed_cost = payload.agreed_cost
    variation.status = payload.status.value

    if variation.status in VARIATION_CLOSED_STATUSES:
        notification_service.resolve_source(
            db,
            source_type="variation",
            source_id=variation.id,
            reason=f"Variation closed ({variation.status})",
        )

    db.commit()
    db.refresh(variation)
    return variation


def get_variation_detail(db: Session, variation_id: UUID) -> dict | None:
    variation = db.get(Variation, variation_id)
    if variation is None:
        return None

    project = _project(db, variation.project_id)
    clock = get_clock(db, variation)

    return {
        "variation": variation,
        "clock": clock,
        "contract_edition": getattr(project, "contract_edition", None),
    }
