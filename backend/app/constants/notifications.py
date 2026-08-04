"""
Vocabulary for the in-app alert stream both engines write into.

There is exactly one notification table and one severity scale for the
whole platform, so a PM opening the bell menu sees a routine 4.20
progress report sitting next to a Sub-Clause 3.7.5 Notice of
Dissatisfaction that expires in two days, ranked by how badly it will
hurt to miss.
"""

from enum import Enum


class NotificationCategory(str, Enum):
    # Engine A: routine, calendar-driven contract compliance.
    COMPLIANCE = "Compliance"

    # Engine B: Sub-Clause 20.2 claim time-bars.
    CLAIM = "Claim"

    # Engine B: Sub-Clause 3.7 agreement/determination and the NOD window.
    DETERMINATION = "Determination"

    # Engine B: Clause 13 Variations and Sub-Clause 3.5 instructions.
    VARIATION = "Variation"

    # Engine B: a logged Event that is running its own notice clock but
    # has not been turned into a Claim yet.
    EVENT = "Event"


class Engine(str, Enum):
    """
    Which of the two logic loops produced an item.

    Carried on every alert and every deadline-feed row because the
    distinction is genuinely hard to see from the item itself - "submit
    the monthly progress report" and "give a Notice of Claim" both look
    like tasks with dates. The difference is WHY they exist, and that is
    exactly what a PM needs in order to know how to react:

      A ("ALWAYS DO")  - the calendar requires it. It was going to be due
                         whether or not anything happened on site, and it
                         will be due again next month.
      B ("DO-IN-CASE") - something happened, and the contract started a
                         clock. It is one-off, it is usually a time-bar,
                         and missing it destroys a right rather than
                         merely being a breach.
    """

    A = "A"
    B = "B"


ENGINE_LABELS = {
    Engine.A.value: "Engine A · ALWAYS DO",
    Engine.B.value: "Engine B · DO-IN-CASE",
}

ENGINE_DESCRIPTIONS = {
    Engine.A.value: (
        "Routine, calendar-driven contract compliance - due whether or not "
        "anything goes wrong on site."
    ),
    Engine.B.value: (
        "Event-driven contractual clocks - started by something that "
        "happened, and usually a time-bar."
    ),
}


class NotificationSeverity(str, Enum):
    """
    Ordered worst-first by SEVERITY_RANK below. CRITICAL is reserved for
    deadlines whose expiry destroys a right outright (a 20.2.1 notice
    time-bar, a 3.7.5 NOD window closing and making a determination
    final and binding, a 3.5 notice that must be given before work
    starts) - if everything is critical, nothing is.
    """

    CRITICAL = "Critical"
    WARNING = "Warning"
    INFO = "Info"


SEVERITY_RANK = {
    NotificationSeverity.CRITICAL.value: 0,
    NotificationSeverity.WARNING.value: 1,
    NotificationSeverity.INFO.value: 2,
}


# The one place a category is mapped to an engine, so the API, the alert
# stream and the deadline feed can never disagree about which loop an
# item came from.
ENGINE_BY_CATEGORY = {
    NotificationCategory.COMPLIANCE.value: Engine.A.value,
    NotificationCategory.CLAIM.value: Engine.B.value,
    NotificationCategory.DETERMINATION.value: Engine.B.value,
    NotificationCategory.VARIATION.value: Engine.B.value,
    NotificationCategory.EVENT.value: Engine.B.value,
}


def engine_for_category(category: str) -> str:
    return ENGINE_BY_CATEGORY.get(category, Engine.B.value)


def severity_for_days_remaining(
    days_remaining: int,
    lead_days: int,
    *,
    rights_destroying: bool = False,
) -> NotificationSeverity:
    """
    The single place the platform decides how loudly to shout.

    CRITICAL is reserved for deadlines whose expiry destroys a right
    outright - a Sub-Clause 20.2 notice period, a 3.7.5 NOD window, a 3.5
    notice that had to precede the work. Nothing else can reach it, ever.

    The first version of this got it exactly backwards in practice.
    Overdue was treated as CRITICAL regardless of what the obligation
    was, so onboarding one ordinary project - a job that had been running
    five months before anyone typed it into CEIP - produced 24 CRITICAL
    alerts, almost all of them variations on "your progress report was
    late in March". A scale where a late progress report shouts as loudly
    as a lapsed Notice of Dissatisfaction is not a scale, and the module
    docstring above had already said so before the code contradicted it.

    So: a routine obligation that is late is a WARNING. It is a breach,
    it should be recorded and put right, and it is not an emergency.
    """
    if rights_destroying:
        return (
            NotificationSeverity.CRITICAL
            if days_remaining <= lead_days
            else NotificationSeverity.WARNING
        )

    if days_remaining <= lead_days:
        return NotificationSeverity.WARNING

    return NotificationSeverity.INFO
