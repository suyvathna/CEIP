"""
Every contractual clock in the platform, in one place.

Originally this generalised notice_deadline_service's 28-day notice clock
into the full FIDIC 2017 Sub-Clause 20.2 lifecycle: the 28-day Notice of
Claim, the 14-day window the Engineer has to flag a late notice (or lose
the right to), the 84-day fully detailed claim, and the 42-day Engineer
response.

Engine B added two more lifecycles that work identically, so they live
here rather than in modules of their own:

  * Sub-Clause 3.7 - Agreement or Determination: 42 days to agree, a
    further 42 for the Engineer to determine, then 28 days from RECEIPT
    for a Notice of Dissatisfaction. That last one is the most expensive
    deadline in the whole contract, because the determination becomes
    final and binding the day after it expires.
  * Sub-Clause 3.5 / 13.3 - Instructions and Variations: the notice that
    must be given before work starts on an instruction that was never
    labelled a Variation, and the period to respond with a proposal.

All periods are project-configurable (see Project model) because they're
contractual defaults, not fixed law - Particular Conditions and the MDB
Harmonised Edition commonly amend them. Nothing here reads or writes the
database: these are pure date functions over a config, which is what
makes them cheap to call in a loop over every project on the daily tick
and trivial to unit test.
"""
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from app.models.project import Project

# Same reasoning as notice_deadline_service.py: claim deadlines are
# calendar-day deadlines tied to the project's local day, not whatever
# timezone the server happens to run in.
PROJECT_TIMEZONE = ZoneInfo("Asia/Phnom_Penh")

# FIDIC 2017 Red Book unamended defaults - used whenever a project hasn't
# overridden them.
DEFAULT_NOTICE_PERIOD_DAYS = 28
DEFAULT_DETAILED_CLAIM_PERIOD_DAYS = 84
DEFAULT_ENGINEER_LATE_NOTICE_FLAG_DAYS = 14
DEFAULT_ENGINEER_RESPONSE_PERIOD_DAYS = 42
DEFAULT_ENGINEER_DETERMINATION_PERIOD_DAYS = 42
DEFAULT_NOD_PERIOD_DAYS = 28
DEFAULT_DEEMED_VARIATION_NOTICE_DAYS = 7
DEFAULT_VARIATION_PROPOSAL_PERIOD_DAYS = 28
DEFAULT_ALERT_LEAD_DAYS = 7


def get_today() -> date:
    return datetime.now(PROJECT_TIMEZONE).date()


@dataclass(frozen=True)
class ClaimClockConfig:
    notice_period_days: int = DEFAULT_NOTICE_PERIOD_DAYS
    detailed_claim_period_days: int = DEFAULT_DETAILED_CLAIM_PERIOD_DAYS
    engineer_late_notice_flag_days: int = DEFAULT_ENGINEER_LATE_NOTICE_FLAG_DAYS

    # Doubles as the Sub-Clause 3.7.3 time limit for AGREEMENT: 20.2.5
    # sends the Engineer to 3.7 with the same 42 days, so there is
    # deliberately no second field for it.
    engineer_response_period_days: int = DEFAULT_ENGINEER_RESPONSE_PERIOD_DAYS

    # The FURTHER period the Engineer then has to make a determination
    # once the agreement window has expired (3.7.3).
    engineer_determination_period_days: int = DEFAULT_ENGINEER_DETERMINATION_PERIOD_DAYS

    # 3.7.5 Notice of Dissatisfaction, from receipt.
    nod_period_days: int = DEFAULT_NOD_PERIOD_DAYS

    # 3.5 practical alerting window - see the note on the Project column.
    deemed_variation_notice_days: int = DEFAULT_DEEMED_VARIATION_NOTICE_DAYS

    # 13.3.1 proposal response period.
    variation_proposal_period_days: int = DEFAULT_VARIATION_PROPOSAL_PERIOD_DAYS

    # How far ahead of a deadline the engines start alerting, and the
    # threshold get_claim_clock's at_risk flag uses.
    alert_lead_days: int = DEFAULT_ALERT_LEAD_DAYS


def config_from_project(project: Project | None) -> ClaimClockConfig:
    if project is None:
        return ClaimClockConfig()

    def _period(attr: str, default: int) -> int:
        # getattr with a default keeps every clock working against a
        # database that hasn't had the Engine A/B migration applied yet,
        # instead of 500ing on every claim page.
        value = getattr(project, attr, None)
        return default if value is None else int(value)

    return ClaimClockConfig(
        notice_period_days=project.notice_period_days,
        detailed_claim_period_days=project.detailed_claim_period_days,
        engineer_late_notice_flag_days=project.engineer_late_notice_flag_days,
        engineer_response_period_days=project.engineer_response_period_days,
        engineer_determination_period_days=_period(
            "engineer_determination_period_days",
            DEFAULT_ENGINEER_DETERMINATION_PERIOD_DAYS,
        ),
        nod_period_days=_period("nod_period_days", DEFAULT_NOD_PERIOD_DAYS),
        deemed_variation_notice_days=_period(
            "deemed_variation_notice_days", DEFAULT_DEEMED_VARIATION_NOTICE_DAYS
        ),
        variation_proposal_period_days=_period(
            "variation_proposal_period_days", DEFAULT_VARIATION_PROPOSAL_PERIOD_DAYS
        ),
        alert_lead_days=_period(
            "compliance_alert_lead_days", DEFAULT_ALERT_LEAD_DAYS
        ),
    )


def _deadline_status(
    deadline: date,
    completed_date: date | None,
    today: date,
) -> str:
    """
    One of: "met" (action taken on or before the deadline), "missed"
    (action taken, but after the deadline - the time-bar already applies;
    recording it late is an honest historical record, not a cure),
    "overdue" (deadline passed, no action yet), "pending" (still open).
    """
    if completed_date is not None:
        return "met" if completed_date <= deadline else "missed"

    return "overdue" if today > deadline else "pending"


def notice_deadline(awareness_date: date, config: ClaimClockConfig) -> date:
    return awareness_date + timedelta(days=config.notice_period_days)


def detailed_claim_deadline(awareness_date: date, config: ClaimClockConfig) -> date:
    return awareness_date + timedelta(days=config.detailed_claim_period_days)


def engineer_flag_deadline(
    notice_submitted_date: date, config: ClaimClockConfig
) -> date:
    return notice_submitted_date + timedelta(
        days=config.engineer_late_notice_flag_days
    )


def engineer_response_deadline(
    detailed_claim_submitted_date: date, config: ClaimClockConfig
) -> date:
    return detailed_claim_submitted_date + timedelta(
        days=config.engineer_response_period_days
    )


def get_claim_clock(
    *,
    awareness_date: date,
    notice_submitted_date: date | None,
    detailed_claim_submitted_date: date | None,
    engineer_responded_date: date | None,
    config: ClaimClockConfig,
    today: date | None = None,
) -> dict:
    """
    Full deadline picture for one claim: every stage's deadline and
    status, plus which action is next due and how many days are left for
    it - the payload the deadlines dashboard and claim detail screen both
    read from.
    """
    today = today or get_today()

    notice_dl = notice_deadline(awareness_date, config)
    notice_stat = _deadline_status(notice_dl, notice_submitted_date, today)

    stages = [
        {
            "stage": "notice",
            "label": "Notice of Claim (Sub-Clause 20.2.1)",
            "deadline": notice_dl,
            "status": notice_stat,
            "completed_date": notice_submitted_date,
        }
    ]

    if notice_submitted_date is not None:
        flag_dl = engineer_flag_deadline(notice_submitted_date, config)
        stages.append(
            {
                "stage": "engineer_late_notice_flag",
                "label": "Engineer's window to flag a late notice (20.2.2)",
                "deadline": flag_dl,
                "status": "pending" if today <= flag_dl else "window_closed",
                "completed_date": None,
            }
        )

        detailed_dl = detailed_claim_deadline(awareness_date, config)
        detailed_stat = _deadline_status(
            detailed_dl, detailed_claim_submitted_date, today
        )
        stages.append(
            {
                "stage": "detailed_claim",
                "label": "Fully detailed claim (20.2.4)",
                "deadline": detailed_dl,
                "status": detailed_stat,
                "completed_date": detailed_claim_submitted_date,
            }
        )

    if detailed_claim_submitted_date is not None:
        response_dl = engineer_response_deadline(
            detailed_claim_submitted_date, config
        )
        response_stat = _deadline_status(
            response_dl, engineer_responded_date, today
        )
        stages.append(
            {
                "stage": "engineer_response",
                "label": "Engineer's agreement or determination (20.2.5)",
                "deadline": response_dl,
                "status": response_stat,
                "completed_date": engineer_responded_date,
            }
        )

    return _summarise(stages, today, config)


def _summarise(stages: list[dict], today: date, config: ClaimClockConfig) -> dict:
    """
    Shared tail of every clock in this module: pick the next thing anyone
    has to act on, and say how close it is.

    Extracted when the 3.7 and 13.3 clocks arrived - all three lifecycles
    answer the same three questions ("what's next", "how long have I got",
    "should I be worried"), and three copies of this arithmetic would have
    been three places for the at-risk threshold to drift apart.
    """
    open_stages = [s for s in stages if s["status"] in ("pending", "overdue")]
    next_action = min(open_stages, key=lambda s: s["deadline"]) if open_stages else None

    days_remaining = (next_action["deadline"] - today).days if next_action else None

    return {
        "stages": stages,
        "next_action": next_action,
        "days_remaining": days_remaining,
        "at_risk": bool(
            next_action and days_remaining is not None
            and days_remaining <= config.alert_lead_days
        ),
    }


# ---------------------------------------------------------------------
# Sub-Clause 3.7 - Agreement or Determination
# ---------------------------------------------------------------------

def agreement_deadline(referred_date: date, config: ClaimClockConfig) -> date:
    """3.7.3 time limit for agreement - 42 days from the Engineer
    receiving the Claim or the matter."""
    return referred_date + timedelta(days=config.engineer_response_period_days)


def determination_deadline(referred_date: date, config: ClaimClockConfig) -> date:
    """
    3.7.3: where no agreement is reached, the Engineer's determination is
    due within a further 42 days AFTER the time limit for agreement -
    i.e. 84 days from referral on unamended terms, not 42.
    """
    return agreement_deadline(referred_date, config) + timedelta(
        days=config.engineer_determination_period_days
    )


def nod_deadline(determination_received_date: date, config: ClaimClockConfig) -> date:
    """
    3.7.5: 28 days from RECEIPT of the Engineer's Notice of the
    determination.

    Receipt, not the date printed on the letter. On a job where the
    Engineer's Notice is dated the 1st and reaches site on the 9th,
    running this from the letter date silently costs the Contractor eight
    of its twenty-eight days - and there is no relief afterwards, because
    the determination is final and binding the moment the window shuts.
    """
    return determination_received_date + timedelta(days=config.nod_period_days)


def get_determination_clock(
    *,
    referred_date: date,
    agreement_reached_date: date | None,
    determination_notice_date: date | None,
    determination_received_date: date | None,
    nod_given_date: date | None,
    config: ClaimClockConfig,
    today: date | None = None,
) -> dict:
    """
    Full deadline picture for one Sub-Clause 3.7 matter.

    Stages appear as the process actually unfolds: the NOD window doesn't
    exist until a determination has been received, and it never appears
    at all where the Parties reached agreement, because an agreement under
    3.7.2 is binding and there is nothing to be dissatisfied about.

    Note that the agreement stage is a WINDOW, not an obligation. Failing
    to reach agreement within the time limit is the ordinary path through
    3.7 - it is not a breach by anyone, and it simply hands the matter to
    the Engineer to determine. Treating it as "overdue" would leave it
    permanently first in the queue of open stages and mask the deadline
    that actually matters, which by then is the NOD window. Same
    treatment the 20.2.2 Engineer late-notice flag already gets above.
    """
    today = today or get_today()

    agree_dl = agreement_deadline(referred_date, config)

    if agreement_reached_date is not None:
        agree_status = "met" if agreement_reached_date <= agree_dl else "missed"
    elif determination_notice_date is not None:
        # The Engineer has issued a determination, so by definition no
        # agreement was reached and the consultation window is over -
        # whatever the calendar says about the 42 days.
        #
        # Getting this wrong had a nasty consequence: on a determination
        # issued early, the agreement stage stayed "pending" with a
        # deadline slightly EARLIER than the Notice of Dissatisfaction
        # deadline, so it won the "next action" comparison and masked the
        # NOD window entirely. The single most expensive deadline in the
        # contract was being hidden behind a stage that had already been
        # overtaken by events, and reported at WARNING instead of
        # CRITICAL.
        agree_status = "window_closed"
    else:
        agree_status = "pending" if today <= agree_dl else "window_closed"

    stages: list[dict] = [
        {
            "stage": "engineer_agreement",
            "label": "Engineer to consult and reach agreement (3.7.1 / 3.7.3)",
            "deadline": agree_dl,
            "status": agree_status,
            "completed_date": agreement_reached_date,
        }
    ]

    if agreement_reached_date is not None:
        # Agreed under 3.7.2 - binding, and the process stops here.
        return _summarise(stages, today, config)

    determine_dl = determination_deadline(referred_date, config)
    stages.append(
        {
            "stage": "engineer_determination",
            "label": "Engineer's fair determination (3.7.3)",
            "deadline": determine_dl,
            "status": _deadline_status(determine_dl, determination_notice_date, today),
            "completed_date": determination_notice_date,
        }
    )

    if determination_received_date is not None:
        nod_dl = nod_deadline(determination_received_date, config)
        stages.append(
            {
                "stage": "notice_of_dissatisfaction",
                "label": "Notice of Dissatisfaction (3.7.5) - or it becomes final and binding",
                "deadline": nod_dl,
                "status": _deadline_status(nod_dl, nod_given_date, today),
                "completed_date": nod_given_date,
            }
        )

    return _summarise(stages, today, config)


def is_final_and_binding(
    *,
    determination_received_date: date | None,
    nod_given_date: date | None,
    config: ClaimClockConfig,
    today: date | None = None,
) -> bool:
    """
    True once the 3.7.5 window has closed with no Notice of
    Dissatisfaction given. From this point the Engineer's determination
    cannot be reopened - not by the DAAB, not in arbitration.
    """
    if determination_received_date is None or nod_given_date is not None:
        return False

    today = today or get_today()
    return today > nod_deadline(determination_received_date, config)


# ---------------------------------------------------------------------
# Sub-Clause 3.5 / 13.3 - Instructions and Variations
# ---------------------------------------------------------------------

def deemed_variation_notice_deadline(
    instruction_received_date: date, config: ClaimClockConfig
) -> date:
    """
    The practical alerting deadline for the Sub-Clause 3.5 Notice.

    The contract does not actually give a number here: the Notice is due
    "immediately, and before commencing any work related to the
    instruction". A platform cannot raise an alarm against the word
    "immediately", so this window exists purely so the alarm has a date
    to hang on - it is not a grace period, and the UI says so wherever
    it is shown.
    """
    return instruction_received_date + timedelta(
        days=config.deemed_variation_notice_days
    )


def variation_proposal_deadline(
    anchor_date: date, config: ClaimClockConfig
) -> date:
    """13.3.1 / 13.3.2 - respond to the instruction or the request for
    proposal within the stated period."""
    return anchor_date + timedelta(days=config.variation_proposal_period_days)


def get_variation_clock(
    *,
    instruction_received_date: date | None,
    is_labelled_as_variation: bool,
    notice_given_date: date | None,
    work_commenced: bool,
    work_commenced_date: date | None,
    proposal_requested_date: date | None,
    proposal_submitted_date: date | None,
    config: ClaimClockConfig,
    today: date | None = None,
) -> dict:
    """
    Deadline picture for one Variation or candidate Variation.

    The first stage only exists where an instruction arrived that was NOT
    labelled a Variation - that is the Sub-Clause 3.5 case, and it is
    reported with an extra flag the ordinary status vocabulary can't
    carry: notice_late_because_work_started. A Contractor who began the
    instructed work before giving Notice has not "got a few days left";
    it is already out of time under 3.5 no matter what the calendar says,
    and being told a soothing "4 days remaining" would be actively
    misleading.
    """
    today = today or get_today()

    stages: list[dict] = []
    notice_late_because_work_started = False

    if instruction_received_date is not None and not is_labelled_as_variation:
        notice_dl = deemed_variation_notice_deadline(instruction_received_date, config)
        status = _deadline_status(notice_dl, notice_given_date, today)

        # Work started before the Notice went in - 3.5 is already
        # breached, whatever the date arithmetic says.
        if notice_given_date is None and work_commenced:
            status = "missed"
            notice_late_because_work_started = True
        elif (
            notice_given_date is not None
            and work_commenced_date is not None
            and notice_given_date > work_commenced_date
        ):
            status = "missed"
            notice_late_because_work_started = True

        stages.append(
            {
                "stage": "deemed_variation_notice",
                "label": (
                    "Notice that the instruction is a Variation (3.5) - "
                    "due immediately, before any related work starts"
                ),
                "deadline": notice_dl,
                "status": status,
                "completed_date": notice_given_date,
            }
        )

    proposal_anchor = proposal_requested_date or instruction_received_date
    if proposal_anchor is not None:
        proposal_dl = variation_proposal_deadline(proposal_anchor, config)
        stages.append(
            {
                "stage": "variation_proposal",
                "label": "Respond with a Variation proposal (13.3)",
                "deadline": proposal_dl,
                "status": _deadline_status(proposal_dl, proposal_submitted_date, today),
                "completed_date": proposal_submitted_date,
            }
        )

    summary = _summarise(stages, today, config)
    summary["notice_late_because_work_started"] = notice_late_because_work_started
    return summary
