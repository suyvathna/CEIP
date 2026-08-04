"""
CRUD and workflow for FIDIC Sub-Clause 3.7 matters.

Thin by design: every state transition lives in contract_engine
(Engine B), and this module's job is to record dated facts and then tell
the engine something happened. That split is what keeps the contractual
logic in one readable place instead of smeared across the API layer.
"""

from datetime import date
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.constants.contract_triggers import TriggerType
from app.constants.determination import DeterminationOutcome, DeterminationStatus
from app.models.claim import Claim
from app.models.determination import Determination
from app.models.evidence import Evidence
from app.models.project import Project
from app.schemas.determination import (
    DeterminationCreate,
    DeterminationReceivedRequest,
    DeterminationUpdate,
    NoticeOfDissatisfactionRequest,
)
from app.services import contract_engine, notification_service
from app.services.claim_clock_service import (
    config_from_project,
    get_determination_clock,
    get_today,
)
from app.services.contract_engine import next_determination_no


def _project(db: Session, project_id: UUID) -> Project | None:
    return db.get(Project, project_id)


def create_determination(
    db: Session, payload: DeterminationCreate
) -> Determination:
    determination = Determination(
        project_id=payload.project_id,
        claim_id=payload.claim_id,
        determination_no=payload.determination_no
        or next_determination_no(db, payload.project_id),
        matter_title=payload.matter_title,
        matter_description=payload.matter_description,
        subject_clause=payload.subject_clause,
        referred_date=payload.referred_date,
        status=DeterminationStatus.UNDER_CONSULTATION.value,
        outcome=DeterminationOutcome.NOT_YET_DETERMINED.value,
    )

    db.add(determination)
    db.flush()

    contract_engine.dispatch(
        db,
        TriggerType.MATTER_REFERRED,
        determination_id=determination.id,
        project_id=determination.project_id,
    )

    db.commit()
    db.refresh(determination)
    return determination


def get_determination(db: Session, determination_id: UUID) -> Determination | None:
    return db.get(Determination, determination_id)


def get_project_determinations(db: Session, project_id: UUID):
    return list(
        db.scalars(
            select(Determination)
            .where(Determination.project_id == project_id)
            .order_by(Determination.referred_date.desc())
        ).all()
    )


def get_claim_determination(db: Session, claim_id: UUID) -> Determination | None:
    return db.scalar(
        select(Determination)
        .where(Determination.claim_id == claim_id)
        .order_by(Determination.created_at.desc())
    )


def get_clock(db: Session, determination: Determination) -> dict:
    project = _project(db, determination.project_id)
    config = config_from_project(project)

    return get_determination_clock(
        referred_date=determination.referred_date,
        agreement_reached_date=determination.agreement_reached_date,
        determination_notice_date=determination.determination_notice_date,
        determination_received_date=determination.determination_received_date,
        nod_given_date=determination.nod_given_date,
        config=config,
    )


def update_determination(
    db: Session, determination_id: UUID, payload: DeterminationUpdate
) -> Determination | None:
    determination = db.get(Determination, determination_id)
    if determination is None:
        return None

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(determination, field, value)

    project = _project(db, determination.project_id)
    contract_engine.advance_determination(
        db, determination, config_from_project(project), get_today()
    )

    db.commit()
    db.refresh(determination)
    return determination


def record_agreement(
    db: Session,
    determination_id: UUID,
    *,
    agreement_reached_date: date,
    summary: str | None = None,
) -> Determination | None:
    """
    Sub-Clause 3.7.2: the Parties agreed. That agreement is binding, and
    no Notice of Dissatisfaction window ever opens - which is exactly why
    it has to be recorded as its own action rather than typed into a
    status field, so the platform stops watching for a NOD that will
    never be due.
    """
    determination = db.get(Determination, determination_id)
    if determination is None:
        return None

    determination.agreement_reached_date = agreement_reached_date
    determination.determination_summary = summary or determination.determination_summary
    determination.status = DeterminationStatus.AGREED.value
    determination.outcome = DeterminationOutcome.FULLY_IN_FAVOUR.value

    # An agreement under 3.7.2 is binding and no NOD window will ever
    # open, so every standing alert on this matter is spent.
    notification_service.resolve_source(
        db,
        source_type="determination",
        source_id=determination.id,
        reason="Agreed under Sub-Clause 3.7.2 - binding",
    )

    db.commit()
    db.refresh(determination)
    return determination


def record_determination_received(
    db: Session,
    determination_id: UUID,
    payload: DeterminationReceivedRequest,
) -> Determination | None:
    """
    The Engineer's Notice of determination arrived.

    Two separate dates are captured and they are not interchangeable.
    determination_notice_date is what the letter says; received_date is
    when it actually reached the Contractor, and the 28-day Sub-Clause
    3.7.5 clock runs from THAT. On a job where the Engineer's Notice is
    dated the 1st and lands on the 9th, running the clock from the letter
    date quietly costs eight of the twenty-eight days - and there is no
    relief afterwards, because the determination is final and binding the
    moment the window shuts.
    """
    determination = db.get(Determination, determination_id)
    if determination is None:
        return None

    determination.determination_notice_date = payload.determination_notice_date
    determination.determination_received_date = payload.determination_received_date
    determination.determination_summary = payload.determination_summary
    determination.outcome = payload.outcome.value
    determination.days_determined = payload.days_determined
    determination.cost_determined = payload.cost_determined

    if payload.determination_evidence_id is not None:
        determination.determination_evidence_id = payload.determination_evidence_id
        evidence = db.get(Evidence, payload.determination_evidence_id)
        if evidence is not None:
            evidence.is_locked = True

    determination.status = DeterminationStatus.DETERMINED_NOD_OPEN.value
    db.flush()

    contract_engine.dispatch(
        db,
        TriggerType.DETERMINATION_RECEIVED,
        determination_id=determination.id,
        project_id=determination.project_id,
    )

    db.commit()
    db.refresh(determination)
    return determination


def give_notice_of_dissatisfaction(
    db: Session,
    determination_id: UUID,
    payload: NoticeOfDissatisfactionRequest,
) -> Determination | None:
    """
    Sub-Clause 3.7.5 Notice of Dissatisfaction.

    Recorded even when it is late. A NOD given on day 30 is worthless
    contractually, but pretending it never happened would leave the
    record dishonest, and the "given late" state is exactly what a
    post-mortem needs to see. Whether it was in time is decided by the
    clock, not by whether the platform accepted the entry.
    """
    determination = db.get(Determination, determination_id)
    if determination is None:
        return None

    determination.nod_given_date = payload.nod_given_date
    determination.nod_reference = payload.nod_reference
    determination.nod_grounds = payload.nod_grounds

    if payload.nod_evidence_id is not None:
        determination.nod_evidence_id = payload.nod_evidence_id
        evidence = db.get(Evidence, payload.nod_evidence_id)
        if evidence is not None:
            evidence.is_locked = True

    determination.status = DeterminationStatus.NOD_GIVEN.value
    determination.is_final_and_binding = False
    determination.became_final_on = None

    # The countdown is over - retire it now rather than at 06:00
    # tomorrow, so the badge drops while the PM is still looking at it.
    notification_service.resolve_source(
        db,
        source_type="determination",
        source_id=determination.id,
        stage="notice_of_dissatisfaction",
        reason="Notice of Dissatisfaction given",
    )

    db.flush()

    contract_engine.dispatch(
        db,
        TriggerType.NOD_GIVEN,
        determination_id=determination.id,
        project_id=determination.project_id,
    )

    db.commit()
    db.refresh(determination)
    return determination


def get_determination_detail(db: Session, determination_id: UUID) -> dict | None:
    """Everything the determination screen needs in one round trip."""
    determination = db.get(Determination, determination_id)
    if determination is None:
        return None

    claim = db.get(Claim, determination.claim_id) if determination.claim_id else None

    return {
        "determination": determination,
        "clock": get_clock(db, determination),
        "claim_no": claim.claim_no if claim else None,
        "claim_title": claim.title if claim else None,
    }
