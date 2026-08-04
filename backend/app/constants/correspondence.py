"""
Vocabulary for the Correspondence register - the plain log of letters,
emails and transmittals the Contractor sends to or receives from the
Engineer. The Engineer never uses this platform; every one of these
exchanges happens by outside means (email, post, hand delivery) and this
register only records that it happened.

Deliberately not a clock: unlike Events/Claims/Variations/Determinations,
nothing here dispatches into contract_engine or opens a deadline. See
app.constants.event_driven_rules for the reference table of which FIDIC
notices actually carry a deadline - Correspondence is where a Contractor
records having sent one.
"""

from enum import Enum


class CorrespondenceDirection(str, Enum):
    OUTGOING = "Outgoing"  # Contractor -> Engineer
    INCOMING = "Incoming"  # Engineer -> Contractor


class CorrespondenceMethod(str, Enum):
    EMAIL = "Email"
    LETTER = "Letter"
    FAX = "Fax"
    HAND_DELIVERY = "Hand Delivery"
    SITE_MEMO = "Site Memo"
    OTHER = "Other"
