"""
FIDIC Conditions of Contract for Construction, 2nd Edition 2017 ("Red
Book") - the practical claim-ground reference the platform tags Events
and Claims against.

This is deliberately a curated, practically-useful subset (the grounds a
mid-size Cambodian contractor actually runs into) rather than an
exhaustive clause-by-clause commentary, and it assumes the unamended
General Conditions. On MDB Harmonised Edition contracts (common on
ADB/World Bank/JICA-funded work here) and on any contract with amended
Particular Conditions, clause numbers and entitlement bases can differ -
this is a drafting aid, not legal advice, and every auto-tagged clause
should be checked against the actual signed contract before it goes into
a Notice of Claim. See DISCLAIMER below, surfaced wherever this reference
is shown in the UI/PDF output.
"""

from app.constants.event_types import EventType
from app.constants.record_kinds import RecordKind

DISCLAIMER = (
    "Clause references are based on the unamended FIDIC Red Book 2017 "
    "General Conditions and are provided as a drafting aid only - they "
    "are not legal advice. Always verify against this project's actual "
    "Particular Conditions, especially on MDB Harmonised Edition or "
    "otherwise amended contracts, before relying on them in a Notice of "
    "Claim."
)


class EntitlementBasis:
    TIME_ONLY = "Time only"
    COST_ONLY = "Cost only"
    TIME_AND_COST = "Time and Cost"
    TIME_AND_COST_PLUS_PROFIT = "Time and Cost Plus Profit"
    CASE_DEPENDENT = "Time and/or Cost (case-dependent)"


# EventType -> FIDIC clause info. Only event types that map to a specific,
# citable Sub-Clause are included here; purely operational categories
# (Progress, Quality, Safety, RFI, Inspection, Delivery, Incident,
# Instruction, Access Restriction, generic Weather/Delay, Other) are left
# out on purpose - tagging them with a clause they don't actually rest on
# would be worse than not tagging them at all.
FIDIC_CLAUSE_REFERENCE = {
    EventType.ADVERSE_WEATHER: {
        "clause_code": "Sub-Clause 8.5(c)",
        "clause_title": "Extension of Time for Completion - Exceptionally Adverse Climatic Conditions",
        "basis": EntitlementBasis.TIME_ONLY,
        "summary": (
            "Exceptionally adverse climatic conditions (measured against "
            "the norm for the time of year and location) entitle the "
            "Contractor to an Extension of Time under Sub-Clause 8.5(c). "
            "No Cost is recoverable under this ground alone."
        ),
    },
    EventType.DESIGN_CHANGE_VARIATION: {
        "clause_code": "Sub-Clause 13.3",
        "clause_title": "Variation Procedure (right to vary under Sub-Clause 13.1)",
        "basis": EntitlementBasis.TIME_AND_COST,
        "summary": (
            "A Variation instructed or agreed under Clause 13 adjusts the "
            "Time for Completion and the Contract Price by its agreed or "
            "determined valuation under Sub-Clause 13.3.1."
        ),
    },
    EventType.DELAYED_DRAWINGS_OR_INSTRUCTIONS: {
        "clause_code": "Sub-Clause 1.9",
        "clause_title": "Delayed Drawings or Instructions",
        "basis": EntitlementBasis.TIME_AND_COST_PLUS_PROFIT,
        "summary": (
            "If the Engineer fails to issue a notified/required drawing "
            "or instruction within a reasonable time, and the Contractor "
            "suffers delay and/or incurs Cost as a result, the Contractor "
            "is entitled to EOT and Cost Plus Profit."
        ),
    },
    EventType.LATE_ACCESS_TO_SITE: {
        "clause_code": "Sub-Clause 2.1",
        "clause_title": "Right of Access to the Site",
        "basis": EntitlementBasis.TIME_AND_COST_PLUS_PROFIT,
        "summary": (
            "If the Employer fails to give the Contractor right of access "
            "to, and possession of, the Site within the time stated in "
            "the Contract Data (or a reasonable time), the Contractor is "
            "entitled to EOT and Cost Plus Profit."
        ),
    },
    EventType.ERRORS_IN_SETTING_OUT: {
        "clause_code": "Sub-Clause 4.7",
        "clause_title": "Setting Out",
        "basis": EntitlementBasis.TIME_AND_COST,
        "summary": (
            "If items of reference (levels, positions, dimensions) "
            "furnished by the Employer contain an error that an "
            "experienced contractor could not reasonably have "
            "discovered, and this causes the Contractor delay and/or "
            "Cost, the Contractor is entitled to EOT and Cost."
        ),
    },
    EventType.UNFORESEEABLE_PHYSICAL_CONDITIONS: {
        "clause_code": "Sub-Clause 4.12",
        "clause_title": "Unforeseeable Physical Conditions",
        "basis": EntitlementBasis.TIME_AND_COST,
        "summary": (
            "Physical conditions (excluding climatic conditions) that an "
            "experienced contractor could not reasonably have foreseen "
            "entitle the Contractor to EOT and Cost (no profit) once the "
            "Sub-Clause 4.12 notice and Engineer's determination process "
            "is followed."
        ),
    },
    EventType.FOSSILS_ANTIQUITIES: {
        "clause_code": "Sub-Clause 4.24",
        "clause_title": "Fossils",
        "basis": EntitlementBasis.TIME_AND_COST,
        "summary": (
            "Fossils, coins, articles of value or antiquity, and other "
            "items of geological/archaeological interest found on Site "
            "are the Employer's property; delay and Cost from the "
            "resulting suspension/handling are recoverable by the "
            "Contractor."
        ),
    },
    EventType.ADDITIONAL_TESTING: {
        "clause_code": "Sub-Clause 7.4",
        "clause_title": "Testing",
        "basis": EntitlementBasis.TIME_AND_COST_PLUS_PROFIT,
        "summary": (
            "Where the Engineer instructs a test not provided for in the "
            "Specification and the test shows the Plant, Materials or "
            "workmanship were not defective, the resulting delay and Cost "
            "Plus Profit are recoverable by the Contractor."
        ),
    },
    EventType.DELAY_BY_AUTHORITIES: {
        "clause_code": "Sub-Clause 8.6",
        "clause_title": "Delays Caused by Authorities",
        "basis": EntitlementBasis.TIME_AND_COST,
        "summary": (
            "Delay caused by relevant statutory/public authorities in the "
            "Country, despite the Contractor having diligently followed "
            "their procedures, entitles the Contractor to EOT and Cost."
        ),
    },
    EventType.EMPLOYER_SUSPENSION: {
        "clause_code": "Sub-Clause 8.9",
        "clause_title": "Employer's Suspension",
        "basis": EntitlementBasis.TIME_AND_COST,
        "summary": (
            "Suspension instructed by the Engineer/Employer (other than "
            "for Contractor default or weather/safety reasons under "
            "8.9.2) entitles the Contractor to EOT and the Cost of the "
            "suspension under Sub-Clauses 8.10-8.11."
        ),
    },
    EventType.INTERFERENCE_WITH_TESTS_ON_COMPLETION: {
        "clause_code": "Sub-Clause 10.3",
        "clause_title": "Interference with Tests on Completion",
        "basis": EntitlementBasis.TIME_AND_COST_PLUS_PROFIT,
        "summary": (
            "If the Employer prevents the Contractor from carrying out "
            "Tests on Completion for more than 14 days, the Contractor is "
            "entitled to EOT and Cost Plus Profit, and the Works are "
            "treated as passed for Taking-Over purposes if applicable."
        ),
    },
    EventType.CHANGE_IN_LAWS: {
        "clause_code": "Sub-Clause 13.6",
        "clause_title": "Adjustments for Changes in Laws",
        "basis": EntitlementBasis.TIME_AND_COST,
        "summary": (
            "A change in the Laws of the Country (or their interpretation "
            "or application) after the Base Date that affects the "
            "Contractor's performance entitles an adjustment of Time for "
            "Completion and Cost."
        ),
    },
    EventType.EXCEPTIONAL_EVENT: {
        "clause_code": "Sub-Clause 18.4",
        "clause_title": "Consequences of an Exceptional Event (Clause 18)",
        "basis": EntitlementBasis.CASE_DEPENDENT,
        "summary": (
            "An Exceptional Event (formerly 'Force Majeure') preventing "
            "performance entitles EOT if completion is or will be "
            "delayed. Cost is recoverable only for specific categories "
            "of Exceptional Event under Sub-Clause 18.1 - most weather, "
            "epidemic, and general economic events do not carry Cost "
            "entitlement. Identify the specific 18.1 category relied on."
        ),
    },
    EventType.EPIDEMIC_OR_GOVERNMENT_ACTION_SHORTAGE: {
        "clause_code": "Sub-Clause 8.5(e)",
        "clause_title": "Extension of Time for Completion - Epidemic / Governmental Action Shortage",
        "basis": EntitlementBasis.TIME_ONLY,
        "summary": (
            "An unforeseeable shortage in the availability of personnel "
            "or goods caused by epidemic or governmental actions entitles "
            "the Contractor to EOT. No Cost is recoverable under this "
            "ground alone."
        ),
    },
    EventType.CONTRACTOR_SUSPENSION_FOR_NONPAYMENT: {
        "clause_code": "Sub-Clause 16.1",
        "clause_title": "Contractor's Entitlement to Suspend Work",
        "basis": EntitlementBasis.TIME_AND_COST_PLUS_PROFIT,
        "summary": (
            "Where the Employer fails to pay an amount due (after the "
            "notice required by 16.1) or otherwise substantially fails to "
            "perform, the Contractor may suspend work and is entitled to "
            "EOT and Cost Plus Profit for the consequences."
        ),
    },
    EventType.LATE_PAYMENT_BY_EMPLOYER: {
        "clause_code": "Sub-Clause 14.8",
        "clause_title": "Delayed Payment",
        "basis": EntitlementBasis.COST_ONLY,
        "summary": (
            "Financing charges compound monthly on any amount not paid "
            "within the Sub-Clause 14.7 payment period. This is a Cost-"
            "only entitlement - it does not itself extend the Time for "
            "Completion (see Sub-Clause 16.1 if payment failure is severe "
            "enough to justify suspension)."
        ),
    },
    EventType.EMPLOYER_DELAY_GENERAL: {
        "clause_code": "Sub-Clause 8.5(b)",
        "clause_title": "Extension of Time for Completion - other Sub-Clause grounds",
        "basis": EntitlementBasis.CASE_DEPENDENT,
        "summary": (
            "Sub-Clause 8.5(b) picks up any other cause of delay that "
            "gives an EOT entitlement under a specific Sub-Clause of "
            "these Conditions. Use this only as a placeholder until the "
            "actual underlying Sub-Clause is identified - re-tag the "
            "event/claim to the specific ground above once known."
        ),
    },
}


# EventType -> required record kinds for the "does this Event have what a
# claim built on it would need" checklist. Deliberately broader than just
# the FIDIC-tagged types above - even a routine Inspection or Delivery
# event benefits from a reminder of what should be attached.
EVENT_TYPE_REQUIRED_RECORDS = {
    EventType.PROGRESS: [],
    EventType.DELAY: [RecordKind.DAILY_LOG_HALTED_WORK, RecordKind.SITE_PHOTOS],
    EventType.WEATHER: [RecordKind.OFFICIAL_WEATHER_DATA, RecordKind.SITE_PHOTOS],
    EventType.QUALITY: [RecordKind.SITE_PHOTOS, RecordKind.INSPECTION_RECORD],
    EventType.SAFETY: [RecordKind.SITE_PHOTOS, RecordKind.GENERAL_EVIDENCE],
    EventType.RFI: [RecordKind.CORRESPONDENCE],
    EventType.INSTRUCTION: [RecordKind.INSTRUCTION_DOCUMENT],
    EventType.INSPECTION: [RecordKind.INSPECTION_RECORD],
    EventType.DELIVERY: [RecordKind.DELIVERY_RECORD],
    EventType.INCIDENT: [RecordKind.SITE_PHOTOS, RecordKind.GENERAL_EVIDENCE],
    EventType.ACCESS_RESTRICTION: [RecordKind.SITE_PHOTOS, RecordKind.CORRESPONDENCE],
    EventType.OTHER: [RecordKind.GENERAL_EVIDENCE],
    EventType.ADVERSE_WEATHER: [
        RecordKind.OFFICIAL_WEATHER_DATA,
        RecordKind.DAILY_LOG_HALTED_WORK,
        RecordKind.SITE_PHOTOS,
    ],
    EventType.DESIGN_CHANGE_VARIATION: [
        RecordKind.INSTRUCTION_DOCUMENT,
        RecordKind.GENERAL_EVIDENCE,
    ],
    EventType.DELAYED_DRAWINGS_OR_INSTRUCTIONS: [
        RecordKind.CORRESPONDENCE,
        RecordKind.INSTRUCTION_DOCUMENT,
    ],
    EventType.LATE_ACCESS_TO_SITE: [
        RecordKind.CORRESPONDENCE,
        RecordKind.SITE_PHOTOS,
        RecordKind.DAILY_LOG_HALTED_WORK,
    ],
    EventType.ERRORS_IN_SETTING_OUT: [
        RecordKind.SETTING_OUT_DATA,
        RecordKind.SITE_PHOTOS,
        RecordKind.CORRESPONDENCE,
    ],
    EventType.UNFORESEEABLE_PHYSICAL_CONDITIONS: [
        RecordKind.SITE_INVESTIGATION_REPORT,
        RecordKind.SITE_PHOTOS,
        RecordKind.CORRESPONDENCE,
    ],
    EventType.FOSSILS_ANTIQUITIES: [RecordKind.SITE_PHOTOS, RecordKind.CORRESPONDENCE],
    EventType.ADDITIONAL_TESTING: [
        RecordKind.INSPECTION_RECORD,
        RecordKind.INSTRUCTION_DOCUMENT,
    ],
    EventType.DELAY_BY_AUTHORITIES: [
        RecordKind.AUTHORITY_NOTICE,
        RecordKind.CORRESPONDENCE,
        RecordKind.DAILY_LOG_HALTED_WORK,
    ],
    EventType.EMPLOYER_SUSPENSION: [
        RecordKind.SUSPENSION_INSTRUCTION,
        RecordKind.DAILY_LOG_HALTED_WORK,
    ],
    EventType.INTERFERENCE_WITH_TESTS_ON_COMPLETION: [
        RecordKind.INSPECTION_RECORD,
        RecordKind.CORRESPONDENCE,
    ],
    EventType.CHANGE_IN_LAWS: [RecordKind.CORRESPONDENCE, RecordKind.GENERAL_EVIDENCE],
    EventType.EXCEPTIONAL_EVENT: [
        RecordKind.SITE_PHOTOS,
        RecordKind.DAILY_LOG_HALTED_WORK,
        RecordKind.CORRESPONDENCE,
    ],
    EventType.EPIDEMIC_OR_GOVERNMENT_ACTION_SHORTAGE: [
        RecordKind.AUTHORITY_NOTICE,
        RecordKind.DAILY_LOG_HALTED_WORK,
    ],
    EventType.CONTRACTOR_SUSPENSION_FOR_NONPAYMENT: [
        RecordKind.PAYMENT_RECORD,
        RecordKind.CORRESPONDENCE,
    ],
    EventType.LATE_PAYMENT_BY_EMPLOYER: [
        RecordKind.PAYMENT_RECORD,
        RecordKind.CORRESPONDENCE,
    ],
    EventType.EMPLOYER_DELAY_GENERAL: [
        RecordKind.DAILY_LOG_HALTED_WORK,
        RecordKind.CORRESPONDENCE,
        RecordKind.SITE_PHOTOS,
    ],
}


def get_clause_reference(event_type: str) -> dict | None:
    return FIDIC_CLAUSE_REFERENCE.get(event_type)


def get_required_record_kinds(event_type: str) -> list:
    return EVENT_TYPE_REQUIRED_RECORDS.get(event_type, [])
