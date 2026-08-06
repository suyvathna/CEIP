from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.constants.compliance import ObligationCategory, ObligationStatus
from app.constants.compliance_rules import (
    COMPLIANCE_DISCLAIMER,
    COMPLIANCE_RULES,
    resolve_clause_code,
)
from app.constants.contract_edition import DEFAULT_EDITION, clause_code
from app.constants.event_driven_rules import EVENT_DRIVEN_DISCLAIMER, EVENT_DRIVEN_RULES
from app.db.session import get_db
from app.models.project import Project
from app.schemas.compliance import (
    ComplianceRegisterOut,
    ComplianceRulesOut,
    ComplianceRunOut,
    EventDrivenRulesOut,
    ObligationOut,
    ObligationStatusOut,
    ObligationSubmitRequest,
    ObligationWaiveRequest,
    RegenerateResultOut,
)
from app.schemas.deadlines import DeadlineFeedOut
from app.services import compliance_service
from app.services.deadline_feed_service import get_deadline_feed

router = APIRouter(prefix="/compliance", tags=["Compliance (Engine A)"])


@router.get("/rules", response_model=ComplianceRulesOut)
def read_rules(
    project_id: UUID | None = None,
    db: Session = Depends(get_db),
):
    """
    The rule book, with clause numbers resolved for a project's edition.

    Pass project_id to get the numbers as they actually read on that
    contract (Progress Reports are Sub-Clause 4.20 under FIDIC 2017 and
    4.21 under 1999) - citing the wrong one in correspondence is exactly
    the sort of small error an Engineer will use to argue about a notice.
    """
    edition = DEFAULT_EDITION.value

    if project_id is not None:
        project = db.get(Project, project_id)
        if project is not None:
            edition = getattr(project, "contract_edition", None) or edition

    return {
        "disclaimer": COMPLIANCE_DISCLAIMER,
        "contract_edition": edition,
        "rules": [
            {
                "key": rule.key,
                "title": rule.title,
                "clause_code": resolve_clause_code(rule, edition),
                "clause_title": rule.clause_title,
                "cadence": rule.cadence.value,
                "category": rule.category,
                "owed_by": rule.owed_by,
                "description": rule.description,
                "rights_destroying": rule.rights_destroying,
                "conditional": rule.conditional,
            }
            for rule in COMPLIANCE_RULES
        ],
    }


@router.get("/event-driven-rules", response_model=EventDrivenRulesOut)
def read_event_driven_rules(
    project_id: UUID | None = None,
    db: Session = Depends(get_db),
):
    """
    The EVENT-DRIVEN half of the document register - notices and replies
    that only exist once something happens, with clause numbers resolved
    for a project's edition exactly like /rules above.
    """
    edition = DEFAULT_EDITION.value

    if project_id is not None:
        project = db.get(Project, project_id)
        if project is not None:
            edition = getattr(project, "contract_edition", None) or edition

    return {
        "disclaimer": EVENT_DRIVEN_DISCLAIMER,
        "contract_edition": edition,
        "rules": [
            {
                "key": rule.key,
                "title": rule.title,
                "clause_code": clause_code(rule.clause_name, edition),
                "direction": rule.direction,
                "trigger": rule.trigger,
                "deadline": rule.deadline,
                "tracked_in": rule.tracked_in,
                "description": rule.description,
            }
            for rule in EVENT_DRIVEN_RULES
        ],
    }


@router.get("/filters", response_model=ObligationStatusOut)
def read_filters():
    """Filter chip vocabulary for the register screen."""
    return {
        "statuses": list(ObligationStatus),
        "categories": list(ObligationCategory),
    }


@router.get("/deadlines", response_model=DeadlineFeedOut)
def read_deadlines(
    project_id: UUID | None = None,
    within_days: int | None = Query(
        default=None,
        ge=0,
        le=730,
        description=(
            "Only return deadlines falling on or before today + N days. "
            "Omit for every open deadline."
        ),
    ),
    db: Session = Depends(get_db),
):
    """
    Every live deadline across both engines - compliance obligations,
    event notice periods, Sub-Clause 20.2 claim stages, Sub-Clause 3.7
    determinations and Sub-Clause 3.5 instructions - in one sorted list.

    This replaces the Deadlines dashboard's old client-side assembly,
    which fetched every project, then every claim, then made one more
    request per claim for its clock (~50 sequential round trips on a
    contractor running eight jobs) and could still only see events and
    claims.
    """
    return get_deadline_feed(db, project_id=project_id, within_days=within_days)


@router.get("/project/{project_id}", response_model=ComplianceRegisterOut)
def read_register(
    project_id: UUID,
    status: str | None = None,
    category: str | None = None,
    include_closed: bool = True,
    db: Session = Depends(get_db),
):
    project = db.get(Project, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")

    return {
        "project_id": project_id,
        "summary": compliance_service.get_register_summary(db, project_id),
        "obligations": compliance_service.get_register(
            db,
            project_id,
            status=status,
            category=category,
            include_closed=include_closed,
        ),
    }


@router.post("/project/{project_id}/regenerate", response_model=RegenerateResultOut)
def regenerate_register(
    project_id: UUID,
    db: Session = Depends(get_db),
):
    """
    Force a rebuild after editing contract milestones, and report what it
    actually did.

    Idempotent - the register is keyed on (project, rule, period), so
    calling this twice changes nothing the second time. It returns counts
    rather than the register itself precisely so the UI can say
    "12 re-dated, 5 revived, 3 alerts retired" instead of succeeding
    silently, which is indistinguishable from doing nothing.
    """
    project = db.get(Project, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")

    return compliance_service.regenerate_for_project(db, project_id)


@router.get("/obligations/{obligation_id}", response_model=ObligationOut)
def read_obligation(obligation_id: UUID, db: Session = Depends(get_db)):
    obligation = compliance_service.get_obligation(db, obligation_id)

    if obligation is None:
        raise HTTPException(status_code=404, detail="Obligation not found")

    return obligation


@router.patch("/obligations/{obligation_id}/submit", response_model=ObligationOut)
def submit_obligation(
    obligation_id: UUID,
    payload: ObligationSubmitRequest,
    db: Session = Depends(get_db),
):
    """
    Record that a submission actually went in.

    A date after the deadline is accepted and stored as SubmittedLate
    rather than rejected - the register is a record of what happened, and
    refusing late entries would only push people into not recording them.
    """
    obligation = compliance_service.mark_submitted(
        db,
        obligation_id,
        submitted_date=payload.submitted_date,
        submitted_reference=payload.submitted_reference,
        evidence_id=payload.evidence_id,
        notes=payload.notes,
    )

    if obligation is None:
        raise HTTPException(status_code=404, detail="Obligation not found")

    return obligation


@router.patch("/obligations/{obligation_id}/waive", response_model=ObligationOut)
def waive_obligation(
    obligation_id: UUID,
    payload: ObligationWaiveRequest,
    db: Session = Depends(get_db),
):
    """
    Mark a rule as not applying to this contract - no advance payment was
    agreed, no monthly revised programme is required, and so on. Survives
    every subsequent tick.
    """
    obligation = compliance_service.waive(
        db, obligation_id, payload.reason, evidence_id=payload.evidence_id
    )

    if obligation is None:
        raise HTTPException(status_code=404, detail="Obligation not found")

    return obligation


@router.patch("/obligations/{obligation_id}/reopen", response_model=ObligationOut)
def reopen_obligation(obligation_id: UUID, db: Session = Depends(get_db)):
    """Undo a waiver, or clear a submission entered in error."""
    obligation = compliance_service.reopen(db, obligation_id)

    if obligation is None:
        raise HTTPException(status_code=404, detail="Obligation not found")

    return obligation


@router.get("/runs", response_model=list[ComplianceRunOut])
def read_runs(limit: int = 20, db: Session = Depends(get_db)):
    """Recent sweeps. The answer to "did the system actually warn me"."""
    return compliance_service.get_recent_runs(db, limit)
