"""
Sub-Clause 3.7 - Agreement or Determination, and the 28-day Notice of
Dissatisfaction window that follows it.

This is the most consequential clock in the platform. Everything else it
tracks costs money when missed; this one costs the right to argue at all,
because a determination nobody objected to in time is final and binding
and cannot be reopened before the DAAB or in arbitration.
"""

from datetime import date, timedelta

from app.services.claim_clock_service import (
    ClaimClockConfig,
    agreement_deadline,
    determination_deadline,
    get_determination_clock,
    is_final_and_binding,
    nod_deadline,
)

CONFIG = ClaimClockConfig()

REFERRED = date(2026, 3, 1)


def stage(clock, name):
    return next((s for s in clock["stages"] if s["stage"] == name), None)


# ---------------------------------------------------------------------
# The three periods
# ---------------------------------------------------------------------

def test_agreement_time_limit_is_42_days_from_referral():
    assert agreement_deadline(REFERRED, CONFIG) == date(2026, 4, 12)


def test_determination_is_due_a_further_42_days_after_the_agreement_limit():
    # The trap this guards against: reading 3.7.3 as "42 days from
    # referral" for the determination too. It is 42 days AFTER the time
    # limit for agreement - 84 from referral on unamended terms - and a
    # Contractor who escalates at day 43 is escalating early.
    assert determination_deadline(REFERRED, CONFIG) == date(2026, 5, 24)
    assert (determination_deadline(REFERRED, CONFIG) - REFERRED).days == 84


def test_nod_window_is_28_days_from_receipt():
    assert nod_deadline(date(2026, 6, 1), CONFIG) == date(2026, 6, 29)


def test_periods_follow_project_configuration():
    amended = ClaimClockConfig(
        engineer_response_period_days=30,
        engineer_determination_period_days=30,
        nod_period_days=14,
    )
    assert agreement_deadline(REFERRED, amended) == date(2026, 3, 31)
    assert determination_deadline(REFERRED, amended) == date(2026, 4, 30)
    assert nod_deadline(date(2026, 6, 1), amended) == date(2026, 6, 15)


# ---------------------------------------------------------------------
# The clock's shape as the process unfolds
# ---------------------------------------------------------------------

def test_only_the_agreement_stage_exists_before_anything_happens():
    clock = get_determination_clock(
        referred_date=REFERRED,
        agreement_reached_date=None,
        determination_notice_date=None,
        determination_received_date=None,
        nod_given_date=None,
        config=CONFIG,
        today=date(2026, 3, 10),
    )

    assert [s["stage"] for s in clock["stages"]] == [
        "engineer_agreement",
        "engineer_determination",
    ]
    assert clock["next_action"]["stage"] == "engineer_agreement"


def test_agreement_ends_the_process_and_opens_no_nod_window():
    # An agreement under 3.7.2 is binding. There is nothing to be
    # dissatisfied about, so the platform must stop watching for a NOD
    # that will never be due.
    clock = get_determination_clock(
        referred_date=REFERRED,
        agreement_reached_date=date(2026, 3, 20),
        determination_notice_date=None,
        determination_received_date=None,
        nod_given_date=None,
        config=CONFIG,
        today=date(2026, 4, 1),
    )

    assert [s["stage"] for s in clock["stages"]] == ["engineer_agreement"]
    assert clock["next_action"] is None


def test_a_lapsed_agreement_window_is_closed_not_overdue():
    # Failing to reach agreement within the 3.7.3 time limit is the
    # ORDINARY path through 3.7 - it is nobody's breach, it just hands
    # the matter to the Engineer to determine. Marking it "overdue" would
    # leave it permanently first in the queue of open stages and mask the
    # deadline that actually matters by then.
    result = get_determination_clock(
        referred_date=REFERRED,
        agreement_reached_date=None,
        determination_notice_date=None,
        determination_received_date=None,
        nod_given_date=None,
        config=CONFIG,
        today=date(2026, 5, 1),
    )

    assert stage(result, "engineer_agreement")["status"] == "window_closed"
    assert result["next_action"]["stage"] == "engineer_determination"


def test_an_issued_determination_closes_the_agreement_window_early():
    # The Engineer determined on day 20, well inside the 42-day
    # consultation window. No agreement was reached - that is what a
    # determination MEANS - so the agreement stage must close, even
    # though its deadline has not passed.
    #
    # Leaving it open had a nasty consequence: its deadline (day 42) fell
    # slightly earlier than the NOD deadline, so it won the "next action"
    # comparison and hid the Notice of Dissatisfaction window completely -
    # the most expensive deadline in the contract, masked by a stage that
    # events had already overtaken, and downgraded to WARNING with it.
    issued = REFERRED + timedelta(days=20)
    result = get_determination_clock(
        referred_date=REFERRED,
        agreement_reached_date=None,
        determination_notice_date=issued,
        determination_received_date=issued + timedelta(days=2),
        nod_given_date=None,
        config=CONFIG,
        today=issued + timedelta(days=5),
    )

    assert stage(result, "engineer_agreement")["status"] == "window_closed"
    assert result["next_action"]["stage"] == "notice_of_dissatisfaction"


def test_the_nod_window_becomes_the_next_action_once_open():
    result = get_determination_clock(
        referred_date=REFERRED,
        agreement_reached_date=None,
        determination_notice_date=date(2026, 5, 1),
        determination_received_date=date(2026, 5, 1),
        nod_given_date=None,
        config=CONFIG,
        today=date(2026, 5, 10),
    )

    assert result["next_action"]["stage"] == "notice_of_dissatisfaction"


def test_nod_stage_appears_only_once_a_determination_has_been_received():
    clock = get_determination_clock(
        referred_date=REFERRED,
        agreement_reached_date=None,
        determination_notice_date=date(2026, 5, 1),
        determination_received_date=None,
        nod_given_date=None,
        config=CONFIG,
        today=date(2026, 5, 5),
    )
    assert stage(clock, "notice_of_dissatisfaction") is None

    clock = get_determination_clock(
        referred_date=REFERRED,
        agreement_reached_date=None,
        determination_notice_date=date(2026, 5, 1),
        determination_received_date=date(2026, 5, 8),
        nod_given_date=None,
        config=CONFIG,
        today=date(2026, 5, 10),
    )
    assert stage(clock, "notice_of_dissatisfaction")["deadline"] == date(2026, 6, 5)


def test_nod_clock_runs_from_receipt_not_from_the_date_on_the_letter():
    # The whole reason both dates are stored. An Engineer's Notice dated
    # the 1st that reaches site on the 9th leaves 28 days from the 9th -
    # running it from the letter date would silently eat eight of them,
    # with no relief afterwards.
    clock = get_determination_clock(
        referred_date=REFERRED,
        agreement_reached_date=None,
        determination_notice_date=date(2026, 5, 1),
        determination_received_date=date(2026, 5, 9),
        nod_given_date=None,
        config=CONFIG,
        today=date(2026, 5, 10),
    )

    assert stage(clock, "notice_of_dissatisfaction")["deadline"] == date(2026, 6, 6)


def test_nod_given_in_time_is_recorded_as_met():
    clock = get_determination_clock(
        referred_date=REFERRED,
        agreement_reached_date=None,
        determination_notice_date=date(2026, 5, 1),
        determination_received_date=date(2026, 5, 1),
        nod_given_date=date(2026, 5, 20),
        config=CONFIG,
        today=date(2026, 6, 10),
    )

    assert stage(clock, "notice_of_dissatisfaction")["status"] == "met"


def test_nod_given_after_the_window_is_recorded_as_missed_not_as_met():
    clock = get_determination_clock(
        referred_date=REFERRED,
        agreement_reached_date=None,
        determination_notice_date=date(2026, 5, 1),
        determination_received_date=date(2026, 5, 1),
        nod_given_date=date(2026, 6, 3),
        config=CONFIG,
        today=date(2026, 6, 10),
    )

    assert stage(clock, "notice_of_dissatisfaction")["status"] == "missed"


# ---------------------------------------------------------------------
# Final and binding - the boundary that matters most
# ---------------------------------------------------------------------

def test_not_final_on_the_deadline_day_itself():
    received = date(2026, 5, 1)
    deadline = nod_deadline(received, CONFIG)

    assert (
        is_final_and_binding(
            determination_received_date=received,
            nod_given_date=None,
            config=CONFIG,
            today=deadline,
        )
        is False
    )


def test_final_the_day_after_the_window_closes():
    received = date(2026, 5, 1)
    deadline = nod_deadline(received, CONFIG)

    assert (
        is_final_and_binding(
            determination_received_date=received,
            nod_given_date=None,
            config=CONFIG,
            today=deadline + timedelta(days=1),
        )
        is True
    )


def test_a_notice_given_in_time_keeps_the_matter_alive():
    assert (
        is_final_and_binding(
            determination_received_date=date(2026, 5, 1),
            nod_given_date=date(2026, 5, 15),
            config=CONFIG,
            today=date(2027, 1, 1),
        )
        is False
    )


def test_nothing_is_final_before_a_determination_has_been_received():
    assert (
        is_final_and_binding(
            determination_received_date=None,
            nod_given_date=None,
            config=CONFIG,
            today=date(2030, 1, 1),
        )
        is False
    )


# ---------------------------------------------------------------------
# Risk flagging
# ---------------------------------------------------------------------

def test_at_risk_uses_the_projects_own_lead_time():
    received = date(2026, 5, 1)
    eight_days_out = nod_deadline(received, CONFIG) - timedelta(days=8)

    def clock_at(lead_days):
        return get_determination_clock(
            referred_date=REFERRED,
            agreement_reached_date=None,
            determination_notice_date=received,
            determination_received_date=received,
            nod_given_date=None,
            config=ClaimClockConfig(alert_lead_days=lead_days),
            today=eight_days_out,
        )

    assert clock_at(7)["at_risk"] is False
    assert clock_at(14)["at_risk"] is True


def test_days_remaining_goes_negative_once_the_window_has_closed():
    received = date(2026, 5, 1)
    clock = get_determination_clock(
        referred_date=REFERRED,
        agreement_reached_date=None,
        determination_notice_date=received,
        determination_received_date=received,
        nod_given_date=None,
        config=CONFIG,
        today=nod_deadline(received, CONFIG) + timedelta(days=3),
    )

    assert clock["days_remaining"] == -3
