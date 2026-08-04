"""
Sub-Clause 3.5 instructions and Clause 13 Variation proposals.

The case worth reading these tests for is
test_notice_is_missed_when_work_started_before_it_was_given: under 3.5
the Notice is due "immediately, and before commencing any work related to
the instruction", so a Contractor who has already started is out of time
no matter how many days the calendar says are left. Reporting a soothing
"4 days remaining" there would be worse than reporting nothing.
"""

from datetime import date

from app.constants.variation import DISGUISED_INSTRUCTION_ORIGINS, VariationStatus
from app.services.claim_clock_service import (
    ClaimClockConfig,
    deemed_variation_notice_deadline,
    get_variation_clock,
    variation_proposal_deadline,
)
from app.services.contract_engine import advance_variation

CONFIG = ClaimClockConfig()
RECEIVED = date(2026, 4, 1)


def clock(**overrides):
    kwargs = dict(
        instruction_received_date=RECEIVED,
        is_labelled_as_variation=False,
        notice_given_date=None,
        work_commenced=False,
        work_commenced_date=None,
        proposal_requested_date=None,
        proposal_submitted_date=None,
        config=CONFIG,
        today=date(2026, 4, 3),
    )
    kwargs.update(overrides)
    return get_variation_clock(**kwargs)


def stage(result, name):
    return next((s for s in result["stages"] if s["stage"] == name), None)


# ---------------------------------------------------------------------
# Periods
# ---------------------------------------------------------------------

def test_deemed_variation_notice_window_defaults_to_seven_days():
    assert deemed_variation_notice_deadline(RECEIVED, CONFIG) == date(2026, 4, 8)


def test_proposal_period_defaults_to_28_days():
    assert variation_proposal_deadline(RECEIVED, CONFIG) == date(2026, 4, 29)


def test_periods_follow_project_configuration():
    amended = ClaimClockConfig(
        deemed_variation_notice_days=3, variation_proposal_period_days=14
    )
    assert deemed_variation_notice_deadline(RECEIVED, amended) == date(2026, 4, 4)
    assert variation_proposal_deadline(RECEIVED, amended) == date(2026, 4, 15)


# ---------------------------------------------------------------------
# When the 3.5 stage exists at all
# ---------------------------------------------------------------------

def test_unlabelled_instruction_raises_the_sub_clause_3_5_notice_stage():
    assert stage(clock(), "deemed_variation_notice") is not None


def test_a_properly_labelled_variation_has_no_3_5_notice_stage():
    # The Engineer called it a Variation, so there is nothing for the
    # Contractor to put on record about what it considers the
    # instruction to be.
    result = clock(is_labelled_as_variation=True)
    assert stage(result, "deemed_variation_notice") is None


def test_no_instruction_date_means_no_notice_stage():
    result = clock(instruction_received_date=None)
    assert stage(result, "deemed_variation_notice") is None
    assert result["next_action"] is None


# ---------------------------------------------------------------------
# The "already started work" case
# ---------------------------------------------------------------------

def test_notice_is_missed_when_work_started_before_it_was_given():
    result = clock(work_commenced=True, work_commenced_date=date(2026, 4, 2))

    assert stage(result, "deemed_variation_notice")["status"] == "missed"
    assert result["notice_late_because_work_started"] is True


def test_notice_dated_after_work_commenced_is_missed_even_inside_the_window():
    # Four days into a seven-day alert window, so the naive arithmetic
    # would say "pending". It isn't: the Notice had to come first.
    result = clock(
        notice_given_date=date(2026, 4, 5),
        work_commenced=True,
        work_commenced_date=date(2026, 4, 2),
        today=date(2026, 4, 6),
    )

    assert stage(result, "deemed_variation_notice")["status"] == "missed"
    assert result["notice_late_because_work_started"] is True


def test_notice_before_work_commenced_is_met():
    result = clock(
        notice_given_date=date(2026, 4, 2),
        work_commenced=True,
        work_commenced_date=date(2026, 4, 5),
        today=date(2026, 4, 6),
    )

    assert stage(result, "deemed_variation_notice")["status"] == "met"
    assert result["notice_late_because_work_started"] is False


def test_notice_given_inside_the_window_with_no_work_started_is_met():
    result = clock(notice_given_date=date(2026, 4, 4), today=date(2026, 4, 5))
    assert stage(result, "deemed_variation_notice")["status"] == "met"


# ---------------------------------------------------------------------
# Proposal stage
# ---------------------------------------------------------------------

def test_proposal_runs_from_the_request_where_one_was_made():
    result = clock(proposal_requested_date=date(2026, 4, 10))
    assert stage(result, "variation_proposal")["deadline"] == date(2026, 5, 8)


def test_proposal_falls_back_to_the_instruction_date():
    assert stage(clock(), "variation_proposal")["deadline"] == date(2026, 4, 29)


def test_submitted_proposal_closes_the_stage():
    result = clock(
        proposal_submitted_date=date(2026, 4, 20), today=date(2026, 4, 21)
    )
    assert stage(result, "variation_proposal")["status"] == "met"


# ---------------------------------------------------------------------
# State machine
# ---------------------------------------------------------------------

class FakeVariation:
    def __init__(self, **kwargs):
        self.status = VariationStatus.LOGGED.value
        self.is_labelled_as_variation = False
        self.notice_given_date = None
        self.proposal_requested_date = None
        self.proposal_submitted_date = None
        self.__dict__.update(kwargs)


def test_status_advances_to_notice_given():
    variation = FakeVariation(notice_given_date=date(2026, 4, 3))
    assert advance_variation(variation, clock()) is True
    assert variation.status == VariationStatus.NOTICE_GIVEN.value


def test_status_advances_to_proposal_submitted():
    variation = FakeVariation(
        notice_given_date=date(2026, 4, 3),
        proposal_requested_date=date(2026, 4, 5),
        proposal_submitted_date=date(2026, 4, 20),
    )
    advance_variation(variation, clock())
    assert variation.status == VariationStatus.PROPOSAL_SUBMITTED.value


def test_a_labelled_variation_with_no_notice_is_simply_instructed():
    variation = FakeVariation(is_labelled_as_variation=True)
    advance_variation(variation, clock(is_labelled_as_variation=True))
    assert variation.status == VariationStatus.INSTRUCTED.value


def test_terminal_and_human_decided_states_are_left_alone():
    # Same principle Engine A applies to waived obligations: the machine
    # does not get to overrule a person who has decided the matter.
    for terminal in (
        VariationStatus.VALUED.value,
        VariationStatus.REJECTED.value,
        VariationStatus.WITHDRAWN.value,
        VariationStatus.DISPUTED.value,
    ):
        variation = FakeVariation(
            status=terminal, notice_given_date=date(2026, 4, 3)
        )
        assert advance_variation(variation, clock()) is False
        assert variation.status == terminal


def test_constructive_variations_count_as_disguised_instructions():
    # No instruction was issued at all, so the same immediate-notice
    # requirement applies and the evidential burden is heavier.
    assert "Constructive" in DISGUISED_INSTRUCTION_ORIGINS
    assert "UnlabelledInstruction" in DISGUISED_INSTRUCTION_ORIGINS
    assert "EngineerInstruction" not in DISGUISED_INSTRUCTION_ORIGINS
