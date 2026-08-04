"""
Engine A: the rule book and the register's status machine.

plan_obligations is a pure function over a project-shaped object, so
everything the scheduler decides about WHAT is due and WHEN is testable
without a database, a session or a clock.
"""

from datetime import date
from types import SimpleNamespace

import pytest

from app.constants.compliance import ObligationStatus
from app.constants.compliance_rules import RULES_BY_KEY, month_periods
from app.constants.contract_edition import ContractEdition, clause_code
from app.services.compliance_service import compute_status, plan_obligations


def make_project(**overrides):
    """
    Project-shaped test double.

    A real Project() ORM instance would be worse here, not better: its
    server_defaults only materialise on flush, so every period field
    would be None and the test would silently exercise the fallback path
    instead of the values a live row actually carries.
    """
    defaults = dict(
        planned_start=date(2026, 1, 1),
        planned_finish=date(2026, 12, 31),
        contract_edition=ContractEdition.FIDIC_2017.value,
        letter_of_acceptance_date=None,
        taking_over_date=None,
        performance_certificate_date=None,
        defects_notification_period_days=365,
        progress_report_due_days=7,
        statement_due_days=7,
        compliance_alert_lead_days=7,
    )
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


def plan_index(project, today, horizon_days=90):
    return {(p.rule.key, p.period_key): p for p in plan_obligations(project, today, horizon_days)}


# ---------------------------------------------------------------------
# Calendar helpers
# ---------------------------------------------------------------------

def test_month_periods_covers_each_calendar_month_inclusively():
    periods = list(month_periods(date(2026, 1, 15), date(2026, 3, 2)))
    assert [p[0] for p in periods] == ["2026-01", "2026-02", "2026-03"]
    assert periods[0][1] == date(2026, 1, 1)
    assert periods[0][2] == date(2026, 1, 31)


def test_month_periods_handles_february_in_a_leap_year():
    periods = list(month_periods(date(2028, 2, 1), date(2028, 2, 1)))
    assert periods == [("2028-02", date(2028, 2, 1), date(2028, 2, 29))]


def test_month_periods_is_empty_when_the_window_is_inverted():
    assert list(month_periods(date(2026, 5, 1), date(2026, 4, 1))) == []


# ---------------------------------------------------------------------
# Milestone anchoring
# ---------------------------------------------------------------------

def test_no_letter_of_acceptance_means_no_performance_security_obligation():
    # The alternative - quietly anchoring 4.2 on the Commencement Date -
    # would produce a deadline that LOOKS authoritative and is simply
    # wrong. Absent is better than confidently incorrect.
    plans = plan_index(make_project(), today=date(2026, 2, 1))
    assert ("performance_security", "once") not in plans


def test_performance_security_is_28_days_after_the_letter_of_acceptance():
    project = make_project(letter_of_acceptance_date=date(2026, 1, 5))
    plans = plan_index(project, today=date(2026, 2, 1))

    assert plans[("performance_security", "once")].due_date == date(2026, 2, 2)


def test_initial_programme_is_28_days_after_commencement():
    plans = plan_index(make_project(), today=date(2026, 2, 1))
    assert plans[("initial_programme", "once")].due_date == date(2026, 1, 29)


def test_statement_at_completion_is_84_days_after_taking_over():
    project = make_project(taking_over_date=date(2026, 6, 30))
    plans = plan_index(project, today=date(2026, 7, 1))

    assert plans[("statement_at_completion", "once")].due_date == date(2026, 9, 22)


def test_final_statement_is_56_days_after_the_performance_certificate():
    project = make_project(performance_certificate_date=date(2027, 7, 1))
    plans = plan_index(project, today=date(2027, 7, 2))

    assert plans[("final_statement", "once")].due_date == date(2027, 8, 26)


def test_defects_notification_period_end_uses_the_project_configured_length():
    project = make_project(
        taking_over_date=date(2026, 6, 30),
        defects_notification_period_days=730,
    )
    plans = plan_index(project, today=date(2026, 7, 1))

    assert plans[("defects_notification_period_end", "once")].due_date == date(
        2028, 6, 29
    )


# ---------------------------------------------------------------------
# Monthly rules
# ---------------------------------------------------------------------

def test_progress_report_is_due_seven_days_after_the_period_ends():
    plans = plan_index(make_project(), today=date(2026, 3, 15))
    january = plans[("monthly_progress_report", "2026-01")]

    assert january.period_end == date(2026, 1, 31)
    assert january.due_date == date(2026, 2, 7)


def test_progress_report_due_offset_is_project_configurable():
    # MDB Harmonised and amended Particular Conditions move this number
    # routinely, which is exactly why it isn't a constant.
    project = make_project(progress_report_due_days=14)
    plans = plan_index(project, today=date(2026, 3, 15))

    assert plans[("monthly_progress_report", "2026-01")].due_date == date(2026, 2, 14)


def test_monthly_rules_stop_at_the_taking_over_certificate():
    project = make_project(taking_over_date=date(2026, 4, 15))
    plans = plan_index(project, today=date(2026, 8, 1))

    months = {
        period for (key, period) in plans if key == "monthly_progress_report"
    }
    assert months == {"2026-01", "2026-02", "2026-03", "2026-04"}


def test_monthly_rules_keep_generating_when_the_works_overrun():
    # A project past its planned Completion Date with no Taking-Over
    # Certificate still owes monthly reports - and that is precisely the
    # situation where the paperwork matters most, so the register must
    # not quietly stop on the planned finish date.
    project = make_project(
        planned_start=date(2026, 1, 1), planned_finish=date(2026, 3, 31)
    )
    plans = plan_index(project, today=date(2026, 6, 15), horizon_days=0)

    months = {
        period for (key, period) in plans if key == "monthly_progress_report"
    }
    assert "2026-06" in months


def test_monthly_generation_is_bounded_by_the_horizon():
    project = make_project(planned_finish=date(2027, 12, 31))
    plans = plan_index(project, today=date(2026, 1, 1), horizon_days=60)

    months = sorted(
        period for (key, period) in plans if key == "monthly_progress_report"
    )
    assert months[-1] == "2026-03"


# ---------------------------------------------------------------------
# Edition-aware clause numbering
# ---------------------------------------------------------------------

def test_progress_report_clause_number_follows_the_contract_edition():
    # Progress Reports are Sub-Clause 4.20 under the 2017 Red Book and
    # 4.21 under 1999. The platform prints these straight into Notices,
    # so citing the wrong one is a real (if small) own goal.
    assert clause_code("progress_reports", ContractEdition.FIDIC_2017) == "Sub-Clause 4.20"
    assert clause_code("progress_reports", ContractEdition.FIDIC_1999) == "Sub-Clause 4.21"


def test_engineers_instructions_clause_number_follows_the_edition():
    assert clause_code("engineers_instructions", "FIDIC 2017") == "Sub-Clause 3.5"
    assert clause_code("engineers_instructions", "FIDIC 1999") == "Sub-Clause 3.3"


def test_unknown_edition_falls_back_to_2017_rather_than_raising():
    assert clause_code("progress_reports", "FIDIC 1987") == "Sub-Clause 4.20"
    assert clause_code("progress_reports", None) == "Sub-Clause 4.20"


def test_unknown_clause_name_returns_itself_rather_than_raising():
    # An engine must never 500 because a clause label is missing from
    # the lookup table.
    assert clause_code("not_a_real_clause", "FIDIC 2017") == "not_a_real_clause"


# ---------------------------------------------------------------------
# Status machine
# ---------------------------------------------------------------------

def obligation(**overrides):
    defaults = dict(
        status=ObligationStatus.PENDING.value,
        due_date=date(2026, 3, 7),
        submitted_date=None,
    )
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


def test_status_is_pending_well_before_the_deadline():
    assert (
        compute_status(obligation(), today=date(2026, 2, 1), lead_days=7)
        == ObligationStatus.PENDING.value
    )


def test_status_becomes_due_soon_inside_the_lead_window():
    assert (
        compute_status(obligation(), today=date(2026, 3, 1), lead_days=7)
        == ObligationStatus.DUE_SOON.value
    )


def test_the_deadline_day_itself_is_not_yet_overdue():
    # Same boundary the notice deadline tests assert: submitting ON the
    # due date is compliant.
    assert (
        compute_status(obligation(), today=date(2026, 3, 7), lead_days=7)
        == ObligationStatus.DUE_SOON.value
    )


def test_status_is_overdue_the_day_after_the_deadline():
    assert (
        compute_status(obligation(), today=date(2026, 3, 8), lead_days=7)
        == ObligationStatus.OVERDUE.value
    )


def test_submitted_on_the_deadline_day_counts_as_on_time():
    row = obligation(submitted_date=date(2026, 3, 7))
    assert (
        compute_status(row, today=date(2026, 4, 1), lead_days=7)
        == ObligationStatus.SUBMITTED.value
    )


def test_submitted_after_the_deadline_is_recorded_as_late_not_as_met():
    # The same distinction claim_clock_service draws between "met" and
    # "missed": recording it late is honest, not a cure. Flattening the
    # two would let a project look fully compliant when it wasn't.
    row = obligation(submitted_date=date(2026, 3, 9))
    assert (
        compute_status(row, today=date(2026, 4, 1), lead_days=7)
        == ObligationStatus.SUBMITTED_LATE.value
    )


@pytest.mark.parametrize(
    "frozen",
    [ObligationStatus.WAIVED.value, ObligationStatus.SUPERSEDED.value],
)
def test_the_sweep_never_overrules_a_human_decision(frozen):
    row = obligation(status=frozen, due_date=date(2020, 1, 1))
    assert compute_status(row, today=date(2026, 6, 1), lead_days=7) == frozen


# ---------------------------------------------------------------------
# Rule book sanity
# ---------------------------------------------------------------------

def test_every_rule_key_is_unique():
    from app.constants.compliance_rules import COMPLIANCE_RULES

    assert len(RULES_BY_KEY) == len(COMPLIANCE_RULES)


def test_derived_rules_point_at_a_real_parent():
    for rule in RULES_BY_KEY.values():
        if rule.parent_key is not None:
            assert rule.parent_key in RULES_BY_KEY
