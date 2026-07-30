from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.constants.claim_status import RiskCategory
from app.models.claim import ClaimEvent
from app.models.event import Event
from app.models.programme_activity import (
    Activity,
    ActivityPredecessor,
    EventActivityImpact,
)
from app.schemas.programme import ActivityCreate, EventActivityImpactCreate
from app.services.cpm_service import ActivityInput, compute_cpm


def create_activity(db: Session, project_id: UUID, payload: ActivityCreate) -> Activity:
    activity = Activity(project_id=project_id, **payload.model_dump())
    db.add(activity)
    db.commit()
    db.refresh(activity)
    return activity


def get_project_activities(db: Session, project_id: UUID) -> list[Activity]:
    stmt = (
        select(Activity)
        .where(Activity.project_id == project_id)
        .order_by(Activity.planned_start)
    )
    return list(db.scalars(stmt).all())


def update_activity(db: Session, activity_id: UUID, payload: ActivityCreate):
    activity = db.get(Activity, activity_id)
    if not activity:
        return None

    for key, value in payload.model_dump().items():
        setattr(activity, key, value)

    db.commit()
    db.refresh(activity)
    return activity


def delete_activity(db: Session, activity_id: UUID) -> bool:
    activity = db.get(Activity, activity_id)
    if not activity:
        return False

    db.delete(activity)
    db.commit()
    return True


def add_predecessor(db: Session, activity_id: UUID, predecessor_id: UUID):
    existing = db.scalar(
        select(ActivityPredecessor).where(
            ActivityPredecessor.activity_id == activity_id,
            ActivityPredecessor.predecessor_id == predecessor_id,
        )
    )
    if existing:
        return existing

    link = ActivityPredecessor(activity_id=activity_id, predecessor_id=predecessor_id)
    db.add(link)
    db.commit()
    db.refresh(link)
    return link


def remove_predecessor(db: Session, activity_id: UUID, predecessor_id: UUID) -> bool:
    link = db.scalar(
        select(ActivityPredecessor).where(
            ActivityPredecessor.activity_id == activity_id,
            ActivityPredecessor.predecessor_id == predecessor_id,
        )
    )
    if not link:
        return False

    db.delete(link)
    db.commit()
    return True


def _predecessors_map(db: Session, project_id: UUID) -> dict[UUID, list[UUID]]:
    activity_ids = select(Activity.id).where(Activity.project_id == project_id)

    stmt = select(ActivityPredecessor).where(
        ActivityPredecessor.activity_id.in_(activity_ids)
    )
    links = db.scalars(stmt).all()

    result: dict[UUID, list[UUID]] = {}
    for link in links:
        result.setdefault(str(link.activity_id), []).append(str(link.predecessor_id))

    return result


def create_impact(
    db: Session, event_id: UUID, payload: EventActivityImpactCreate
) -> EventActivityImpact:
    impact = EventActivityImpact(
        event_id=event_id,
        activity_id=payload.activity_id,
        impact_days=payload.impact_days,
        risk_category=payload.risk_category,
        notes=payload.notes,
    )
    db.add(impact)
    db.commit()
    db.refresh(impact)
    return impact


def get_activity_impacts(db: Session, activity_id: UUID) -> list[EventActivityImpact]:
    stmt = select(EventActivityImpact).where(
        EventActivityImpact.activity_id == activity_id
    )
    return list(db.scalars(stmt).all())


def get_event_impacts(db: Session, event_id: UUID) -> list[EventActivityImpact]:
    stmt = select(EventActivityImpact).where(EventActivityImpact.event_id == event_id)
    return list(db.scalars(stmt).all())


def _to_cpm_inputs(activities: list[Activity]) -> list[ActivityInput]:
    return [
        ActivityInput(
            id=str(a.id),
            name=a.name,
            planned_start=a.planned_start,
            planned_finish=a.planned_finish,
        )
        for a in activities
    ]


def compute_baseline_cpm(db: Session, project_id: UUID):
    activities = get_project_activities(db, project_id)
    if not activities:
        return None

    predecessors = _predecessors_map(db, project_id)
    return compute_cpm(_to_cpm_inputs(activities), predecessors)


def compute_cpm_with_impacts(
    db: Session,
    project_id: UUID,
    impact_days_by_activity: dict[str, int],
):
    activities = get_project_activities(db, project_id)
    if not activities:
        return None

    predecessors = _predecessors_map(db, project_id)
    base_inputs = _to_cpm_inputs(activities)

    overrides = {}
    for a in base_inputs:
        base_duration = max((a.planned_finish - a.planned_start).days, 0)
        overrides[a.id] = base_duration + impact_days_by_activity.get(a.id, 0)

    return compute_cpm(base_inputs, predecessors, duration_overrides=overrides)


def analyze_claim_delay(db: Session, claim_id: UUID, project_id: UUID) -> dict | None:
    """
    Phase-2-scoped delay analysis for one claim: recomputes the critical
    path with only this claim's linked-event impacts applied, compares
    against the unimpacted baseline to get a critical-path delta (this
    naturally nets out float - an impact that doesn't exhaust an
    activity's float doesn't move the project finish date), and
    separately surfaces any other Contractor-Risk events impacting
    activities whose planned dates overlap this claim's affected
    activities, for transparency.

    This deliberately does NOT attempt to automatically decide true
    concurrency (whether the other event is independently critical) -
    that is presented to Contractor and Engineer as a fact to jointly
    assess, consistent with the SCL Protocol's position that an
    Employer-Risk delay keeps its full EOT entitlement unless proven
    otherwise, not reduced by an algorithm's guess.
    """
    baseline = compute_baseline_cpm(db, project_id)
    if baseline is None:
        return None

    claim_event_ids = list(
        db.scalars(select(ClaimEvent.event_id).where(ClaimEvent.claim_id == claim_id))
    )

    claim_impacts = []
    if claim_event_ids:
        stmt = select(EventActivityImpact).where(
            EventActivityImpact.event_id.in_(claim_event_ids)
        )
        claim_impacts = list(db.scalars(stmt).all())

    impact_days_by_activity: dict[str, int] = {}
    for impact in claim_impacts:
        key = str(impact.activity_id)
        impact_days_by_activity[key] = impact_days_by_activity.get(key, 0) + impact.impact_days

    claim_impacted = compute_cpm_with_impacts(
        db, project_id, impact_days_by_activity
    )

    gross_delay = (
        claim_impacted.project_finish - baseline.project_finish
    ).days
    requested_days = sum(impact_days_by_activity.values())

    # Overlap check: other events' Contractor-Risk impacts on activities
    # whose planned window overlaps an activity this claim's events hit.
    affected_activity_ids = set(impact_days_by_activity.keys())
    overlapping = []

    if affected_activity_ids:
        activities_by_id = {
            str(a.id): a for a in get_project_activities(db, project_id)
        }
        affected_windows = [
            (activities_by_id[aid].planned_start, activities_by_id[aid].planned_finish)
            for aid in affected_activity_ids
            if aid in activities_by_id
        ]

        other_impacts_stmt = select(EventActivityImpact).where(
            EventActivityImpact.risk_category == RiskCategory.CONTRACTOR_RISK.value,
            ~EventActivityImpact.event_id.in_(claim_event_ids or [None]),
        )
        events_by_id = {}
        for impact in db.scalars(other_impacts_stmt).all():
            activity = activities_by_id.get(str(impact.activity_id))
            if not activity:
                continue

            overlaps_any = any(
                activity.planned_start <= w_end and w_start <= activity.planned_finish
                for w_start, w_end in affected_windows
            )
            if not overlaps_any:
                continue

            if impact.event_id not in events_by_id:
                events_by_id[impact.event_id] = db.get(Event, impact.event_id)
            event = events_by_id[impact.event_id]

            overlapping.append(
                {
                    "event_id": impact.event_id,
                    "event_title": event.title if event else "(deleted event)",
                    "activity_id": impact.activity_id,
                    "activity_name": activity.name,
                    "impact_days": impact.impact_days,
                    "risk_category": impact.risk_category,
                }
            )

    from app.models.claim import Claim
    from app.services.claim_fact_service import get_fact_summary

    claim = db.get(Claim, claim_id)
    fact_summary = get_fact_summary(db, claim_id)

    return {
        "claim_id": claim_id,
        "baseline_project_finish": baseline.project_finish,
        "claim_impacted_project_finish": claim_impacted.project_finish,
        "gross_critical_delay_days": max(gross_delay, 0),
        "requested_impact_days": requested_days,
        "float_absorbed_days": max(requested_days - max(gross_delay, 0), 0),
        "claimed_days": claim.claimed_days if claim else None,
        "fact_register_agreed_days": fact_summary["agreed_days_total"],
        "overlapping_contractor_risk_events": overlapping,
        "note": (
            "gross_critical_delay_days is a Phase-1/2 CPM estimate over "
            "finish-to-start logic only (no lags, no resource leveling). "
            "Overlapping Contractor-Risk events are listed for the "
            "Contractor and Engineer to jointly assess, not automatically "
            "subtracted - per the SCL Protocol, an Employer-Risk delay "
            "that independently sits on the critical path keeps its full "
            "EOT entitlement."
        ),
    }
