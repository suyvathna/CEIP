from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

NOTICE_PERIOD_DAYS = 28

# Deadlines are legal/contractual dates tied to the project's local calendar
# day, not the server's system clock. A server running in UTC (the normal
# default for cloud hosting) would compute "today" incorrectly for roughly
# the first 7 hours of each new day in Cambodia (UTC+7) - a deadline that
# just passed at local midnight would still look "pending" until the
# server's UTC clock rolled over. Anchoring explicitly to this timezone
# avoids that regardless of where the server itself is physically hosted.
PROJECT_TIMEZONE = ZoneInfo("Asia/Phnom_Penh")


def get_today() -> date:
    return datetime.now(PROJECT_TIMEZONE).date()


def calculate_notice_deadline(
    event_date: date,
    period_days: int = NOTICE_PERIOD_DAYS,
) -> date:
    """
    FIDIC Sub-Clause 20.1 (1999) / 20.2.1 (2017): notice of claim must be
    given no later than 28 days (the unamended default - see period_days)
    after the date the contractor became aware, or should have become
    aware, of the event giving rise to the claim.

    We use event_date (the date logged for the site event) as the practical
    proxy for "awareness date" - it's the earliest contemporaneous record
    available, and the one this system already captures.

    period_days defaults to the FIDIC unamended 28 days but should be
    passed explicitly from the owning Project's notice_period_days where
    available, since Particular Conditions frequently amend this number.
    """
    return event_date + timedelta(days=period_days)


def days_remaining(
    event_date: date,
    today: date,
    period_days: int = NOTICE_PERIOD_DAYS,
) -> int:
    """
    Days left until the notice deadline. Negative means the deadline has
    already passed.
    """
    deadline = calculate_notice_deadline(event_date, period_days)
    return (deadline - today).days


def get_notice_status(
    event_date: date,
    notice_given_date: date | None,
    today: date,
    period_days: int = NOTICE_PERIOD_DAYS,
) -> str:
    """
    One of:
    - "given_on_time": notice was submitted on or before the deadline
    - "given_late": notice was submitted, but after the deadline had passed
      (FIDIC's time-bar is absolute - submitting late notice does not cure
      it, this state exists purely as an honest historical record)
    - "overdue": the deadline has passed and no notice was ever given
    - "pending": still within the notice window, no notice given yet
    """
    deadline = calculate_notice_deadline(event_date, period_days)

    if notice_given_date is not None:
        return "given_on_time" if notice_given_date <= deadline else "given_late"

    return "overdue" if today > deadline else "pending"
