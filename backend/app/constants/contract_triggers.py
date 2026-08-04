"""
The trigger vocabulary Engine B listens on.

Engine B is a state machine, and every transition in it is caused by
exactly one of these - a dated thing that happened in the real world and
got recorded. Nothing in Engine B fires on a guess or on a status
somebody typed in by hand; if there is no trigger, there is no
transition.
"""

from enum import Enum


class TriggerType(str, Enum):
    # --- Site / record triggers -------------------------------------
    # An Event was logged whose event_type maps to a citable FIDIC claim
    # ground. Starts the Sub-Clause 20.2.1 awareness clock even before
    # anyone decides to raise a Claim.
    EVENT_LOGGED = "EventLogged"

    # A Notice of Claim was recorded against a bare Event (the
    # PATCH /events/{id}/notice path).
    EVENT_NOTICE_GIVEN = "EventNoticeGiven"

    # --- Sub-Clause 20.2 claim triggers -----------------------------
    CLAIM_CREATED = "ClaimCreated"
    CLAIM_NOTICE_SUBMITTED = "ClaimNoticeSubmitted"
    DETAILED_CLAIM_SUBMITTED = "DetailedClaimSubmitted"
    ENGINEER_RESPONDED = "EngineerResponded"

    # --- Sub-Clause 3.7 triggers ------------------------------------
    MATTER_REFERRED = "MatterReferred"
    DETERMINATION_RECEIVED = "DeterminationReceived"
    NOD_GIVEN = "NoticeOfDissatisfactionGiven"

    # --- Clause 13 / Sub-Clause 3.5 triggers ------------------------
    VARIATION_LOGGED = "VariationLogged"
    VARIATION_NOTICE_GIVEN = "VariationNoticeGiven"
    VARIATION_PROPOSAL_SUBMITTED = "VariationProposalSubmitted"

    # --- Project-level triggers -------------------------------------
    # A contract milestone moved (Commencement, Taking-Over,
    # Performance Certificate). Forces Engine A to re-materialise every
    # obligation anchored on it.
    PROJECT_MILESTONE_CHANGED = "ProjectMilestoneChanged"

    # The daily sweep. Fired by the scheduler (or POST /compliance/tick),
    # and the only trigger that is time-based rather than caused by a
    # user action.
    DAILY_TICK = "DailyTick"
