"""
The EVENT-DRIVEN half of the FIDIC 2017 Red Book document register: the
notices and replies that only exist because something happened, as
opposed to app.constants.compliance_rules' ALWAYS obligations which are
owed regardless.

This is deliberately a reference table, not a second materialized
register like ComplianceObligation. A Notice of Claim or a Notice of
Dissatisfaction is a live, stateful thing this platform already tracks
properly - as an actual Claim/Variation/Determination row, timed by
app.services.claim_clock_service and dispatched through contract_engine.
Duplicating that here as another set of per-project due-date rows would
create two clocks answering the same question and let them drift apart.
So each entry just says what the notice/reply is, what triggers it, what
the FIDIC deadline formula is in plain English, and - critically - where
in this app to actually go and act on it. For the handful of clauses this
platform has no dedicated engine for (Exceptional Events, Fossils,
Notice to Correct, Termination, Suspension, unforeseeable physical
conditions), that pointer is the Correspondence tab: there is nowhere
else to record having sent the letter.
"""

from dataclasses import dataclass

from app.constants.compliance import OwedBy


@dataclass(frozen=True)
class EventDrivenRule:
    key: str
    title: str

    # Key into app.constants.contract_edition.CLAUSE_NUMBERS.
    clause_name: str

    # Who sends this notice/document.
    direction: OwedBy

    # Plain English: what has to happen for this to be owed.
    trigger: str

    # Plain English deadline formula - these are event-anchored (from the
    # triggering occurrence, not a project milestone), so unlike
    # ObligationRule this is prose, not an anchor+offset the scheduler
    # resolves against a Project column.
    deadline: str

    # Where in THIS app a Contractor actually tracks a real instance of
    # this notice, if anywhere: "Claims tab", "Variations tab",
    # "Determinations tab", or "Correspondence tab" for the clauses with
    # no dedicated engine. None only for the couple of entries here purely
    # for completeness (e.g. the Employer/Engineer-owed replies this
    # platform already surfaces as part of the Claims clock itself).
    tracked_in: str | None

    description: str


EVENT_DRIVEN_RULES: tuple[EventDrivenRule, ...] = (
    EventDrivenRule(
        key="notice_of_claim",
        title="Notice of Claim",
        clause_name="notice_of_claim",
        direction=OwedBy.CONTRACTOR,
        trigger=(
            "The Contractor becomes aware, or should have become aware, "
            "of an event or circumstance giving rise to a claim for "
            "additional time and/or cost."
        ),
        deadline="Within 28 days of becoming aware (or should have become aware).",
        tracked_in="Claims tab",
        description=(
            "The single most time-bar-heavy notice in the contract. "
            "Miss it and the claim is lost outright, however good the "
            "underlying entitlement - log the Claim as soon as the "
            "notice goes out, not after."
        ),
    ),
    EventDrivenRule(
        key="engineer_late_notice_flag",
        title="Engineer's notice that a Notice of Claim was late",
        clause_name="engineer_late_notice_flag",
        direction=OwedBy.ENGINEER,
        trigger="The Contractor's Notice of Claim was given after the 28-day window.",
        deadline="Within 14 days of receiving the (late) Notice of Claim.",
        tracked_in="Claims tab",
        description=(
            "Silence here is not agreement - but a flagged late notice "
            "starts the separate process for the Contractor to show "
            "why time should still run. Tracked as part of the claim's "
            "own clock."
        ),
    ),
    EventDrivenRule(
        key="fully_detailed_claim",
        title="Fully Detailed Claim",
        clause_name="fully_detailed_claim",
        direction=OwedBy.CONTRACTOR,
        trigger="A Notice of Claim has been given and is being pursued.",
        deadline="Within 84 days of the event/circumstance (or as otherwise agreed).",
        tracked_in="Claims tab",
        description=(
            "The particulars, basis, and substantiation of the claim in "
            "full. Sub-Clause 20.2.5 sends this straight into the 3.7 "
            "determination process the moment it's submitted."
        ),
    ),
    EventDrivenRule(
        key="agreement_or_determination",
        title="Engineer's Agreement or Determination",
        clause_name="agreement_or_determination",
        direction=OwedBy.ENGINEER,
        trigger="A fully detailed claim (or any other Sub-Clause 3.7 matter) has been referred.",
        deadline="Within 42 days of receiving the claim/matter, or as otherwise agreed.",
        tracked_in="Determinations tab",
        description=(
            "A late determination is itself a breach worth logging, but "
            "the more dangerous trap is the notice below - the 28-day "
            "objection window runs whether or not the determination "
            "feels final."
        ),
    ),
    EventDrivenRule(
        key="notice_of_dissatisfaction",
        title="Notice of Dissatisfaction",
        clause_name="notice_of_dissatisfaction",
        direction=OwedBy.CONTRACTOR,
        trigger="The Contractor disagrees with an Engineer's determination or agreement.",
        deadline="Within 28 days of receiving the determination.",
        tracked_in="Determinations tab",
        description=(
            "Miss this and the determination becomes final and binding "
            "for good - not appealable to the DAAB, not in arbitration. "
            "Runs from receipt, not from the date printed on the letter."
        ),
    ),
    EventDrivenRule(
        key="engineers_instructions",
        title="Notice that an instruction is treated as a Variation",
        clause_name="engineers_instructions",
        direction=OwedBy.CONTRACTOR,
        trigger=(
            "An instruction changes the Works but is not labelled a "
            "Variation (a marked-up drawing, a site memo, a line in "
            "minutes of meeting)."
        ),
        deadline="Immediately, and before any related work starts.",
        tracked_in="Variations tab",
        description=(
            "The Sub-Clause 3.5 alarm. A Contractor who simply builds "
            "what was asked and raises it at the next valuation has "
            "already lost the argument - the clock does not wait for "
            "the work to finish."
        ),
    ),
    EventDrivenRule(
        key="variation_procedure",
        title="Variation Proposal",
        clause_name="variation_procedure",
        direction=OwedBy.CONTRACTOR,
        trigger="The Engineer requests a proposal for a Variation (Sub-Clause 13.3.2).",
        deadline="Within the period stated in the request, or as instructed/agreed.",
        tracked_in="Variations tab",
        description=(
            "Covers the cost/time quotation for an instructed change - "
            "distinct from the Sub-Clause 3.5 notice above, which is "
            "about whether the instruction is a Variation at all."
        ),
    ),
    EventDrivenRule(
        key="unforeseeable_physical_conditions",
        title="Notice of Unforeseeable Physical Conditions",
        clause_name="unforeseeable_physical_conditions",
        direction=OwedBy.CONTRACTOR,
        trigger="The Contractor encounters physical conditions it considers unforeseeable.",
        deadline="As soon as practicable, before the conditions are disturbed if possible.",
        tracked_in="Correspondence tab",
        description=(
            "A classic claim ground (soft clay, unrecorded services, "
            "unexpected groundwater) - notice it here, then raise the "
            "Sub-Clause 20.2 claim on the Claims tab in the usual way."
        ),
    ),
    EventDrivenRule(
        key="fossils",
        title="Notice of Fossils / Antiquities / Site Finds",
        clause_name="fossils",
        direction=OwedBy.CONTRACTOR,
        trigger="Fossils, coins, articles of value or antiquity, or structures are found on Site.",
        deadline="Immediately upon discovery.",
        tracked_in="Correspondence tab",
        description=(
            "The Contractor must not disturb the find and must notify "
            "the Engineer at once - the Engineer then instructs how to "
            "deal with it, which is where a time/cost claim can follow."
        ),
    ),
    EventDrivenRule(
        key="exceptional_event",
        title="Notice of an Exceptional Event",
        clause_name="exceptional_event",
        direction=OwedBy.CONTRACTOR,
        trigger="An Exceptional Event (Force Majeure under 1999) prevents performance.",
        deadline="Within 14 days of becoming aware of the event.",
        tracked_in="Correspondence tab",
        description=(
            "Either Party may give this notice. Continued effect must "
            "then be notified monthly until it ends - log each notice "
            "here as it goes out."
        ),
    ),
    EventDrivenRule(
        key="notice_to_correct",
        title="Notice to Correct",
        clause_name="notice_to_correct",
        direction=OwedBy.ENGINEER,
        trigger="The Contractor fails to remedy a default under the Contract.",
        deadline="A reasonable time to correct is stated in the notice itself.",
        tracked_in="Correspondence tab",
        description=(
            "An Engineer-issued notice, not a Contractor obligation - "
            "logged here on receipt because an unanswered Notice to "
            "Correct is a step on the road to termination under 15.2."
        ),
    ),
    EventDrivenRule(
        key="termination_by_employer",
        title="Notice of Termination by Employer",
        clause_name="termination_by_employer",
        direction=OwedBy.EMPLOYER,
        trigger="A Sub-Clause 15.2 ground for termination has arisen.",
        deadline="Per the grounds and notice periods set out in Sub-Clause 15.2.",
        tracked_in="Correspondence tab",
        description=(
            "Received, not sent, by the Contractor - logged here so the "
            "date of receipt (which starts several other clocks) is on "
            "record."
        ),
    ),
    EventDrivenRule(
        key="suspension_by_contractor",
        title="Notice of Suspension (or reduced rate of work)",
        clause_name="suspension_by_contractor",
        direction=OwedBy.CONTRACTOR,
        trigger="The Employer fails to pay a certified amount, or otherwise substantially fails to perform.",
        deadline="Not less than 21 days' notice before suspending.",
        tracked_in="Correspondence tab",
        description=(
            "The Sub-Clause 16.1 right that turns a late-payment problem "
            "into contractual leverage - the underlying non-payment "
            "should already be on the Claims tab as its own claim."
        ),
    ),
    EventDrivenRule(
        key="termination_by_contractor",
        title="Notice of Termination by Contractor",
        clause_name="termination_by_contractor",
        direction=OwedBy.CONTRACTOR,
        trigger="A Sub-Clause 16.2 ground for termination has arisen.",
        deadline="Per the grounds and notice periods set out in Sub-Clause 16.2.",
        tracked_in="Correspondence tab",
        description=(
            "The last resort - logged here, but this is the point to "
            "get advice beyond what a register can offer."
        ),
    ),
)

EVENT_DRIVEN_DISCLAIMER = (
    "This is a reference table of the notices and replies the unamended "
    "FIDIC General Conditions require once a particular event happens - "
    "it does not itself compute a due date, because that date runs from "
    "the event, not from a fixed contract milestone. Where this platform "
    "already tracks the live clock for one of these (Claims, Variations, "
    "Determinations), follow the link. For the rest, log the letter on "
    "the Correspondence tab as it goes out or comes in."
)
