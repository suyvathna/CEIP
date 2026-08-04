"""
Vocabulary for Clause 13 (Variations) and its Sub-Clause 3.5 trap.

The trap is the whole reason this record type exists. FIDIC 2017
Sub-Clause 3.5 says that if the Contractor considers an instruction
constitutes a Variation, it shall "immediately, and before commencing
any work related to the instruction", give a Notice to the Engineer.

Engineers routinely issue instructions - by letter, by site memo, by a
marked-up drawing - that change the Works without ever using the word
"Variation". A Contractor who reads it as ordinary direction, gets on
with the work, and only raises it at the next valuation has already lost
the argument: the Notice had to come before the work started. This model
makes "an instruction arrived that was not labelled a Variation" a first
class, alarm-raising record rather than a note in someone's diary.
"""

from enum import Enum


class VariationOrigin(str, Enum):
    # The Engineer instructed it and called it a Variation. Clean path.
    ENGINEER_INSTRUCTION = "EngineerInstruction"

    # The Engineer asked for a proposal before instructing (13.3.2).
    REQUEST_FOR_PROPOSAL = "RequestForProposal"

    # The Contractor proposed it (13.2 Value Engineering).
    VALUE_ENGINEERING = "ValueEngineering"

    # An instruction, drawing revision or written direction that changes
    # the Works but was NOT labelled a Variation. This is the Sub-Clause
    # 3.5 case, and it is the one with the immediate notice requirement.
    UNLABELLED_INSTRUCTION = "UnlabelledInstruction"

    # A change with no instruction at all - the Employer or Engineer
    # simply behaved in a way that varied the Works.
    CONSTRUCTIVE = "Constructive"


class VariationStatus(str, Enum):
    # Logged; if origin is UNLABELLED_INSTRUCTION, the 3.5 notice clock
    # is running and this is the dangerous state to sit in.
    LOGGED = "Logged"

    # Sub-Clause 3.5 Notice given - the Contractor has put on record that
    # it treats the instruction as a Variation.
    NOTICE_GIVEN = "NoticeGiven"

    # The Engineer has asked for (or the Contractor owes) a proposal
    # under 13.3.
    PROPOSAL_DUE = "ProposalDue"

    PROPOSAL_SUBMITTED = "ProposalSubmitted"

    # Instructed/agreed as a Variation - Clause 13 valuation applies.
    INSTRUCTED = "Instructed"

    # Priced and agreed.
    VALUED = "Valued"

    # The Engineer refused to treat it as a Variation. This is not the
    # end of the road: it becomes a Sub-Clause 20.2 Claim, which is why
    # Variation carries a claim_id.
    DISPUTED = "Disputed"

    REJECTED = "Rejected"

    WITHDRAWN = "Withdrawn"


# Origins where an instruction exists but was not labelled a Variation -
# the ones that trigger the immediate Sub-Clause 3.5 notice requirement.
DISGUISED_INSTRUCTION_ORIGINS = frozenset(
    {
        VariationOrigin.UNLABELLED_INSTRUCTION.value,
        VariationOrigin.CONSTRUCTIVE.value,
    }
)

# Statuses where nothing further is owed.
VARIATION_CLOSED_STATUSES = frozenset(
    {
        VariationStatus.VALUED.value,
        VariationStatus.REJECTED.value,
        VariationStatus.WITHDRAWN.value,
    }
)
