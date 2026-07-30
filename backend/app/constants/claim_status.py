from enum import Enum


class ClaimType(str, Enum):
    EOT = "EOT"
    COST = "Cost"
    EOT_COST = "EOT+Cost"


class ClaimingParty(str, Enum):
    CONTRACTOR = "Contractor"
    EMPLOYER = "Employer"


class ClaimStatus(str, Enum):
    """
    Mirrors the FIDIC 2017 Sub-Clause 20.2 lifecycle. Each transition is
    driven by a dated action (submit_notice, engineer_flag_late_notice,
    submit_detailed_claim, engineer_respond) recorded in claim_service.py,
    so the status always reflects the last thing that actually happened
    rather than a value someone typed in.
    """

    NOTIFIED = "Notified"
    NOTICE_FLAGGED_LATE = "NoticeFlaggedLate"
    DETAILED_CLAIM_SUBMITTED = "DetailedClaimSubmitted"
    AWAITING_ENGINEER_RESPONSE = "AwaitingEngineerResponse"
    AGREED = "Agreed"
    PARTIALLY_AGREED = "PartiallyAgreed"
    DETERMINED = "Determined"
    DEEMED_REJECTED = "DeemedRejected"
    REFERRED_TO_DAAB = "ReferredToDAAB"
    LAPSED = "Lapsed"


class ClaimResponseType(str, Enum):
    ENGINEER_LATE_NOTICE_FLAG = "EngineerLateNoticeFlag"
    REQUEST_FOR_PARTICULARS = "RequestForParticulars"
    AGREEMENT = "Agreement"
    PARTIAL_AGREEMENT = "PartialAgreement"
    DISAGREEMENT = "Disagreement"
    DETERMINATION = "Determination"


class ClaimFactStatus(str, Enum):
    PROPOSED = "Proposed"
    AGREED = "Agreed"
    DISPUTED = "Disputed"
    NEEDS_EVIDENCE = "NeedsEvidence"


class RiskCategory(str, Enum):
    """
    Which party's risk the delay to a programme activity falls under -
    the tag the SCL Protocol's concurrent-delay principle (Core Principle
    on concurrency) is built on: an Employer-Risk delay keeps its full EOT
    entitlement even where a Contractor-Risk delay is independently
    critical over the same period.
    """

    EMPLOYER_RISK = "EmployerRisk"
    CONTRACTOR_RISK = "ContractorRisk"
    NEUTRAL = "Neutral"
