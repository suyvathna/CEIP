"""
Vocabulary for Engine A - the "ALWAYS DO" side of the platform: the
mandatory, time-bound submissions a FIDIC contract requires whether or
not anything goes wrong on site.

Deliberately separate from app.constants.claim_status, which is the
vocabulary of Engine B ("DO-IN-CASE"): a monthly progress report and a
Notice of Claim are both deadlines, but one is a routine calendar
obligation and the other is an event-triggered time-bar, and collapsing
them into one status enum would make both harder to read.
"""

from enum import Enum


class ObligationCadence(str, Enum):
    """How often a rule produces an obligation instance."""

    # Happens once per project, anchored on a contract milestone
    # (Letter of Acceptance, Commencement, Taking-Over, Performance
    # Certificate).
    ONE_OFF = "OneOff"

    # Produces one instance per calendar month over the life of the
    # works (progress reports, Statements, IPCs, payments).
    MONTHLY = "Monthly"


class MilestoneAnchor(str, Enum):
    """The contract date an obligation's deadline is measured from."""

    LETTER_OF_ACCEPTANCE = "LetterOfAcceptance"
    COMMENCEMENT = "Commencement"
    MONTH_END = "MonthEnd"
    TAKING_OVER = "TakingOver"
    PERFORMANCE_CERTIFICATE = "PerformanceCertificate"

    # Measured from another obligation instance in the same period -
    # e.g. the Engineer's IPC (14.6) runs from the date the Contractor's
    # Statement (14.3) was actually submitted, falling back to when it
    # was due if it hasn't been.
    PARENT_OBLIGATION = "ParentObligation"


class ObligationCategory(str, Enum):
    """Grouping for the compliance register's UI, nothing more."""

    MOBILISATION = "Mobilisation"
    REPORTING = "Reporting"
    PROGRAMME = "Programme"
    PAYMENT = "Payment"
    COMPLETION = "Completion"


class OwedBy(str, Enum):
    """
    Who the obligation sits with. The platform is Contractor-side, but
    tracking what the Engineer and Employer owe is the point: a late IPC
    under 14.6 or a late payment under 14.7 is itself claim ground
    (16.1 / 14.8), so those deadlines belong in the same register rather
    than in someone's head.
    """

    CONTRACTOR = "Contractor"
    ENGINEER = "Engineer"
    EMPLOYER = "Employer"


class ObligationStatus(str, Enum):
    """
    Computed on every scheduler tick from the obligation's due date and
    its recorded submission - except WAIVED and SUPERSEDED, which are
    deliberate human decisions the tick must never overwrite.
    """

    # Open, deadline still comfortably ahead.
    PENDING = "Pending"

    # Open, inside the project's alert lead time.
    DUE_SOON = "DueSoon"

    # Deadline passed with nothing recorded.
    OVERDUE = "Overdue"

    # Recorded on or before the deadline.
    SUBMITTED = "Submitted"

    # Recorded, but after the deadline had already passed. Kept distinct
    # from SUBMITTED for the same reason claim_clock_service distinguishes
    # "met" from "missed": recording it late is an honest record, not a
    # cure.
    SUBMITTED_LATE = "SubmittedLate"

    # A human decided this rule doesn't apply to this contract (e.g. no
    # advance payment was agreed, so no 14.2 guarantee is owed). Survives
    # every tick.
    WAIVED = "Waived"

    # The anchoring milestone moved and this instance no longer
    # corresponds to a real period. Kept rather than deleted so the
    # register stays an audit trail.
    SUPERSEDED = "Superseded"


# A HUMAN decision. Nothing the scheduler does may overrule it: if a PM
# says this contract has no advance payment, the sweep does not get to
# argue with them tomorrow morning.
HUMAN_FROZEN_STATUSES = frozenset({ObligationStatus.WAIVED.value})

# A MACHINE decision, and therefore reversible by the machine. Superseded
# means "the anchoring milestone moved and this instance no longer
# corresponds to a real period" - so when the milestone moves back, the
# obligation must come back with it.
#
# This distinction is load-bearing and was got wrong first time round:
# lumping SUPERSEDED in with WAIVED made a mistyped Taking-Over date a
# one-way door. It retired every monthly obligation after that date, and
# correcting the typo did not bring them back, because generation skipped
# frozen rows entirely. The register then looked permanently, inexplicably
# short - and no amount of pressing Rebuild fixed it.
MACHINE_CLOSED_STATUSES = frozenset({ObligationStatus.SUPERSEDED.value})

# Statuses compute_status() must leave exactly as it found them. Both
# kinds qualify: a waived obligation has no deadline to evaluate, and a
# superseded one has no period. The difference is that generation may
# revive the superseded kind and may never revive the waived kind.
FROZEN_STATUSES = HUMAN_FROZEN_STATUSES | MACHINE_CLOSED_STATUSES

# Statuses that still need somebody to do something.
OPEN_STATUSES = frozenset(
    {
        ObligationStatus.PENDING.value,
        ObligationStatus.DUE_SOON.value,
        ObligationStatus.OVERDUE.value,
    }
)

# Statuses where nothing further is owed, so any alert still standing
# against the obligation is stale and should be resolved.
SETTLED_STATUSES = frozenset(
    {
        ObligationStatus.SUBMITTED.value,
        ObligationStatus.SUBMITTED_LATE.value,
        ObligationStatus.WAIVED.value,
        ObligationStatus.SUPERSEDED.value,
    }
)
