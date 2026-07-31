from enum import Enum


class EventType(str, Enum):
    PROGRESS = "Progress"
    DELAY = "Delay"
    WEATHER = "Weather"
    ADVERSE_WEATHER = "Adverse Weather"
    QUALITY = "Quality"
    SAFETY = "Safety"
    RFI = "RFI"
    INSTRUCTION = "Instruction"
    INSPECTION = "Inspection"
    DELIVERY = "Delivery"
    INCIDENT = "Incident"
    DESIGN_CHANGE_VARIATION = "Design Change / Variation Order"
    ACCESS_RESTRICTION = "Access Restriction"
    OTHER = "Other"