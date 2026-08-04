"""
Vocabulary for FIDIC 2017 Sub-Clause 3.7 (1999: Sub-Clause 3.5) -
"Agreement or Determination".

The reason this is its own record type rather than another column on
Claim: 3.7 governs "any matter or Claim", not just Claims. An Engineer
determines valuation disputes, measurement disagreements and rate
adjustments that never became a 20.2 Claim at all, and each of those
still starts a Notice of Dissatisfaction clock that, if missed, makes the
determination final and binding on the Contractor forever.
"""

from enum import Enum


class DeterminationStatus(str, Enum):
    """
    The 3.7 sequence, in order:

      3.7.1  Engineer consults both Parties to try to reach agreement.
      3.7.3  If no agreement within the time limit (42 days from receipt
             of the Claim / of the matter), the Engineer shall make a
             fair determination within a further 42 days.
      3.7.5  A Party who is dissatisfied must give a Notice of
             Dissatisfaction within 28 days of receiving the
             determination. Miss it and the determination becomes final
             and binding - the single most expensive deadline in the
             whole contract, because there is no appeal from it.
    """

    # Matter referred; the Engineer is consulting under 3.7.1.
    UNDER_CONSULTATION = "UnderConsultation"

    # The Parties agreed - binding, and no NOD window arises at all.
    AGREED = "Agreed"

    # No agreement; the Engineer's determination window (3.7.3) is
    # running.
    AWAITING_DETERMINATION = "AwaitingDetermination"

    # Determination issued and received; the 28-day NOD window is open.
    DETERMINED_NOD_OPEN = "DeterminedNodOpen"

    # A Notice of Dissatisfaction was given in time - the matter is live
    # and can go to the DAAB under Clause 21.
    NOD_GIVEN = "NodGiven"

    # The NOD window closed without a Notice. Final and binding.
    FINAL_AND_BINDING = "FinalAndBinding"

    # The Engineer blew the 3.7.3 window entirely. Under 2017 this is
    # deemed a rejection, which itself opens a dispute route - it is not
    # the Contractor's problem to keep waiting.
    DEEMED_REJECTION = "DeemedRejection"


class DeterminationOutcome(str, Enum):
    """What the Engineer actually decided, for reporting."""

    FULLY_IN_FAVOUR = "FullyInFavour"
    PARTIALLY_IN_FAVOUR = "PartiallyInFavour"
    REJECTED = "Rejected"
    NOT_YET_DETERMINED = "NotYetDetermined"


# Statuses where the Contractor still has something to protect.
DETERMINATION_OPEN_STATUSES = frozenset(
    {
        DeterminationStatus.UNDER_CONSULTATION.value,
        DeterminationStatus.AWAITING_DETERMINATION.value,
        DeterminationStatus.DETERMINED_NOD_OPEN.value,
    }
)
