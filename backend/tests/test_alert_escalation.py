"""
Alert severity and deduplication.

The failure mode being designed against here is not a missing alert - it
is a stream so noisy that people stop reading it. A sweep that
re-announces the same deadline every morning gets muted within a week,
and a muted alert stream is worse than none because everyone believes
they're covered.
"""

from datetime import date

from app.constants.compliance import (
    FROZEN_STATUSES,
    HUMAN_FROZEN_STATUSES,
    MACHINE_CLOSED_STATUSES,
    OPEN_STATUSES,
    SETTLED_STATUSES,
    ObligationStatus,
)
from app.constants.notifications import (
    ENGINE_BY_CATEGORY,
    SEVERITY_RANK,
    Engine,
    NotificationCategory,
    NotificationSeverity,
    engine_for_category,
    severity_for_days_remaining,
)
from app.services.notification_service import build_dedupe_key


LEAD = 7


def test_outside_the_lead_window_is_only_informational():
    assert (
        severity_for_days_remaining(20, LEAD) == NotificationSeverity.INFO
    )


def test_inside_the_lead_window_is_a_warning():
    assert severity_for_days_remaining(5, LEAD) == NotificationSeverity.WARNING


def test_a_routine_obligation_never_reaches_critical():
    # Not even when it is overdue. A late progress report is a breach to
    # be recorded and put right, not an emergency - and treating it as one
    # is what produced 24 CRITICAL alerts on a freshly onboarded project
    # and made the real time-bars impossible to see.
    for days in (2, 0, -1, -90):
        assert (
            severity_for_days_remaining(days, LEAD) == NotificationSeverity.WARNING
        ), days


def test_critical_is_reserved_for_time_bars():
    # There is no gentle version of a reminder about a Sub-Clause 20.2
    # notice period or a 3.7.5 NOD window. Either it is far enough away
    # to be ordinary planning, or it is an emergency.
    assert (
        severity_for_days_remaining(6, LEAD, rights_destroying=True)
        == NotificationSeverity.CRITICAL
    )
    assert (
        severity_for_days_remaining(-1, LEAD, rights_destroying=True)
        == NotificationSeverity.CRITICAL
    )
    assert (
        severity_for_days_remaining(20, LEAD, rights_destroying=True)
        == NotificationSeverity.WARNING
    )


def test_only_rights_destroying_deadlines_can_ever_be_critical():
    # The property that makes the scale mean something: if CRITICAL can
    # be reached by anything routine, a red badge stops carrying
    # information.
    for days in range(-30, 60):
        if severity_for_days_remaining(days, LEAD) == NotificationSeverity.CRITICAL:
            raise AssertionError(f"routine obligation reached CRITICAL at {days} days")


def test_severity_ranking_puts_critical_first():
    ranks = [
        SEVERITY_RANK[NotificationSeverity.CRITICAL.value],
        SEVERITY_RANK[NotificationSeverity.WARNING.value],
        SEVERITY_RANK[NotificationSeverity.INFO.value],
    ]
    assert ranks == sorted(ranks)


# ---------------------------------------------------------------------
# Deduplication and escalation
# ---------------------------------------------------------------------

def test_the_same_alert_on_the_same_day_produces_the_same_key():
    # Re-running the sweep five times must not produce five alerts.
    first = build_dedupe_key("claim", "abc", "notice", "Warning")
    second = build_dedupe_key("claim", "abc", "notice", "Warning")
    assert first == second


def test_escalating_severity_produces_a_new_key():
    # This IS the escalation mechanism - no timers, no per-alert state.
    # A deadline crossing from 10 days out to 2 days out changes the
    # severity, which changes the key, which raises a genuinely new
    # alert.
    warning = build_dedupe_key("claim", "abc", "notice", "Warning")
    critical = build_dedupe_key("claim", "abc", "notice", "Critical")
    assert warning != critical


def test_different_stages_on_one_record_do_not_collide():
    # A claim can be overdue on its notice and approaching its detailed
    # claim deadline at the same time; one must not silently swallow the
    # other.
    notice = build_dedupe_key("claim", "abc", "notice", "Critical")
    detailed = build_dedupe_key("claim", "abc", "detailed_claim", "Critical")
    assert notice != detailed


def test_different_records_do_not_collide():
    assert build_dedupe_key("claim", "abc", "notice", "Critical") != build_dedupe_key(
        "claim", "def", "notice", "Critical"
    )


def test_a_re_dated_deadline_produces_a_new_key():
    # The bug this guards: correcting a contract milestone re-dated an
    # obligation, but the alert key ignored the deadline, so no new alert
    # was raised. The PM was left looking at an alert quoting the OLD
    # date with nothing to indicate anything had changed.
    before = build_dedupe_key("obligation", "abc", "due", "Warning", date(2026, 6, 30))
    after = build_dedupe_key("obligation", "abc", "due", "Warning", date(2026, 8, 9))
    assert before != after


def test_the_same_deadline_still_dedupes():
    assert build_dedupe_key(
        "obligation", "abc", "due", "Warning", date(2026, 6, 30)
    ) == build_dedupe_key("obligation", "abc", "due", "Warning", date(2026, 6, 30))


# ---------------------------------------------------------------------
# Which decisions the sweep may overrule
# ---------------------------------------------------------------------

def test_a_waiver_is_a_human_decision_the_sweep_may_never_undo():
    assert ObligationStatus.WAIVED.value in HUMAN_FROZEN_STATUSES
    assert ObligationStatus.WAIVED.value not in MACHINE_CLOSED_STATUSES


def test_superseded_is_a_machine_decision_and_must_be_reversible():
    # This distinction is the whole fix for a one-way door: a mistyped
    # Taking-Over date retired every monthly obligation after it, and
    # correcting the typo did not bring them back, because generation
    # treated superseded exactly like waived and skipped it forever.
    assert ObligationStatus.SUPERSEDED.value in MACHINE_CLOSED_STATUSES
    assert ObligationStatus.SUPERSEDED.value not in HUMAN_FROZEN_STATUSES


def test_compute_status_still_leaves_both_kinds_alone():
    # Reversible by GENERATION is not the same as recomputed by the
    # status pass - a superseded row has no period to evaluate.
    assert ObligationStatus.WAIVED.value in FROZEN_STATUSES
    assert ObligationStatus.SUPERSEDED.value in FROZEN_STATUSES


def test_every_settled_status_stops_alerting():
    # If a status means "nothing further is owed", any alert still
    # standing against it is stale and must be resolvable.
    assert SETTLED_STATUSES == {
        ObligationStatus.SUBMITTED.value,
        ObligationStatus.SUBMITTED_LATE.value,
        ObligationStatus.WAIVED.value,
        ObligationStatus.SUPERSEDED.value,
    }
    assert not (SETTLED_STATUSES & OPEN_STATUSES)


# ---------------------------------------------------------------------
# Engine attribution
# ---------------------------------------------------------------------

def test_compliance_alerts_are_engine_a_and_everything_else_is_engine_b():
    assert engine_for_category(NotificationCategory.COMPLIANCE.value) == Engine.A.value

    for category in (
        NotificationCategory.CLAIM,
        NotificationCategory.DETERMINATION,
        NotificationCategory.VARIATION,
        NotificationCategory.EVENT,
    ):
        assert engine_for_category(category.value) == Engine.B.value


def test_every_category_is_attributed_to_an_engine():
    for category in NotificationCategory:
        assert category.value in ENGINE_BY_CATEGORY


def test_an_unknown_category_defaults_to_engine_b():
    # Better to over-report something as an event-driven clock than to
    # file a time-bar under routine paperwork.
    assert engine_for_category("SomethingNew") == Engine.B.value
