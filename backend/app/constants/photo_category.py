from enum import Enum


class PhotoCategory(str, Enum):
    """
    Buckets a Photos-section attachment into the Daily Log section it
    documents. Manual today, but the same field a camera-API import would
    set automatically once photos start arriving without a person
    tagging each one by hand.
    """

    GENERAL = "General"
    MANPOWER = "Manpower"
    EQUIPMENT = "Equipment"
    DELIVERY = "Delivery"
    INSPECTION = "Inspection"
    HSE = "HSE"
    WEATHER = "Weather"
    VISITOR = "Visitor"
