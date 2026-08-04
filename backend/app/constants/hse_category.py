from enum import Enum


class HSECategory(str, Enum):
    TOOLBOX_TALK = "Toolbox Talk"
    INCIDENT = "Incident"
    NEAR_MISS = "Near Miss"
    PPE_VIOLATION = "PPE Violation"
    HOUSEKEEPING = "Housekeeping"
    INSPECTION = "Inspection"
    OTHER = "Other"
