from enum import Enum


class EventType(str, Enum):
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
    OTHER = "Other"