"""
Which FIDIC edition a project is actually signed under.

This exists because clause numbers move between editions, and the
platform quotes clause numbers straight into Notices and claim letters -
citing the wrong number in correspondence with the Engineer is the kind
of small error that gets a Contractor's notice argued about.

The two that matter in practice on Cambodian work:

  * 2017 (Red Book 2nd Edition): Progress Reports are Sub-Clause 4.20,
    Engineer's Instructions 3.5, Agreement or Determination 3.7,
    Claims 20.2, EOT 8.5.
  * 1999 (Red Book 1st Edition, still the base of most MDB Harmonised
    Edition contracts on ADB/World Bank/JICA-funded jobs here): Progress
    Reports are Sub-Clause 4.21, Instructions 3.3, Determinations 3.5,
    Claims 20.1, EOT 8.4.

NOTE for the existing app/constants/fidic_clauses.py: that module's
docstring says "2017" but a few of its entries carry 1999 numbering
(Fossils is 4.24 under 1999 and 4.23 under 2017; Progress Reports 4.21
vs 4.20). It is left untouched here on purpose - retagging existing
Events/Claims would rewrite history on live records - but it should be
reconciled against this enum in a follow-up.
"""

from enum import Enum


class ContractEdition(str, Enum):
    FIDIC_2017 = "FIDIC 2017"
    FIDIC_1999 = "FIDIC 1999"


DEFAULT_EDITION = ContractEdition.FIDIC_2017

# Every clause this platform's engines cite by number, in both editions.
# Keyed by a stable internal name so the rest of the codebase never has
# to hardcode a bare clause number anywhere.
CLAUSE_NUMBERS: dict[str, dict[ContractEdition, str]] = {
    "performance_security": {
        ContractEdition.FIDIC_2017: "Sub-Clause 4.2",
        ContractEdition.FIDIC_1999: "Sub-Clause 4.2",
    },
    "contractors_representative": {
        ContractEdition.FIDIC_2017: "Sub-Clause 4.3",
        ContractEdition.FIDIC_1999: "Sub-Clause 4.3",
    },
    "environmental_protection": {
        ContractEdition.FIDIC_2017: "Sub-Clause 4.18",
        ContractEdition.FIDIC_1999: "Sub-Clause 4.18",
    },
    "health_and_safety": {
        ContractEdition.FIDIC_2017: "Sub-Clause 4.8",
        ContractEdition.FIDIC_1999: "Sub-Clause 4.8",
    },
    "quality_management": {
        ContractEdition.FIDIC_2017: "Sub-Clause 4.9",
        ContractEdition.FIDIC_1999: "Sub-Clause 4.9",
    },
    "personnel_and_equipment_records": {
        ContractEdition.FIDIC_2017: "Sub-Clause 6.10",
        ContractEdition.FIDIC_1999: "Sub-Clause 6.10",
    },
    "progress_reports": {
        ContractEdition.FIDIC_2017: "Sub-Clause 4.20",
        ContractEdition.FIDIC_1999: "Sub-Clause 4.21",
    },
    "engineers_instructions": {
        ContractEdition.FIDIC_2017: "Sub-Clause 3.5",
        ContractEdition.FIDIC_1999: "Sub-Clause 3.3",
    },
    "agreement_or_determination": {
        ContractEdition.FIDIC_2017: "Sub-Clause 3.7",
        ContractEdition.FIDIC_1999: "Sub-Clause 3.5",
    },
    "notice_of_dissatisfaction": {
        ContractEdition.FIDIC_2017: "Sub-Clause 3.7.5",
        ContractEdition.FIDIC_1999: "Sub-Clause 20.4",
    },
    "programme": {
        ContractEdition.FIDIC_2017: "Sub-Clause 8.3",
        ContractEdition.FIDIC_1999: "Sub-Clause 8.3",
    },
    "extension_of_time": {
        ContractEdition.FIDIC_2017: "Sub-Clause 8.5",
        ContractEdition.FIDIC_1999: "Sub-Clause 8.4",
    },
    "taking_over": {
        ContractEdition.FIDIC_2017: "Sub-Clause 10.1",
        ContractEdition.FIDIC_1999: "Sub-Clause 10.1",
    },
    "defects_notification_period": {
        ContractEdition.FIDIC_2017: "Sub-Clause 11.1",
        ContractEdition.FIDIC_1999: "Sub-Clause 11.1",
    },
    "performance_certificate": {
        ContractEdition.FIDIC_2017: "Sub-Clause 11.9",
        ContractEdition.FIDIC_1999: "Sub-Clause 11.9",
    },
    "right_to_vary": {
        ContractEdition.FIDIC_2017: "Sub-Clause 13.1",
        ContractEdition.FIDIC_1999: "Sub-Clause 13.1",
    },
    "variation_procedure": {
        ContractEdition.FIDIC_2017: "Sub-Clause 13.3",
        ContractEdition.FIDIC_1999: "Sub-Clause 13.3",
    },
    "advance_payment": {
        ContractEdition.FIDIC_2017: "Sub-Clause 14.2",
        ContractEdition.FIDIC_1999: "Sub-Clause 14.2",
    },
    "schedule_of_payments": {
        ContractEdition.FIDIC_2017: "Sub-Clause 14.4",
        ContractEdition.FIDIC_1999: "Sub-Clause 14.4",
    },
    "application_for_ipc": {
        ContractEdition.FIDIC_2017: "Sub-Clause 14.3",
        ContractEdition.FIDIC_1999: "Sub-Clause 14.3",
    },
    "issue_of_ipc": {
        ContractEdition.FIDIC_2017: "Sub-Clause 14.6",
        ContractEdition.FIDIC_1999: "Sub-Clause 14.6",
    },
    "payment": {
        ContractEdition.FIDIC_2017: "Sub-Clause 14.7",
        ContractEdition.FIDIC_1999: "Sub-Clause 14.7",
    },
    "statement_at_completion": {
        ContractEdition.FIDIC_2017: "Sub-Clause 14.10",
        ContractEdition.FIDIC_1999: "Sub-Clause 14.10",
    },
    "final_statement": {
        ContractEdition.FIDIC_2017: "Sub-Clause 14.11",
        ContractEdition.FIDIC_1999: "Sub-Clause 14.11",
    },
    "insurance": {
        ContractEdition.FIDIC_2017: "Sub-Clause 18.1",
        ContractEdition.FIDIC_1999: "Sub-Clause 18.1",
    },
    "claims": {
        ContractEdition.FIDIC_2017: "Sub-Clause 20.2",
        ContractEdition.FIDIC_1999: "Sub-Clause 20.1",
    },
    "notice_of_claim": {
        ContractEdition.FIDIC_2017: "Sub-Clause 20.2.1",
        ContractEdition.FIDIC_1999: "Sub-Clause 20.1",
    },
    "fully_detailed_claim": {
        ContractEdition.FIDIC_2017: "Sub-Clause 20.2.4",
        ContractEdition.FIDIC_1999: "Sub-Clause 20.1",
    },
    "engineer_late_notice_flag": {
        ContractEdition.FIDIC_2017: "Sub-Clause 20.2.2",
        ContractEdition.FIDIC_1999: "Sub-Clause 20.1",
    },
    "unforeseeable_physical_conditions": {
        ContractEdition.FIDIC_2017: "Sub-Clause 4.12",
        ContractEdition.FIDIC_1999: "Sub-Clause 4.12",
    },
    "fossils": {
        ContractEdition.FIDIC_2017: "Sub-Clause 4.23",
        ContractEdition.FIDIC_1999: "Sub-Clause 4.24",
    },
    "exceptional_event": {
        ContractEdition.FIDIC_2017: "Sub-Clause 18.4",
        ContractEdition.FIDIC_1999: "Sub-Clause 19.2",
    },
    "notice_to_correct": {
        ContractEdition.FIDIC_2017: "Sub-Clause 15.1",
        ContractEdition.FIDIC_1999: "Sub-Clause 15.1",
    },
    "termination_by_employer": {
        ContractEdition.FIDIC_2017: "Sub-Clause 15.2",
        ContractEdition.FIDIC_1999: "Sub-Clause 15.2",
    },
    "suspension_by_contractor": {
        ContractEdition.FIDIC_2017: "Sub-Clause 16.1",
        ContractEdition.FIDIC_1999: "Sub-Clause 16.1",
    },
    "termination_by_contractor": {
        ContractEdition.FIDIC_2017: "Sub-Clause 16.2",
        ContractEdition.FIDIC_1999: "Sub-Clause 16.2",
    },
}


def coerce_edition(value: str | ContractEdition | None) -> ContractEdition:
    """
    Never raises. A project row carrying an unrecognised (or NULL)
    contract_edition falls back to the 2017 default rather than breaking
    every deadline calculation on that project.
    """
    if isinstance(value, ContractEdition):
        return value

    if value:
        for edition in ContractEdition:
            if edition.value == value:
                return edition

    return DEFAULT_EDITION


def clause_code(name: str, edition: str | ContractEdition | None) -> str:
    """
    Resolve an internal clause name to the number as it reads in this
    project's edition. Unknown names return the name itself rather than
    raising - an engine should never 500 because a clause label is
    missing from the table.
    """
    mapping = CLAUSE_NUMBERS.get(name)
    if not mapping:
        return name

    return mapping[coerce_edition(edition)]
