"""
Engine B - the "DO-IN-CASE" event listener.

Where Engine A asks "what does the calendar require of us this month",
Engine B asks "something happened; what has the contract just started
running against us". It is a state machine with two halves:

  * Reactive. Something dated gets recorded - an Event is logged, a
    Notice goes in, an Engineer's determination arrives - and dispatch()
    routes it to the handlers that advance state and raise alerts. Every
    transition in the system is caused by one of these; nothing here
    fires on a guess or on a status somebody typed by hand.

  * Sweeping. run_daily_sweep() walks every open clock once a day and
    catches the transitions that are caused by nothing happening, which
    in FIDIC is most of the expensive ones: a notice period expiring, an
    Engineer's determination window lapsing, and above all a Notice of
    Dissatisfaction window closing - the moment a determination becomes
    final and binding forever.

Three clocks are enforced here, all computed by claim_clock_service:

  Sub-Clause 20.2   awareness -> +28 notice -> +84 fully detailed claim
  Sub-Clause 3.7    referral -> +42 agree -> +42 determine -> +28 NOD
  Sub-Clause 3.5    instruction received -> Notice BEFORE work starts

This module imports models and clocks, never other services (beyond the
notification sink). determination_service and variation_service call
into it, not the other way round, which keeps the dependency graph
acyclic and means a trigger can be fired from an API request without
dragging Engine A in.
"""

import logging
from collections import defaultdict
from collections.abc import Callable
from datetime import date, timedelta
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.constants.claim_status import ClaimResponseType, ClaimStatus
from app.constants.contract_edition import clause_code
from app.constants.contract_triggers import TriggerType
from app.constants.determination import DeterminationStatus
from app.constants.fidic_clauses import get_clause_reference
from app.constants.notifications import (
    NotificationCategory,
    NotificationSeverity,
    severity_for_days_remaining,
)
from app.constants.variation import (
    DISGUISED_INSTRUCTION_ORIGINS,
    VARIATION_CLOSED_STATUSES,
    VariationStatus,
)
from app.models.claim import Claim, ClaimEvent, ClaimResponse
from app.models.determination import Determination
from app.models.event import Event
from app.models.notification import Notification
from app.models.project import Project
from app.models.variation import Variation
from app.services import notification_service
from app.services.claim_clock_service import (
    ClaimClockConfig,
    config_from_project,
    get_claim_clock,
    get_determination_clock,
    get_today,
    get_variation_clock,
    is_final_and_binding,
    notice_deadline,
)

logger = logging.getLogger(__name__)

Handler = Callable[[Session, dict], int]

_HANDLERS: dict[TriggerType, list[Handler]] = defaultdict(list)


def on(trigger: TriggerType):
    """Register a handler for a trigger. Handlers return the number of
    alerts they raised."""

    def decorator(func: Handler) -> Handler:
        _HANDLERS[trigger].append(func)
        return func

    return decorator


def dispatch(db: Session, trigger: TriggerType, **payload: Any) -> int:
    """
    Fire a trigger.

    Deliberately never raises. Engine B runs inside the same transaction
    as the user action that triggered it (submitting a claim notice,
    logging an instruction), and a failure to raise an alert must not
    roll back the substantive record the user just created - losing the
    Notice of Claim because the reminder about it failed would be an
    absurd trade. Failures are logged and swallowed.
    """
    raised = 0

    for handler in _HANDLERS.get(trigger, []):
        try:
            raised += handler(db, payload) or 0
        except Exception:  # noqa: BLE001 - see docstring
            logger.exception(
                "Engine B handler %s failed for trigger %s",
                getattr(handler, "__name__", handler),
                trigger,
            )

    return raised


# ---------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------

def _project(db: Session, project_id: UUID) -> Project | None:
    return db.get(Project, project_id)


def _config(db: Session, project_id: UUID) -> ClaimClockConfig:
    return config_from_project(_project(db, project_id))


def _edition(db: Session, project_id: UUID):
    project = _project(db, project_id)
    return getattr(project, "contract_edition", None) if project else None


def _describe_remaining(days_remaining: int) -> str:
    if days_remaining < 0:
        return f"expired {abs(days_remaining)} day(s) ago"
    if days_remaining == 0:
        return "expires today"
    return f"expires in {days_remaining} day(s)"


# Stages whose expiry destroys a right outright rather than merely being
# a breach. These are alerted at CRITICAL from the first warning, because
# there is no such thing as a gentle reminder about a time-bar.
RIGHTS_DESTROYING_STAGES = frozenset(
    {
        "notice",
        "detailed_claim",
        "notice_of_dissatisfaction",
        "deemed_variation_notice",
    }
)


def _alert_clock(
    db: Session,
    *,
    project: Project,
    clock: dict,
    category: NotificationCategory,
    source_type: str,
    source_id: UUID,
    link_path: str,
    subject: str,
    today: date,
) -> int:
    """
    Shared alerting for any of the three lifecycles: look at the clock's
    next_action, decide how loudly to shout, and hand it to the
    notification sink to dedupe.
    """
    next_action = clock.get("next_action")
    if not next_action:
        return 0

    lead_days = config_from_project(project).alert_lead_days
    days_remaining = (next_action["deadline"] - today).days

    if days_remaining > lead_days:
        return 0

    severity = severity_for_days_remaining(
        days_remaining,
        lead_days,
        rights_destroying=next_action["stage"] in RIGHTS_DESTROYING_STAGES,
    )

    body = (
        f"{subject}: {next_action['label']} "
        f"{_describe_remaining(days_remaining)} "
        f"(deadline {next_action['deadline'].isoformat()})."
    )

    if next_action["stage"] == "notice_of_dissatisfaction":
        body += (
            " If this window closes without a Notice of Dissatisfaction, "
            "the Engineer's determination becomes final and binding and "
            "cannot be reopened - not by the DAAB, not in arbitration."
        )
    elif next_action["stage"] in ("notice", "detailed_claim"):
        body += " Sub-Clause 20.2's time-bar is absolute; a late notice does not cure it."
    elif next_action["stage"] == "deemed_variation_notice":
        body += (
            " Sub-Clause 3.5 requires this Notice immediately and BEFORE any "
            "related work begins - the date shown is a working alert window, "
            "not a grace period."
        )

    raised = notification_service.emit(
        db,
        project_id=project.id,
        category=category,
        severity=severity,
        title=f"{subject} - {next_action['label']}",
        body=body,
        source_type=source_type,
        source_id=source_id,
        stage=next_action["stage"],
        link_path=link_path,
        due_date=next_action["deadline"],
        days_remaining=days_remaining,
        dedupe_key=notification_service.build_dedupe_key(
            source_type,
            source_id,
            next_action["stage"],
            severity.value,
            next_action["deadline"],
        ),
    )

    return 1 if raised else 0


def _resolve_finished_stages(
    db: Session, *, source_type: str, source_id: UUID, clock: dict
) -> int:
    """
    Retire alerts about stages of a record that are no longer the thing
    to act on - the Notice went in, the window closed, the whole record
    is done.

    Deliberately keyed on "is this still the next action" rather than on
    stage status, because that is the same question the alert answered
    when it was raised. A stage that has stopped being the next action
    has stopped being actionable, whatever its status says.
    """
    next_stage = (clock.get("next_action") or {}).get("stage")

    live = db.scalars(
        select(Notification).where(
            Notification.source_type == source_type,
            Notification.source_id == source_id,
            Notification.is_resolved.is_(False),
        )
    ).all()

    resolved = 0
    for notification in live:
        if notification.stage == next_stage:
            continue

        stage_row = next(
            (s for s in clock.get("stages", []) if s["stage"] == notification.stage),
            None,
        )

        if stage_row is None:
            reason = "No longer applicable"
        elif stage_row["status"] == "met":
            reason = "Done in time"
        elif stage_row["status"] == "missed":
            reason = "Recorded late - the time-bar had already applied"
        elif stage_row["status"] == "window_closed":
            reason = "Window closed"
        else:
            reason = "Superseded by a later stage"

        resolved += notification_service.resolve_source(
            db,
            source_type=source_type,
            source_id=source_id,
            stage=notification.stage,
            reason=reason,
        )

    return resolved


# ---------------------------------------------------------------------
# Reactive handlers
# ---------------------------------------------------------------------

@on(TriggerType.EVENT_LOGGED)
def _on_event_logged(db: Session, payload: dict) -> int:
    """
    A site Event was logged. If its type maps to a citable FIDIC claim
    ground, the Sub-Clause 20.2.1 awareness clock is already running -
    whether or not anybody has decided to raise a Claim yet.

    That gap is where entitlements die. A Contractor logs "late access to
    the north compound", intends to think about it, and 28 days later the
    right to claim is simply gone. So the alert goes out at the moment of
    logging, states the deadline, and keeps stating it on every sweep
    until either a Notice is recorded or a Claim is raised.
    """
    event_id = payload.get("event_id")
    event = db.get(Event, event_id) if event_id else None
    if event is None:
        return 0

    clause = get_clause_reference(event.event_type)
    if not clause:
        return 0

    project = _project(db, event.project_id)
    if project is None:
        return 0

    config = config_from_project(project)
    today = payload.get("today") or get_today()
    deadline = notice_deadline(event.event_date, config)
    days_remaining = (deadline - today).days

    raised = notification_service.emit(
        db,
        project_id=project.id,
        category=NotificationCategory.EVENT,
        severity=NotificationSeverity.WARNING,
        title=(
            f"Notice clock started - {event.event_no or 'Event'}: {event.title}"
        ),
        body=(
            f"This event is tagged {clause['clause_code']} "
            f"({clause['clause_title']}). The "
            f"{clause_code('notice_of_claim', project.contract_edition)} Notice of "
            f"Claim is due by {deadline.isoformat()} "
            f"({config.notice_period_days} days from {event.event_date.isoformat()}) "
            f"- {_describe_remaining(days_remaining)}. Entitlement basis: "
            f"{clause['basis']}."
        ),
        clause_code=clause["clause_code"],
        source_type="event",
        source_id=event.id,
        stage="notice_clock_started",
        link_path=f"/projects/{project.id}/events/{event.id}",
        due_date=deadline,
        days_remaining=days_remaining,
        dedupe_key=notification_service.build_dedupe_key(
            "event", event.id, "notice_clock_started", "Warning"
        ),
    )

    return 1 if raised else 0


@on(TriggerType.DETAILED_CLAIM_SUBMITTED)
def _on_detailed_claim_submitted(db: Session, payload: dict) -> int:
    """
    Sub-Clause 20.2.5: once the fully detailed claim is in, the Engineer
    must proceed under Sub-Clause 3.7 to agree or determine it. That is
    not a separate optional process the Contractor opts into - it starts
    automatically - so a Determination record is opened here rather than
    waiting for someone to remember to create one.

    Opening it now is what makes the 3.7.5 Notice of Dissatisfaction
    window enforceable later: the record has to exist before the
    Engineer's determination lands, or nothing is watching for it.
    """
    claim_id = payload.get("claim_id")
    claim = db.get(Claim, claim_id) if claim_id else None
    if claim is None or claim.detailed_claim_submitted_date is None:
        return 0

    existing = db.scalar(
        select(Determination).where(Determination.claim_id == claim.id)
    )
    if existing is not None:
        # Re-submission after a request for particulars restarts the
        # Engineer's clock from the new date.
        if existing.referred_date != claim.detailed_claim_submitted_date:
            existing.referred_date = claim.detailed_claim_submitted_date
            db.flush()
        return 0

    determination = Determination(
        project_id=claim.project_id,
        claim_id=claim.id,
        determination_no=next_determination_no(db, claim.project_id),
        matter_title=claim.title,
        matter_description=(
            f"Sub-Clause 20.2 claim {claim.claim_no or ''} referred to the "
            f"Engineer for agreement or determination."
        ).strip(),
        subject_clause=claim.governing_clause,
        referred_date=claim.detailed_claim_submitted_date,
        status=DeterminationStatus.UNDER_CONSULTATION.value,
    )
    db.add(determination)
    db.flush()

    return 0


@on(TriggerType.ENGINEER_RESPONDED)
def _on_engineer_responded(db: Session, payload: dict) -> int:
    """
    An Engineer response landed against a claim. Where it is a
    substantive decision (a determination or a disagreement, as opposed
    to a request for particulars), it feeds the linked Sub-Clause 3.7
    record and opens the Notice of Dissatisfaction window.

    Note what is NOT assumed here: the response_date is the date on the
    Engineer's Notice, and the NOD clock runs from RECEIPT. Until someone
    confirms the receipt date, the platform provisionally treats them as
    the same day - which is the conservative choice, since it makes the
    window look shorter rather than longer - and the determination screen
    prompts for the real receipt date.
    """
    claim_id = payload.get("claim_id")
    claim = db.get(Claim, claim_id) if claim_id else None
    if claim is None:
        return 0

    response_type = payload.get("response_type")
    response_date = payload.get("response_date")

    if response_type not in (
        ClaimResponseType.AGREEMENT.value,
        ClaimResponseType.PARTIAL_AGREEMENT.value,
        ClaimResponseType.DISAGREEMENT.value,
        ClaimResponseType.DETERMINATION.value,
    ):
        return 0

    determination = db.scalar(
        select(Determination).where(Determination.claim_id == claim.id)
    )

    if determination is None:
        determination = Determination(
            project_id=claim.project_id,
            claim_id=claim.id,
            determination_no=next_determination_no(db, claim.project_id),
            matter_title=claim.title,
            subject_clause=claim.governing_clause,
            referred_date=claim.detailed_claim_submitted_date
            or response_date
            or claim.awareness_date,
            status=DeterminationStatus.UNDER_CONSULTATION.value,
        )
        db.add(determination)
        db.flush()

    if response_type == ClaimResponseType.AGREEMENT.value:
        determination.agreement_reached_date = response_date
        determination.status = DeterminationStatus.AGREED.value
        db.flush()
        return 0

    determination.determination_notice_date = response_date
    if determination.determination_received_date is None:
        determination.determination_received_date = response_date

    determination.days_determined = payload.get("days_granted")
    determination.cost_determined = payload.get("cost_awarded_amount")
    determination.determination_summary = payload.get("comment")
    determination.status = DeterminationStatus.DETERMINED_NOD_OPEN.value
    db.flush()

    project = _project(db, claim.project_id)
    if project is None:
        return 0

    config = config_from_project(project)
    today = payload.get("today") or get_today()
    from app.services.claim_clock_service import nod_deadline

    deadline = nod_deadline(determination.determination_received_date, config)
    days_remaining = (deadline - today).days

    raised = notification_service.emit(
        db,
        project_id=project.id,
        category=NotificationCategory.DETERMINATION,
        severity=NotificationSeverity.CRITICAL,
        title=(
            f"Notice of Dissatisfaction window open - "
            f"{determination.determination_no or 'determination'}"
        ),
        body=(
            f"The Engineer has determined \"{claim.title}\". A Notice of "
            f"Dissatisfaction under "
            f"{clause_code('notice_of_dissatisfaction', project.contract_edition)} "
            f"is due by {deadline.isoformat()} "
            f"({config.nod_period_days} days from receipt). If that window "
            f"closes without one, the determination becomes final and "
            f"binding and cannot be reopened. Confirm the actual date of "
            f"receipt on the determination record - the clock runs from "
            f"receipt, not from the date on the letter."
        ),
        clause_code=clause_code(
            "notice_of_dissatisfaction", project.contract_edition
        ),
        source_type="determination",
        source_id=determination.id,
        stage="notice_of_dissatisfaction",
        link_path=f"/projects/{project.id}/determinations/{determination.id}",
        due_date=deadline,
        days_remaining=days_remaining,
        dedupe_key=notification_service.build_dedupe_key(
            "determination", determination.id, "nod_window_opened", "Critical"
        ),
    )

    return 1 if raised else 0


@on(TriggerType.VARIATION_LOGGED)
def _on_variation_logged(db: Session, payload: dict) -> int:
    """
    An instruction was logged. If it changes the Works but was never
    labelled a Variation, this is the Sub-Clause 3.5 trap and the alert
    is CRITICAL immediately - not when a deadline approaches, because the
    real deadline is "before you start the work", and on a live site that
    can be tomorrow morning.
    """
    variation_id = payload.get("variation_id")
    variation = db.get(Variation, variation_id) if variation_id else None
    if variation is None:
        return 0

    if variation.origin not in DISGUISED_INSTRUCTION_ORIGINS:
        return 0

    if variation.notice_given_date is not None:
        return 0

    project = _project(db, variation.project_id)
    if project is None:
        return 0

    edition = project.contract_edition
    instruction_clause = clause_code("engineers_instructions", edition)
    vary_clause = clause_code("right_to_vary", edition)

    body = (
        f"An instruction was recorded that appears to change the Works but "
        f"was not issued as a Variation under {vary_clause}. "
        f"{instruction_clause} requires the Contractor to give Notice that "
        f"it considers the instruction a Variation IMMEDIATELY, and before "
        f"commencing any work related to it. Give that Notice before the "
        f"work starts - once it has started, the argument that this was a "
        f"Variation is very much harder to run."
    )

    if variation.work_commenced:
        body += (
            " Work is already recorded as commenced on this instruction, so "
            "the Sub-Clause 3.5 requirement has already been missed. Give "
            "the Notice anyway, immediately, and record the reason for the "
            "delay - a late Notice is worth more than none."
        )

    raised = notification_service.emit(
        db,
        project_id=project.id,
        category=NotificationCategory.VARIATION,
        severity=NotificationSeverity.CRITICAL,
        title=(
            f"Unlabelled instruction - {variation.variation_no or 'Variation'}: "
            f"{variation.title}"
        ),
        body=body,
        clause_code=instruction_clause,
        source_type="variation",
        source_id=variation.id,
        stage="deemed_variation_notice",
        link_path=f"/projects/{project.id}/variations/{variation.id}",
        due_date=variation.instruction_received_date,
        dedupe_key=notification_service.build_dedupe_key(
            "variation", variation.id, "unlabelled_instruction", "Critical"
        ),
    )

    return 1 if raised else 0


def next_determination_no(db: Session, project_id: UUID) -> str:
    """"DET-001", "DET-002", ... per project - mirrors Claim._next_claim_no."""
    from sqlalchemy import func as sa_func

    count = db.scalar(
        select(sa_func.count())
        .select_from(Determination)
        .where(Determination.project_id == project_id)
    )
    return f"DET-{(count or 0) + 1:03d}"


# ---------------------------------------------------------------------
# State advancement (the transitions caused by nothing happening)
# ---------------------------------------------------------------------

def advance_determination(
    db: Session,
    determination: Determination,
    config: ClaimClockConfig,
    today: date,
) -> bool:
    """
    Move a Sub-Clause 3.7 record to whatever state the calendar has put
    it in. Returns True if the status changed.

    Two of these transitions are terminal and neither is triggered by
    anyone doing anything:

      FINAL_AND_BINDING - the NOD window closed with no Notice. The
      determination can never be reopened. This is the single most
      consequential automatic state change in the platform, which is why
      the date it happened is recorded on the row rather than merely
      inferred later.

      DEEMED_REJECTION - the Engineer let the determination window lapse.
      Under FIDIC 2017 that is deemed a rejection, which opens the
      dispute route under Clause 21; the Contractor is not obliged to
      keep waiting politely.
    """
    if determination.status in (
        DeterminationStatus.AGREED.value,
        DeterminationStatus.NOD_GIVEN.value,
        DeterminationStatus.FINAL_AND_BINDING.value,
    ):
        return False

    original = determination.status

    if determination.nod_given_date is not None:
        determination.status = DeterminationStatus.NOD_GIVEN.value
        return determination.status != original

    if determination.agreement_reached_date is not None:
        determination.status = DeterminationStatus.AGREED.value
        return determination.status != original

    if determination.determination_received_date is not None:
        if is_final_and_binding(
            determination_received_date=determination.determination_received_date,
            nod_given_date=determination.nod_given_date,
            config=config,
            today=today,
        ):
            determination.status = DeterminationStatus.FINAL_AND_BINDING.value
            determination.is_final_and_binding = True
            if determination.became_final_on is None:
                from app.services.claim_clock_service import nod_deadline

                determination.became_final_on = nod_deadline(
                    determination.determination_received_date, config
                ) + timedelta(days=1)
        else:
            determination.status = DeterminationStatus.DETERMINED_NOD_OPEN.value

        return determination.status != original

    from app.services.claim_clock_service import (
        agreement_deadline,
        determination_deadline,
    )

    if today > determination_deadline(determination.referred_date, config):
        determination.status = DeterminationStatus.DEEMED_REJECTION.value
    elif today > agreement_deadline(determination.referred_date, config):
        determination.status = DeterminationStatus.AWAITING_DETERMINATION.value
    else:
        determination.status = DeterminationStatus.UNDER_CONSULTATION.value

    return determination.status != original


def advance_variation(
    variation: Variation, clock: dict
) -> bool:
    """
    Keep a Variation's status in step with what has actually been
    recorded against it. Returns True if the status changed.

    Terminal and human-decided states (VALUED, REJECTED, WITHDRAWN,
    DISPUTED) are left alone - the same principle Engine A applies to
    WAIVED obligations.
    """
    if variation.status in VARIATION_CLOSED_STATUSES:
        return False
    if variation.status == VariationStatus.DISPUTED.value:
        return False

    original = variation.status

    if variation.proposal_submitted_date is not None:
        variation.status = VariationStatus.PROPOSAL_SUBMITTED.value
    elif variation.proposal_requested_date is not None:
        variation.status = VariationStatus.PROPOSAL_DUE.value
    elif variation.notice_given_date is not None:
        variation.status = VariationStatus.NOTICE_GIVEN.value
    elif variation.is_labelled_as_variation:
        variation.status = VariationStatus.INSTRUCTED.value
    else:
        variation.status = VariationStatus.LOGGED.value

    return variation.status != original


# ---------------------------------------------------------------------
# The daily sweep
# ---------------------------------------------------------------------

def _sweep_events(db: Session, project: Project, today: date) -> tuple[int, int]:
    """
    Events sitting on a running Sub-Clause 20.2.1 clock with no Notice
    recorded and no Claim raised.

    The join to claim_events is the point: an Event that has been folded
    into a Claim is no longer this sweep's problem, because the Claim's
    own clock has taken over. Without it, every claimed event would keep
    generating notice reminders forever, and the noise would bury the
    events that genuinely still need one.
    """
    config = config_from_project(project)
    lead_days = config.alert_lead_days

    claimed_event_ids = set(
        db.scalars(
            select(ClaimEvent.event_id)
            .join(Claim, Claim.id == ClaimEvent.claim_id)
            .where(Claim.project_id == project.id)
        ).all()
    )

    events = db.scalars(
        select(Event).where(Event.project_id == project.id)
    ).all()

    raised = 0
    resolved = 0

    for event in events:
        # A Notice has been recorded, or the event has been folded into a
        # Claim whose own clock has taken over. Either way this event has
        # stopped being anybody's problem, so its standing alerts go.
        if event.notice_given_date is not None or event.id in claimed_event_ids:
            resolved += notification_service.resolve_source(
                db,
                source_type="event",
                source_id=event.id,
                reason=(
                    "Notice of Claim recorded"
                    if event.notice_given_date is not None
                    else "Folded into a Claim - the claim's own clock now applies"
                ),
            )
            continue

        clause = get_clause_reference(event.event_type)
        if not clause:
            continue

        deadline = notice_deadline(event.event_date, config)
        days_remaining = (deadline - today).days

        if days_remaining > lead_days:
            continue

        # Stop nagging forever once the bar has long since fallen. The
        # event stays on the deadlines feed as "missed"; it does not need
        # a fresh alert every morning for the rest of the job.
        if days_remaining < -lead_days:
            continue

        severity = severity_for_days_remaining(
            days_remaining, lead_days, rights_destroying=True
        )

        if notification_service.emit(
            db,
            project_id=project.id,
            category=NotificationCategory.EVENT,
            severity=severity,
            title=(
                f"No Notice of Claim yet - {event.event_no or 'Event'}: "
                f"{event.title}"
            ),
            body=(
                f"{clause['clause_code']} event with no Notice of Claim and no "
                f"Claim raised. The notice period "
                f"{_describe_remaining(days_remaining)} "
                f"(deadline {deadline.isoformat()}). Sub-Clause 20.2's "
                f"time-bar is absolute - once it passes, the entitlement is "
                f"gone whatever the merits."
            ),
            clause_code=clause["clause_code"],
            source_type="event",
            source_id=event.id,
            stage="notice_due",
            link_path=f"/projects/{project.id}/events/{event.id}",
            due_date=deadline,
            days_remaining=days_remaining,
            dedupe_key=notification_service.build_dedupe_key(
                "event", event.id, "notice_due", severity.value, deadline
            ),
        ):
            raised += 1

    return raised, resolved


def _latest_decision_date(db: Session, claim_id: UUID) -> date | None:
    from app.services.claim_service import DECISION_RESPONSE_TYPES

    return db.scalar(
        select(ClaimResponse.response_date)
        .where(
            ClaimResponse.claim_id == claim_id,
            ClaimResponse.response_type.in_(DECISION_RESPONSE_TYPES),
        )
        .order_by(ClaimResponse.response_date.desc())
        .limit(1)
    )


def _sweep_claims(db: Session, project: Project, today: date) -> tuple[int, int]:
    config = config_from_project(project)
    claims = db.scalars(
        select(Claim).where(Claim.project_id == project.id)
    ).all()

    raised = 0
    resolved = 0

    for claim in claims:
        if claim.status in (
            ClaimStatus.AGREED.value,
            ClaimStatus.PARTIALLY_AGREED.value,
            ClaimStatus.DETERMINED.value,
            ClaimStatus.LAPSED.value,
        ):
            resolved += notification_service.resolve_source(
                db,
                source_type="claim",
                source_id=claim.id,
                reason=f"Claim closed ({claim.status})",
            )
            continue

        clock = get_claim_clock(
            awareness_date=claim.awareness_date,
            notice_submitted_date=claim.notice_submitted_date,
            detailed_claim_submitted_date=claim.detailed_claim_submitted_date,
            engineer_responded_date=_latest_decision_date(db, claim.id),
            config=config,
            today=today,
        )

        # Sub-Clause 20.2.5: silence past the response period is treated
        # as a rejection the Contractor can act on. Previously this was
        # only applied lazily when someone happened to open the claim
        # page - which meant a claim nobody looked at sat in
        # "AwaitingEngineerResponse" indefinitely. The sweep now does it
        # for every claim, every day, whether or not anyone is watching.
        if (
            claim.status == ClaimStatus.AWAITING_ENGINEER_RESPONSE.value
            and claim.detailed_claim_submitted_date is not None
        ):
            from app.services.claim_clock_service import engineer_response_deadline

            if today > engineer_response_deadline(
                claim.detailed_claim_submitted_date, config
            ):
                claim.status = ClaimStatus.DEEMED_REJECTED.value

        raised += _alert_clock(
            db,
            project=project,
            clock=clock,
            category=NotificationCategory.CLAIM,
            source_type="claim",
            source_id=claim.id,
            link_path=f"/projects/{project.id}/claims/{claim.id}",
            subject=f"{claim.claim_no or 'Claim'}: {claim.title}",
            today=today,
        )
        resolved += _resolve_finished_stages(
            db, source_type="claim", source_id=claim.id, clock=clock
        )

    return raised, resolved


def _sweep_determinations(db: Session, project: Project, today: date) -> tuple[int, int]:
    config = config_from_project(project)
    determinations = db.scalars(
        select(Determination).where(Determination.project_id == project.id)
    ).all()

    raised = 0
    resolved = 0

    for determination in determinations:
        became_final = (
            determination.status != DeterminationStatus.FINAL_AND_BINDING.value
        )
        advance_determination(db, determination, config, today)
        became_final = (
            became_final
            and determination.status == DeterminationStatus.FINAL_AND_BINDING.value
        )

        if became_final:
            # This is the one alert that arrives too late to act on, and
            # it is sent anyway. A Contractor who does not know a
            # determination went final and binding will keep budgeting
            # for money it can no longer recover.
            if notification_service.emit(
                db,
                project_id=project.id,
                category=NotificationCategory.DETERMINATION,
                severity=NotificationSeverity.CRITICAL,
                title=(
                    f"Determination is now FINAL AND BINDING - "
                    f"{determination.determination_no or determination.matter_title}"
                ),
                body=(
                    f"The Notice of Dissatisfaction window on "
                    f"\"{determination.matter_title}\" closed on "
                    f"{determination.became_final_on.isoformat() if determination.became_final_on else 'the deadline'} "
                    f"with no Notice recorded. The Engineer's determination "
                    f"can no longer be challenged - not before the DAAB, not "
                    f"in arbitration. Record the outcome in the claim and "
                    f"adjust the forecast accordingly."
                ),
                clause_code=clause_code(
                    "notice_of_dissatisfaction", project.contract_edition
                ),
                source_type="determination",
                source_id=determination.id,
                link_path=(
                    f"/projects/{project.id}/determinations/{determination.id}"
                ),
                due_date=determination.became_final_on,
                stage="final_and_binding",
                dedupe_key=notification_service.build_dedupe_key(
                    "determination", determination.id, "final_and_binding", "Critical"
                ),
            ):
                raised += 1

            # The countdown alerts are spent - the window has shut. The
            # final-and-binding notice above replaces them, and leaving
            # "3 days left" standing next to "no longer challengeable"
            # would be worse than useless.
            resolved += notification_service.resolve_source(
                db,
                source_type="determination",
                source_id=determination.id,
                stage="notice_of_dissatisfaction",
                reason="Window closed - determination is final and binding",
            )
            continue

        if determination.status not in (
            DeterminationStatus.UNDER_CONSULTATION.value,
            DeterminationStatus.AWAITING_DETERMINATION.value,
            DeterminationStatus.DETERMINED_NOD_OPEN.value,
        ):
            resolved += notification_service.resolve_source(
                db,
                source_type="determination",
                source_id=determination.id,
                reason=f"Determination closed ({determination.status})",
            )
            continue

        clock = get_determination_clock(
            referred_date=determination.referred_date,
            agreement_reached_date=determination.agreement_reached_date,
            determination_notice_date=determination.determination_notice_date,
            determination_received_date=determination.determination_received_date,
            nod_given_date=determination.nod_given_date,
            config=config,
            today=today,
        )

        raised += _alert_clock(
            db,
            project=project,
            clock=clock,
            category=NotificationCategory.DETERMINATION,
            source_type="determination",
            source_id=determination.id,
            link_path=f"/projects/{project.id}/determinations/{determination.id}",
            subject=(
                f"{determination.determination_no or 'Determination'}: "
                f"{determination.matter_title}"
            ),
            today=today,
        )
        resolved += _resolve_finished_stages(
            db,
            source_type="determination",
            source_id=determination.id,
            clock=clock,
        )

    return raised, resolved


def _sweep_variations(db: Session, project: Project, today: date) -> tuple[int, int]:
    config = config_from_project(project)
    variations = db.scalars(
        select(Variation).where(Variation.project_id == project.id)
    ).all()

    raised = 0
    resolved = 0

    for variation in variations:
        if variation.status in VARIATION_CLOSED_STATUSES:
            resolved += notification_service.resolve_source(
                db,
                source_type="variation",
                source_id=variation.id,
                reason=f"Variation closed ({variation.status})",
            )
            continue

        clock = get_variation_clock(
            instruction_received_date=variation.instruction_received_date,
            is_labelled_as_variation=variation.is_labelled_as_variation,
            notice_given_date=variation.notice_given_date,
            work_commenced=variation.work_commenced,
            work_commenced_date=variation.work_commenced_date,
            proposal_requested_date=variation.proposal_requested_date,
            proposal_submitted_date=variation.proposal_submitted_date,
            config=config,
            today=today,
        )

        advance_variation(variation, clock)

        raised += _alert_clock(
            db,
            project=project,
            clock=clock,
            category=NotificationCategory.VARIATION,
            source_type="variation",
            source_id=variation.id,
            link_path=f"/projects/{project.id}/variations/{variation.id}",
            subject=(
                f"{variation.variation_no or 'Variation'}: {variation.title}"
            ),
            today=today,
        )

        # The Sub-Clause 3.5 Notice is a special case worth resolving
        # explicitly: once it has been given, the reactive CRITICAL alert
        # raised at logging time has done its job, and it is not one of
        # the clock's own stage alerts.
        if variation.notice_given_date is not None:
            resolved += notification_service.resolve_source(
                db,
                source_type="variation",
                source_id=variation.id,
                stage="deemed_variation_notice",
                reason="Sub-Clause 3.5 Notice recorded",
            )

        resolved += _resolve_finished_stages(
            db, source_type="variation", source_id=variation.id, clock=clock
        )

    return raised, resolved


def run_daily_sweep(db: Session, *, today: date | None = None) -> tuple[int, int]:
    """
    Engine B's half of the daily tick: every open clock in the system,
    advanced, alerted on, and - just as importantly - had its spent
    alerts retired.

    Returns (raised, resolved). Called by
    compliance_service.run_daily_tick inside its transaction and its
    advisory lock, so this does not commit.
    """
    today = today or get_today()
    projects = list(db.scalars(select(Project)).all())

    raised = 0
    resolved = 0

    for project in projects:
        for sweep in (
            _sweep_events,
            _sweep_claims,
            _sweep_determinations,
            _sweep_variations,
        ):
            r, c = sweep(db, project, today)
            raised += r
            resolved += c

    db.flush()
    return raised, resolved
