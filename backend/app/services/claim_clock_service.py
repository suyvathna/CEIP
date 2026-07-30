"""
Generalises notice_deadline_service's 28-day notice clock into the full
FIDIC 2017 Sub-Clause 20.2 lifecycle: the 28-day Notice of Claim, the
14-day window the Engineer has to flag a late notice (or lose the right
to), the 84-day fully detailed claim, and the 42-day Engineer response.

All four periods are project-configurable (see Project model) because
they're contractual defaults, not fixed law - Particular Conditions and
the MDB Harmonised Edition commonly amend them.
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


def get_today() -> date:
    return datetime.now(PROJECT_TIMEZONE).date()


@dataclass(frozen=True)
class ClaimClockConfig:
    notice_period_days: int = DEFAULT_NOTICE_PERIOD_DAYS
    detailed_claim_period_days: int = DEFAULT_DETAILED_CLAIM_PERIOD_DAYS
    engineer_late_notice_flag_days: int = DEFAULT_ENGINEER_LATE_NOTICE_FLAG_DAYS
    engineer_response_period_days: int = DEFAULT_ENGINEER_RESPONSE_PERIOD_DAYS


def config_from_project(project: Project | None) -> ClaimClockConfig:
    if project is None:
        return ClaimClockConfig()

    return ClaimClockConfig(
        notice_period_days=project.notice_period_days,
        detailed_claim_period_days=project.detailed_claim_period_days,
        engineer_late_notice_flag_days=project.engineer_late_notice_flag_days,
        engineer_response_period_days=project.engineer_response_period_days,
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

    # The next thing anyone needs to act on: the earliest stage that's
    # still pending or already overdue.
    open_stages = [s for s in stages if s["status"] in ("pending", "overdue")]
    next_action = min(open_stages, key=lambda s: s["deadline"]) if open_stages else None

    return {
        "stages": stages,
        "next_action": next_action,
        "days_remaining": (
            (next_action["deadline"] - today).days if next_action else None
        ),
        "at_risk": bool(
            next_action
            and ((next_action["deadline"] - today).days <= 7)
        ),
    }
