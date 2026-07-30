from datetime import date, datetime, timedelta, timezone

from app.services.notice_deadline_service import (
    PROJECT_TIMEZONE,
    calculate_notice_deadline,
    days_remaining,
    get_notice_status,
)


def test_utc_server_clock_does_not_shift_the_local_calendar_day():
    # 19:00 UTC on July 29 is 2:00 AM on July 30 in Phnom Penh (UTC+7).
    # A server running on UTC system time must NOT report this as July 29.
    utc_instant = datetime(2026, 7, 29, 19, 0, tzinfo=timezone.utc)
    phnom_penh_date = utc_instant.astimezone(PROJECT_TIMEZONE).date()
    assert phnom_penh_date == date(2026, 7, 30)


def test_deadline_is_28_days_after_event():
    assert calculate_notice_deadline(date(2026, 1, 1)) == date(2026, 1, 29)


def test_deadline_crosses_month_boundary():
    assert calculate_notice_deadline(date(2026, 8, 10)) == date(2026, 9, 7)


def test_deadline_handles_leap_year():
    assert calculate_notice_deadline(date(2028, 2, 1)) == date(2028, 2, 29)


def test_deadline_crosses_year_boundary():
    assert calculate_notice_deadline(date(2026, 12, 20)) == date(2027, 1, 17)


def test_status_pending_when_deadline_not_reached():
    status = get_notice_status(date(2026, 7, 1), None, today=date(2026, 7, 20))
    assert status == "pending"


def test_status_pending_on_the_deadline_day_itself():
    # The deadline date itself is still compliant - this boundary matters:
    # a contractor who submits notice ON day 28 has NOT missed the deadline.
    deadline = calculate_notice_deadline(date(2026, 7, 1))
    status = get_notice_status(date(2026, 7, 1), None, today=deadline)
    assert status == "pending"


def test_status_overdue_the_day_after_deadline():
    deadline = calculate_notice_deadline(date(2026, 7, 1))
    the_day_after = deadline + timedelta(days=1)
    status = get_notice_status(date(2026, 7, 1), None, today=the_day_after)
    assert status == "overdue"


def test_status_given_on_time_when_submitted_on_deadline_day():
    deadline = calculate_notice_deadline(date(2026, 7, 1))
    status = get_notice_status(
        date(2026, 7, 1), notice_given_date=deadline, today=date(2026, 8, 1)
    )
    assert status == "given_on_time"


def test_status_given_on_time_when_submitted_early():
    status = get_notice_status(
        date(2026, 7, 1), notice_given_date=date(2026, 7, 10), today=date(2026, 8, 1)
    )
    assert status == "given_on_time"


def test_status_given_late_when_submitted_after_deadline():
    deadline = calculate_notice_deadline(date(2026, 7, 1))
    late_date = deadline + timedelta(days=2)
    status = get_notice_status(
        date(2026, 7, 1), notice_given_date=late_date, today=date(2026, 8, 15)
    )
    assert status == "given_late"


def test_days_remaining_positive_before_deadline():
    assert days_remaining(date(2026, 7, 1), today=date(2026, 7, 20)) == 9


def test_days_remaining_zero_on_deadline_day():
    deadline = calculate_notice_deadline(date(2026, 7, 1))
    assert days_remaining(date(2026, 7, 1), today=deadline) == 0


def test_days_remaining_negative_after_deadline():
    assert days_remaining(date(2026, 7, 1), today=date(2026, 8, 5)) == -7