from enum import Enum


class EventType(str, Enum):
    # --- Operational / day-to-day categories (not tied to one FIDIC
    # sub-clause on their own) ---
    PROGRESS = "Progress"
    DELAY = "Delay"
    WEATHER = "Weather"
    QUALITY = "Quality"
    SAFETY = "Safety"
    RFI = "RFI"
    INSTRUCTION = "Instruction"
    INSPECTION = "Inspection"
    DELIVERY = "Delivery"
    INCIDENT = "Incident"
    ACCESS_RESTRICTION = "Access Restriction"
    OTHER = "Other"

    # --- FIDIC Red Book 2017 delay/claim grounds - each of these maps to
    # a specific Sub-Clause in app/constants/fidic_clauses.py, which is
    # what drives the "required records" checklist and the Claim's
    # governing-clause auto-tagging. Kept as distinct values (rather than
    # folding them all into the generic "Delay" type above) precisely so
    # that mapping can exist - a generic "Delay" carries no clause
    # information on its own.
    ADVERSE_WEATHER = "Adverse Weather"
    DESIGN_CHANGE_VARIATION = "Design Change / Variation Order"
    DELAYED_DRAWINGS_OR_INSTRUCTIONS = "Delayed Drawings or Instructions"
    LATE_ACCESS_TO_SITE = "Late Access to Site"
    ERRORS_IN_SETTING_OUT = "Errors in Setting-Out Data"
    UNFORESEEABLE_PHYSICAL_CONDITIONS = "Unforeseeable Physical Conditions"
    FOSSILS_ANTIQUITIES = "Fossils / Antiquities"
    ADDITIONAL_TESTING = "Employer-Instructed Additional Testing"
    DELAY_BY_AUTHORITIES = "Delay Caused by Authorities"
    EMPLOYER_SUSPENSION = "Employer's Suspension of Work"
    INTERFERENCE_WITH_TESTS_ON_COMPLETION = "Interference with Tests on Completion"
    CHANGE_IN_LAWS = "Change in Laws"
    EXCEPTIONAL_EVENT = "Exceptional Event (Force Majeure)"
    EPIDEMIC_OR_GOVERNMENT_ACTION_SHORTAGE = "Epidemic / Government Action Shortage"
    CONTRACTOR_SUSPENSION_FOR_NONPAYMENT = "Contractor's Suspension for Non-Payment"
    LATE_PAYMENT_BY_EMPLOYER = "Late Payment by Employer"
    EMPLOYER_DELAY_GENERAL = "Employer-Caused Delay (General)"
