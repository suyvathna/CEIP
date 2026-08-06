"""
One deadline feed across both engines.

This replaces what the Deadlines dashboard used to do client-side: fetch
every project, then every claim in every project, then issue one more
request per claim for its clock. On a contractor running eight live jobs
with forty claims between them that was ~50 sequential round trips to
render one page, and it could only ever see events and claims - the
compliance register, Sub-Clause 3.7 determinations and Sub-Clause 3.5
instructions were invisible to it because they hadn't existed yet.

Everything is computed server-side in a handful of queries and returned
as one flat, sorted list. The rule for what belongs here: anything with a
date the Contractor will regret missing.
"""

from datetime import date, timedelta
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.constants.claim_status import ClaimStatus
from app.constants.compliance import OPEN_STATUSES
from app.constants.determination import DETERMINATION_OPEN_STATUSES
from app.constants.fidic_clauses import get_clause_reference
from app.constants.notifications import (
    SEVERITY_RANK,
    Engine,
    NotificationCategory,
    engine_for_category,
    severity_for_days_remaining,
)
from app.constants.variation import VARIATION_CLOSED_STATUSES
from app.models.claim import Claim, ClaimEvent, ClaimResponse
from app.models.compliance_obligation import ComplianceObligation
from app.models.determination import Determination
from app.models.event import Event
from app.models.project import Project
from app.models.variation import Variation
from app.services.claim_clock_service import (
    config_from_project,
    get_claim_clock,
    get_determination_clock,
    get_today,
    get_variation_clock,
    notice_deadline,
)
from app.services.contract_engine import RIGHTS_DESTROYING_STAGES


def _item(
    *,
    project: Project,
    source_type: str,
    source_id: UUID,
    category: NotificationCategory,
    reference: str | None,
    title: str,
    stage: str,
    stage_label: str,
    deadline: date,
    today: date,
    lead_days: int,
    clause_code: str | None,
    link_path: str,
    status: str,
) -> dict:
    days_remaining = (deadline - today).days

    return {
        "source_type": source_type,
        "source_id": source_id,
        "project_id": project.id,
        "project_name": project.project_name,
        "category": category.value,
        "reference": reference,
        "title": title,
        "stage": stage,
        "stage_label": stage_label,
        "clause_code": clause_code,
        "deadline": deadline,
        "days_remaining": days_remaining,
        "status": status,
        "severity": severity_for_days_remaining(
            days_remaining,
            lead_days,
            rights_destroying=stage in RIGHTS_DESTROYING_STAGES,
        ).value,
        "link_path": link_path,
    }


def _obligation_items(
    db: Session, project: Project, today: date, lead_days: int
) -> list[dict]:
    rows = db.scalars(
        select(ComplianceObligation).where(
            ComplianceObligation.project_id == project.id,
            ComplianceObligation.status.in_(tuple(OPEN_STATUSES)),
        )
    ).all()

    return [
        _item(
            project=project,
            source_type="obligation",
            source_id=row.id,
            category=NotificationCategory.COMPLIANCE,
            reference=row.period_key if row.period_key != "once" else None,
            title=row.title,
            stage="obligation",
            stage_label=f"{row.owed_by} obligation",
            deadline=row.due_date,
            today=today,
            lead_days=lead_days,
            clause_code=row.clause_code,
            link_path=f"/projects/{project.id}/compliance?highlight={row.id}",
            status=row.status,
        )
        for row in rows
    ]


def _event_items(
    db: Session, project: Project, today: date, lead_days: int
) -> list[dict]:
    """
    Events still carrying their own Sub-Clause 20.2.1 clock: no Notice
    recorded, and not yet folded into a Claim. Once a Claim exists, its
    clock supersedes this one and the event drops out of the feed - so
    the same deadline is never counted twice.
    """
    config = config_from_project(project)

    claimed_event_ids = set(
        db.scalars(
            select(ClaimEvent.event_id)
            .join(Claim, Claim.id == ClaimEvent.claim_id)
            .where(Claim.project_id == project.id)
        ).all()
    )

    events = db.scalars(
        select(Event).where(
            Event.project_id == project.id,
            Event.notice_given_date.is_(None),
        )
    ).all()

    items = []
    for event in events:
        if event.id in claimed_event_ids:
            continue

        clause = get_clause_reference(event.event_type)
        if not clause:
            continue

        deadline = notice_deadline(event.event_date, config)

        items.append(
            _item(
                project=project,
                source_type="event",
                source_id=event.id,
                category=NotificationCategory.EVENT,
                reference=event.event_no,
                title=event.title,
                stage="notice",
                stage_label="Notice of Claim (Sub-Clause 20.2.1)",
                deadline=deadline,
                today=today,
                lead_days=lead_days,
                clause_code=clause["clause_code"],
                link_path=f"/projects/{project.id}/events/{event.id}",
                status="overdue" if today > deadline else "pending",
            )
        )

    return items


def _claim_items(
    db: Session, project: Project, today: date, lead_days: int
) -> list[dict]:
    from app.services.claim_service import DECISION_RESPONSE_TYPES

    config = config_from_project(project)
    claims = db.scalars(select(Claim).where(Claim.project_id == project.id)).all()

    closed = {
        ClaimStatus.AGREED.value,
        ClaimStatus.PARTIALLY_AGREED.value,
        ClaimStatus.DETERMINED.value,
        ClaimStatus.LAPSED.value,
    }

    items = []
    for claim in claims:
        if claim.status in closed:
            continue

        responded = db.scalar(
            select(ClaimResponse.response_date)
            .where(
                ClaimResponse.claim_id == claim.id,
                ClaimResponse.response_type.in_(DECISION_RESPONSE_TYPES),
            )
            .order_by(ClaimResponse.response_date.desc())
            .limit(1)
        )

        clock = get_claim_clock(
            awareness_date=claim.awareness_date,
            notice_submitted_date=claim.notice_submitted_date,
            detailed_claim_submitted_date=claim.detailed_claim_submitted_date,
            engineer_responded_date=responded,
            config=config,
            today=today,
        )

        next_action = clock.get("next_action")
        if not next_action:
            continue

        items.append(
            _item(
                project=project,
                source_type="claim",
                source_id=claim.id,
                category=NotificationCategory.CLAIM,
                reference=claim.claim_no,
                title=claim.title,
                stage=next_action["stage"],
                stage_label=next_action["label"],
                deadline=next_action["deadline"],
                today=today,
                lead_days=lead_days,
                clause_code=claim.governing_clause,
                link_path=f"/projects/{project.id}/claims/{claim.id}",
                status=next_action["status"],
            )
        )

    return items


def _determination_items(
    db: Session, project: Project, today: date, lead_days: int
) -> list[dict]:
    config = config_from_project(project)
    rows = db.scalars(
        select(Determination).where(
            Determination.project_id == project.id,
            Determination.status.in_(tuple(DETERMINATION_OPEN_STATUSES)),
        )
    ).all()

    items = []
    for row in rows:
        clock = get_determination_clock(
            referred_date=row.referred_date,
            agreement_reached_date=row.agreement_reached_date,
            determination_notice_date=row.determination_notice_date,
            determination_received_date=row.determination_received_date,
            nod_given_date=row.nod_given_date,
            config=config,
            today=today,
        )

        next_action = clock.get("next_action")
        if not next_action:
            continue

        items.append(
            _item(
                project=project,
                source_type="determination",
                source_id=row.id,
                category=NotificationCategory.DETERMINATION,
                reference=row.determination_no,
                title=row.matter_title,
                stage=next_action["stage"],
                stage_label=next_action["label"],
                deadline=next_action["deadline"],
                today=today,
                lead_days=lead_days,
                clause_code=row.subject_clause,
                link_path=f"/projects/{project.id}/determinations/{row.id}",
                status=next_action["status"],
            )
        )

    return items


def _variation_items(
    db: Session, project: Project, today: date, lead_days: int
) -> list[dict]:
    config = config_from_project(project)
    rows = db.scalars(
        select(Variation).where(
            Variation.project_id == project.id,
            Variation.status.notin_(tuple(VARIATION_CLOSED_STATUSES)),
        )
    ).all()

    items = []
    for row in rows:
        clock = get_variation_clock(
            instruction_received_date=row.instruction_received_date,
            is_labelled_as_variation=row.is_labelled_as_variation,
            notice_given_date=row.notice_given_date,
            work_commenced=row.work_commenced,
            work_commenced_date=row.work_commenced_date,
            proposal_requested_date=row.proposal_requested_date,
            proposal_submitted_date=row.proposal_submitted_date,
            config=config,
            today=today,
        )

        next_action = clock.get("next_action")
        if not next_action:
            continue

        items.append(
            _item(
                project=project,
                source_type="variation",
                source_id=row.id,
                category=NotificationCategory.VARIATION,
                reference=row.variation_no,
                title=row.title,
                stage=next_action["stage"],
                stage_label=next_action["label"],
                deadline=next_action["deadline"],
                today=today,
                lead_days=lead_days,
                clause_code=row.instruction_reference,
                link_path=f"/projects/{project.id}/variations/{row.id}",
                status=next_action["status"],
            )
        )

    return items


def get_deadline_feed(
    db: Session,
    *,
    project_id: UUID | None = None,
    within_days: int | None = None,
    today: date | None = None,
) -> dict:
    """
    Every live deadline across both engines, soonest first.

    within_days=None means "everything still open", which is what the
    project-scoped compliance screen wants. The global Deadlines
    dashboard passes a window, so a PM with a hundred open obligations
    sees the fortnight that matters rather than the year that doesn't.
    """
    today = today or get_today()

    stmt = select(Project)
    if project_id is not None:
        stmt = stmt.where(Project.id == project_id)

    projects = list(db.scalars(stmt).all())

    items: list[dict] = []

    for project in projects:
        lead_days = config_from_project(project).alert_lead_days

        items.extend(_obligation_items(db, project, today, lead_days))
        items.extend(_event_items(db, project, today, lead_days))
        items.extend(_claim_items(db, project, today, lead_days))
        items.extend(_determination_items(db, project, today, lead_days))
        items.extend(_variation_items(db, project, today, lead_days))

    if within_days is not None:
        cutoff = today + timedelta(days=within_days)
        items = [i for i in items if i["deadline"] <= cutoff]

    items.sort(
        key=lambda i: (i["deadline"], SEVERITY_RANK.get(i["severity"], 99))
    )

    overdue = sum(1 for i in items if i["days_remaining"] < 0)
    critical = sum(1 for i in items if i["severity"] == "Critical")
    engine_a = sum(
        1 for i in items if engine_for_category(i["category"]) == Engine.A.value
    )

    return {
        "generated_for": today,
        "total": len(items),
        "overdue": overdue,
        "critical": critical,
        "engine_a": engine_a,
        "engine_b": len(items) - engine_a,
        "items": items,
    }
