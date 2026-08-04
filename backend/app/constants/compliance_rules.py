"""
Engine A's rule book: the mandatory, time-bound submissions a FIDIC
contract requires regardless of whether anything goes wrong.

These are the obligations that kill contractors quietly. Nobody forgets
to claim for a flooded site; plenty of teams forget that the Sub-Clause
4.20 progress report was due seven days after month end, that the
Sub-Clause 8.3 initial programme was due 28 days after Commencement, or
that the Statement at Completion under 14.10 has to go in within 84 days
of the Taking-Over Certificate. Each miss is a breach the Engineer can
point at later, and several of them (a late 14.11 Final Statement above
all) forfeit money outright.

Same disclaimer as app.constants.fidic_clauses: these are the unamended
General Conditions. Particular Conditions and the MDB Harmonised Edition
routinely change the numbers, which is why every period below is either
project-configurable or waivable per instance rather than hardcoded law.
"""

from calendar import monthrange
from dataclasses import dataclass, field
from datetime import date, timedelta

from app.constants.compliance import (
    MilestoneAnchor,
    ObligationCadence,
    ObligationCategory,
    OwedBy,
)
from app.constants.contract_edition import clause_code

COMPLIANCE_DISCLAIMER = (
    "This compliance register is generated from the unamended FIDIC "
    "General Conditions for the edition set on this project. Periods "
    "shown are contractual defaults, not law - check the Particular "
    "Conditions before relying on any date here, and waive any rule that "
    "does not apply to this contract."
)


@dataclass(frozen=True)
class ObligationRule:
    """
    One recurring or one-off contractual duty.

    Deadlines are never written into this table. A rule states an anchor
    (which contract milestone the clock starts from) and an offset (how
    many days after it), and app.services.compliance_service resolves
    both against the live Project row on every scheduler tick. Change a
    project's Taking-Over date and every 14.10/11.1 deadline re-dates
    itself on the next tick, exactly as claim_clock_service already does
    for Sub-Clause 20.2.
    """

    key: str
    title: str

    # Key into app.constants.contract_edition.CLAUSE_NUMBERS, so the
    # clause number printed in the UI and in correspondence follows the
    # project's edition (Progress Reports are 4.20 in 2017 but 4.21 in
    # 1999).
    clause_name: str
    clause_title: str

    cadence: ObligationCadence
    anchor: MilestoneAnchor
    category: ObligationCategory
    owed_by: OwedBy
    description: str

    # Fixed offset in days from the anchor date. Ignored when
    # offset_config_field is set.
    offset_days: int = 0

    # Name of a Project column to read the offset from instead, so a PM
    # can retune it per contract without a code change.
    offset_config_field: str | None = None

    # For MilestoneAnchor.PARENT_OBLIGATION: the rule whose actual
    # submission (or, failing that, due date) this one runs from.
    parent_key: str | None = None

    # True where missing the deadline forfeits an entitlement outright
    # rather than merely being a breach. Drives CRITICAL alerting.
    rights_destroying: bool = False

    # Rules that only apply to some contracts. Surfaced in the UI with a
    # prompt to waive them if they don't apply here, so the register
    # doesn't fill with noise on a contract with no advance payment.
    conditional: bool = False

    aliases: tuple[str, ...] = field(default_factory=tuple)


COMPLIANCE_RULES: tuple[ObligationRule, ...] = (
    # ---------------------------------------------------------------
    # Mobilisation - anchored on the Letter of Acceptance / Commencement
    # ---------------------------------------------------------------
    ObligationRule(
        key="performance_security",
        title="Deliver Performance Security to the Employer",
        clause_name="performance_security",
        clause_title="Performance Security",
        cadence=ObligationCadence.ONE_OFF,
        anchor=MilestoneAnchor.LETTER_OF_ACCEPTANCE,
        offset_days=28,
        category=ObligationCategory.MOBILISATION,
        owed_by=OwedBy.CONTRACTOR,
        rights_destroying=True,
        description=(
            "The Contractor shall deliver the Performance Security to the "
            "Employer within 28 days after receiving the Letter of "
            "Acceptance, and send a copy to the Engineer. Failure is a "
            "ground for termination, and on most contracts the Employer "
            "will not certify the first payment without it."
        ),
    ),
    ObligationRule(
        key="advance_payment_guarantee",
        title="Provide Advance Payment Guarantee",
        clause_name="advance_payment",
        clause_title="Advance Payment",
        cadence=ObligationCadence.ONE_OFF,
        anchor=MilestoneAnchor.LETTER_OF_ACCEPTANCE,
        offset_days=28,
        category=ObligationCategory.MOBILISATION,
        owed_by=OwedBy.CONTRACTOR,
        conditional=True,
        description=(
            "Where an advance payment is stated in the Contract Data, no "
            "advance payment is made until the Employer has received the "
            "guarantee. Waive this rule if no advance payment was agreed."
        ),
    ),
    ObligationRule(
        key="insurance_evidence",
        title="Submit evidence of insurances",
        clause_name="insurance",
        clause_title="General Requirements for Insurances",
        cadence=ObligationCadence.ONE_OFF,
        anchor=MilestoneAnchor.COMMENCEMENT,
        offset_days=28,
        category=ObligationCategory.MOBILISATION,
        owed_by=OwedBy.CONTRACTOR,
        description=(
            "Evidence that the required insurances are in force, and "
            "copies of the policies, are to go to the other Party within "
            "the periods stated in the Contract Data."
        ),
    ),
    ObligationRule(
        key="health_and_safety_manual",
        title="Submit the health and safety manual",
        clause_name="health_and_safety",
        clause_title="Health and Safety Obligations",
        cadence=ObligationCadence.ONE_OFF,
        anchor=MilestoneAnchor.COMMENCEMENT,
        offset_days=21,
        category=ObligationCategory.MOBILISATION,
        owed_by=OwedBy.CONTRACTOR,
        description=(
            "The Contractor shall submit a health and safety manual for "
            "the execution of the Works before commencing any work on "
            "Site, and keep it updated."
        ),
    ),
    ObligationRule(
        key="quality_management_system",
        title="Submit the Quality Management System",
        clause_name="quality_management",
        clause_title="Quality Management and Compliance Verification Systems",
        cadence=ObligationCadence.ONE_OFF,
        anchor=MilestoneAnchor.COMMENCEMENT,
        offset_days=28,
        category=ObligationCategory.MOBILISATION,
        owed_by=OwedBy.CONTRACTOR,
        description=(
            "The Contractor shall prepare and submit a Quality Management "
            "System and a compliance verification system within 28 days "
            "of the Commencement Date."
        ),
    ),
    ObligationRule(
        key="contractors_representative_notice",
        title="Notify the Contractor's Representative",
        clause_name="contractors_representative",
        clause_title="Contractor's Representative",
        cadence=ObligationCadence.ONE_OFF,
        anchor=MilestoneAnchor.COMMENCEMENT,
        offset_days=7,
        category=ObligationCategory.MOBILISATION,
        owed_by=OwedBy.CONTRACTOR,
        description=(
            "The Contractor shall notify the Employer of the name and "
            "authority of the person who will act as the Contractor's "
            "Representative, and the extent of authority delegated to "
            "any other person acting on the Representative's behalf."
        ),
    ),
    ObligationRule(
        key="environmental_management_plan",
        title="Submit the Environmental Management Plan",
        clause_name="environmental_protection",
        clause_title="Environmental Protection",
        cadence=ObligationCadence.ONE_OFF,
        anchor=MilestoneAnchor.COMMENCEMENT,
        offset_days=28,
        category=ObligationCategory.MOBILISATION,
        owed_by=OwedBy.CONTRACTOR,
        conditional=True,
        description=(
            "Not a standing requirement of the unamended General "
            "Conditions' short Sub-Clause 4.18 text, but near-universal "
            "on ADB/World Bank-funded infrastructure work under the "
            "Particular Conditions or the Environmental Permit. Waive "
            "this rule if this contract carries no such requirement."
        ),
    ),
    ObligationRule(
        key="traffic_management_plan",
        title="Submit the Traffic Management Plan",
        clause_name="environmental_protection",
        clause_title="Environmental Protection / Particular Conditions",
        cadence=ObligationCadence.ONE_OFF,
        anchor=MilestoneAnchor.COMMENCEMENT,
        offset_days=28,
        category=ObligationCategory.MOBILISATION,
        owed_by=OwedBy.CONTRACTOR,
        conditional=True,
        description=(
            "A Particular-Conditions requirement on road and highway "
            "works, not a numbered General Conditions clause in its own "
            "right - kept on this register because it is exactly the "
            "kind of mobilisation submission that is easy to forget "
            "chasing the ones that are. Waive if this contract carries "
            "no such requirement."
        ),
    ),
    # ---------------------------------------------------------------
    # Programme
    # ---------------------------------------------------------------
    ObligationRule(
        key="initial_programme",
        title="Submit the initial Programme",
        clause_name="programme",
        clause_title="Programme",
        cadence=ObligationCadence.ONE_OFF,
        anchor=MilestoneAnchor.COMMENCEMENT,
        offset_days=28,
        category=ObligationCategory.PROGRAMME,
        owed_by=OwedBy.CONTRACTOR,
        rights_destroying=True,
        description=(
            "The initial Programme is due within 28 days of the "
            "Commencement Date. This one is worth being early on: an "
            "accepted baseline programme is what every later EOT claim "
            "is measured against, and a Contractor with no accepted "
            "baseline is arguing delay from nothing."
        ),
    ),
    ObligationRule(
        key="revised_programme",
        title="Submit a revised Programme",
        clause_name="programme",
        clause_title="Programme",
        cadence=ObligationCadence.MONTHLY,
        anchor=MilestoneAnchor.MONTH_END,
        offset_config_field="progress_report_due_days",
        category=ObligationCategory.PROGRAMME,
        owed_by=OwedBy.CONTRACTOR,
        conditional=True,
        description=(
            "A revised Programme is due whenever the current one ceases "
            "to reflect actual progress, and within 14 days of an "
            "Engineer's Notice that it does not comply. Many Particular "
            "Conditions turn this into a flat monthly requirement, which "
            "is how it is generated here - waive any month where your "
            "contract does not require one."
        ),
    ),
    # ---------------------------------------------------------------
    # Monthly reporting
    # ---------------------------------------------------------------
    ObligationRule(
        key="monthly_progress_report",
        title="Submit the monthly Progress Report",
        clause_name="progress_reports",
        clause_title="Progress Reports",
        cadence=ObligationCadence.MONTHLY,
        anchor=MilestoneAnchor.MONTH_END,
        offset_config_field="progress_report_due_days",
        category=ObligationCategory.REPORTING,
        owed_by=OwedBy.CONTRACTOR,
        description=(
            "Monthly progress reports are due within 7 days after the "
            "last day of the period they cover, and continue until the "
            "Contractor has completed all outstanding work. Beyond "
            "compliance, this is the Contractor's own contemporaneous "
            "record - a claim supported by progress reports that already "
            "flagged the problem is a different animal from one that "
            "raises it for the first time months later."
        ),
    ),
    ObligationRule(
        key="personnel_equipment_records",
        title="Submit records of Contractor's Personnel and Equipment",
        clause_name="personnel_and_equipment_records",
        clause_title="Records of Contractor's Personnel and Equipment",
        cadence=ObligationCadence.MONTHLY,
        anchor=MilestoneAnchor.MONTH_END,
        offset_config_field="progress_report_due_days",
        category=ObligationCategory.REPORTING,
        owed_by=OwedBy.CONTRACTOR,
        description=(
            "Monthly records of the numbers of each category of the "
            "Contractor's Personnel and each type of Equipment on Site, "
            "in the form the Engineer instructs - due on the same cycle "
            "as the Progress Report, and just as easy to forget once the "
            "report itself is filed."
        ),
    ),
    # ---------------------------------------------------------------
    # Payment cycle
    # ---------------------------------------------------------------
    ObligationRule(
        key="schedule_of_payments",
        title="Submit the Schedule of Payments",
        clause_name="schedule_of_payments",
        clause_title="Schedule of Payments",
        cadence=ObligationCadence.ONE_OFF,
        anchor=MilestoneAnchor.COMMENCEMENT,
        offset_days=28,
        category=ObligationCategory.PAYMENT,
        owed_by=OwedBy.CONTRACTOR,
        conditional=True,
        description=(
            "Only where payment is on a Schedule of Payments basis "
            "rather than measured against a Bill of Quantities - waive "
            "this rule where the contract does not use one."
        ),
    ),
    ObligationRule(
        key="monthly_statement",
        title="Submit the monthly Statement (application for IPC)",
        clause_name="application_for_ipc",
        clause_title="Application for Interim Payment",
        cadence=ObligationCadence.MONTHLY,
        anchor=MilestoneAnchor.MONTH_END,
        offset_config_field="statement_due_days",
        category=ObligationCategory.PAYMENT,
        owed_by=OwedBy.CONTRACTOR,
        description=(
            "The Contractor submits a Statement after the end of each "
            "month, in the form the Engineer accepts. The General "
            "Conditions fix no day for this, so the offset is taken from "
            "this project's Statement due days setting - set it to match "
            "the day your Particular Conditions or the Engineer's agreed "
            "procedure actually require."
        ),
    ),
    ObligationRule(
        key="engineer_issue_ipc",
        title="Engineer to issue the Interim Payment Certificate",
        clause_name="issue_of_ipc",
        clause_title="Issue of Interim Payment Certificate",
        cadence=ObligationCadence.MONTHLY,
        anchor=MilestoneAnchor.PARENT_OBLIGATION,
        parent_key="monthly_statement",
        offset_days=28,
        category=ObligationCategory.PAYMENT,
        owed_by=OwedBy.ENGINEER,
        description=(
            "The Engineer shall issue an IPC within 28 days after "
            "receiving the Statement and supporting documents. This is "
            "tracked from the Contractor's side because a late IPC is "
            "the first half of the evidence trail for a Sub-Clause 14.8 "
            "financing charge or a 16.1 suspension."
        ),
    ),
    ObligationRule(
        key="employer_payment",
        title="Employer to pay the certified amount",
        clause_name="payment",
        clause_title="Payment",
        cadence=ObligationCadence.MONTHLY,
        anchor=MilestoneAnchor.PARENT_OBLIGATION,
        parent_key="monthly_statement",
        offset_days=56,
        category=ObligationCategory.PAYMENT,
        owed_by=OwedBy.EMPLOYER,
        description=(
            "The Employer shall pay the amount certified in an IPC within "
            "56 days after the Engineer receives the Statement. Once this "
            "date passes unpaid, financing charges start running under "
            "Sub-Clause 14.8 and the Sub-Clause 16.1 suspension right "
            "begins to open up - log an Event and raise a Claim rather "
            "than simply chasing it by phone."
        ),
    ),
    # ---------------------------------------------------------------
    # Completion and close-out
    # ---------------------------------------------------------------
    ObligationRule(
        key="statement_at_completion",
        title="Submit the Statement at Completion",
        clause_name="statement_at_completion",
        clause_title="Statement at Completion",
        cadence=ObligationCadence.ONE_OFF,
        anchor=MilestoneAnchor.TAKING_OVER,
        offset_days=84,
        category=ObligationCategory.COMPLETION,
        owed_by=OwedBy.CONTRACTOR,
        rights_destroying=True,
        description=(
            "Within 84 days after receiving the Taking-Over Certificate, "
            "the Contractor submits a Statement at Completion showing the "
            "value of all work done and any further sums the Contractor "
            "considers due - including every claim still outstanding. "
            "Anything left out here is much harder to recover later."
        ),
    ),
    ObligationRule(
        key="defects_notification_period_end",
        title="Defects Notification Period ends",
        clause_name="defects_notification_period",
        clause_title="Completion of Outstanding Work and Remedying Defects",
        cadence=ObligationCadence.ONE_OFF,
        anchor=MilestoneAnchor.TAKING_OVER,
        offset_config_field="defects_notification_period_days",
        category=ObligationCategory.COMPLETION,
        owed_by=OwedBy.CONTRACTOR,
        description=(
            "The end of the Defects Notification Period, measured from "
            "the Taking-Over Certificate. A milestone rather than a "
            "submission: after it passes the Engineer should issue the "
            "Performance Certificate, which in turn starts the Final "
            "Statement clock."
        ),
    ),
    ObligationRule(
        key="final_statement",
        title="Submit the Final Statement",
        clause_name="final_statement",
        clause_title="Final Statement",
        cadence=ObligationCadence.ONE_OFF,
        anchor=MilestoneAnchor.PERFORMANCE_CERTIFICATE,
        offset_days=56,
        category=ObligationCategory.COMPLETION,
        owed_by=OwedBy.CONTRACTOR,
        rights_destroying=True,
        description=(
            "Within 56 days after receiving the Performance Certificate, "
            "the Contractor submits the Final Statement with supporting "
            "documents. This is the last door in the contract: sums not "
            "included here, and claims not reserved here, are generally "
            "gone for good once the discharge takes effect."
        ),
    ),
)


RULES_BY_KEY: dict[str, ObligationRule] = {rule.key: rule for rule in COMPLIANCE_RULES}

# Rules whose anchor is a milestone that may simply not have happened
# yet. Generation skips them silently rather than inventing a date.
OPTIONAL_ANCHORS = (
    MilestoneAnchor.LETTER_OF_ACCEPTANCE,
    MilestoneAnchor.TAKING_OVER,
    MilestoneAnchor.PERFORMANCE_CERTIFICATE,
)


def resolve_clause_code(rule: ObligationRule, edition) -> str:
    return clause_code(rule.clause_name, edition)


def resolve_offset_days(rule: ObligationRule, project) -> int:
    """
    A rule's offset comes either from a literal on the rule or from a
    column on the Project, never from a constant frozen at import time -
    so retuning a project's periods re-dates its register on the next
    tick.
    """
    if rule.offset_config_field:
        value = getattr(project, rule.offset_config_field, None)
        if value is not None:
            return int(value)

    return rule.offset_days


def month_end(day: date) -> date:
    return day.replace(day=monthrange(day.year, day.month)[1])


def month_start(day: date) -> date:
    return day.replace(day=1)


def next_month_start(day: date) -> date:
    return month_end(day) + timedelta(days=1)


def month_periods(start: date, end: date):
    """
    Yields (period_key, period_start, period_end) for every calendar
    month touched by [start, end].

    period_key is "YYYY-MM" and forms half of an obligation's uniqueness
    key, which is what makes generation idempotent: re-running the tick
    a hundred times a day produces the same rows.
    """
    if end < start:
        return

    cursor = month_start(start)
    last = month_start(end)

    while cursor <= last:
        period_end = month_end(cursor)
        yield f"{cursor.year:04d}-{cursor.month:02d}", cursor, period_end
        cursor = period_end + timedelta(days=1)
