"""
Computes the "required records" checklist for an Event - the FIDIC-clause
driven prompt described in the roadmap: e.g. for a Weather Delay event,
placeholders demanding Official Weather Data, a Daily Log showing halted
work, and Photos of the site.

Deliberately NOT a stored status table. Every check here is computed at
read time from records that already exist (linked Daily Logs, their
structured child rows, and attached Evidence) - so the checklist can never
drift out of sync with what's actually been attached, and there's no
separate "mark as satisfied" action for a contractor to forget. The
trade-off is that these are necessarily heuristics ("is there a Daily Log
that plausibly documents this"), not exact field-level validation - see
RecordKind's docstring. That's intentional: the goal is prompting the
record-keeping habit and giving the Engineer/PM a fast "is this claim
ready" signal, not blocking on rigid tagging a busy site team won't keep
up with.
"""

from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.constants.fidic_clauses import get_clause_reference, get_required_record_kinds
from app.constants.record_kinds import RECORD_KIND_LABELS, RecordKind
from app.models.daily_log import DailyLog, DailyLogEventLink
from app.models.daily_log_entries import DeliveryEntry, InspectionEntry, WeatherObservation
from app.models.event import Event
from app.models.evidence import Evidence


def _linked_daily_logs(db: Session, event: Event) -> list[DailyLog]:
    """Same "primary event_id OR DailyLogEventLink" rule as daily_log_service.get_logs_for_event."""
    primary = list(db.scalars(select(DailyLog).where(DailyLog.event_id == event.id)).all())

    linked_ids = set(
        db.scalars(
            select(DailyLogEventLink.daily_log_id).where(
                DailyLogEventLink.event_id == event.id
            )
        ).all()
    )
    primary_ids = {d.id for d in primary}
    remaining_ids = linked_ids - primary_ids

    extra = []
    if remaining_ids:
        extra = list(db.scalars(select(DailyLog).where(DailyLog.id.in_(remaining_ids))).all())

    return primary + extra


def _evidence_count(db: Session, event_id: UUID, daily_log_ids: list[UUID]) -> int:
    owner_filter = Evidence.event_id == event_id
    if daily_log_ids:
        owner_filter = or_(owner_filter, Evidence.daily_log_id.in_(daily_log_ids))

    return db.scalar(select(func.count(Evidence.id)).where(owner_filter)) or 0


def _has_weather_report_data(daily_log: DailyLog) -> bool:
    """Weather Report section (the day's summary row) actually filled in, not just left blank."""
    fields = (
        daily_log.temp_low_c,
        daily_log.temp_high_c,
        daily_log.temp_avg_c,
        daily_log.precip_since_midnight_mm,
        daily_log.humidity_avg_pct,
        daily_log.wind_avg_kmh,
    )
    return any(f is not None for f in fields)


def _has_halted_work(db: Session, daily_log: DailyLog) -> bool:
    if daily_log.delays and daily_log.delays.strip():
        return True

    caused_delay = db.scalar(
        select(WeatherObservation.id).where(
            WeatherObservation.daily_log_id == daily_log.id,
            WeatherObservation.caused_delay.is_(True),
        )
    )
    return caused_delay is not None


def _child_rows_exist(db: Session, daily_log_ids: list[UUID], model) -> bool:
    if not daily_log_ids:
        return False
    row = db.scalar(select(model.id).where(model.daily_log_id.in_(daily_log_ids)))
    return row is not None


def get_event_requirements(db: Session, event: Event) -> list[dict]:
    """
    Returns one entry per RecordKind required for this event's event_type,
    each shaped {kind, label, satisfied, detail}. Empty list for event
    types with no FIDIC-driven requirement (e.g. Progress).
    """
    required_kinds = get_required_record_kinds(event.event_type)
    if not required_kinds:
        return []

    daily_logs = _linked_daily_logs(db, event)
    daily_log_ids = [d.id for d in daily_logs]
    evidence_count = _evidence_count(db, event.id, daily_log_ids)
    has_weather_data = any(_has_weather_report_data(d) for d in daily_logs)
    has_halted_work = any(_has_halted_work(db, d) for d in daily_logs)
    has_delivery_rows = _child_rows_exist(db, daily_log_ids, DeliveryEntry)
    has_inspection_rows = _child_rows_exist(db, daily_log_ids, InspectionEntry)
    has_daily_log = len(daily_logs) > 0

    checklist = []
    for kind in required_kinds:
        if kind == RecordKind.OFFICIAL_WEATHER_DATA:
            satisfied = has_weather_data
            detail = (
                "Weather Report section is filled in on at least one linked Daily Log."
                if satisfied
                else "No linked Daily Log has its Weather Report section filled in yet."
            )
        elif kind == RecordKind.DAILY_LOG_HALTED_WORK:
            satisfied = has_halted_work
            detail = (
                "A linked Daily Log records halted/affected work or a weather-caused delay."
                if satisfied
                else "No linked Daily Log notes halted work or a weather-caused delay yet."
            )
        elif kind == RecordKind.SITE_PHOTOS:
            satisfied = evidence_count > 0
            detail = (
                f"{evidence_count} file(s) attached."
                if satisfied
                else "No photos or files attached to this event yet."
            )
        elif kind == RecordKind.DELIVERY_RECORD:
            satisfied = has_delivery_rows
            detail = (
                "A linked Daily Log has a Delivery Log entry."
                if satisfied
                else "No linked Daily Log has a Delivery Log entry yet."
            )
        elif kind == RecordKind.INSPECTION_RECORD:
            satisfied = has_inspection_rows
            detail = (
                "A linked Daily Log has an Inspection Log entry."
                if satisfied
                else "No linked Daily Log has an Inspection Log entry yet."
            )
        elif kind == RecordKind.GENERAL_EVIDENCE:
            satisfied = evidence_count > 0 or has_daily_log
            detail = (
                "Supporting evidence or a linked Daily Log is attached."
                if satisfied
                else "Attach at least one supporting file or Daily Log entry."
            )
        else:
            # INSTRUCTION_DOCUMENT, CORRESPONDENCE, AUTHORITY_NOTICE,
            # SETTING_OUT_DATA, SITE_INVESTIGATION_REPORT,
            # SUSPENSION_INSTRUCTION, PAYMENT_RECORD: no dedicated
            # structured log for these exist in the data model yet, so
            # the heuristic falls back to "is there at least one
            # supporting file attached" per record_kinds.py's docstring.
            satisfied = evidence_count > 0
            detail = (
                f"{evidence_count} file(s) attached."
                if satisfied
                else "No supporting document attached to this event yet."
            )

        checklist.append(
            {
                "kind": kind.value,
                "label": RECORD_KIND_LABELS[kind],
                "satisfied": satisfied,
                "detail": detail,
            }
        )

    return checklist


def get_event_clause_info(event: Event) -> dict | None:
    return get_clause_reference(event.event_type)


def event_requirements_summary(db: Session, event: Event) -> dict:
    checklist = get_event_requirements(db, event)
    return {
        "checklist": checklist,
        "all_satisfied": all(item["satisfied"] for item in checklist),
        "clause_reference": get_event_clause_info(event),
    }
