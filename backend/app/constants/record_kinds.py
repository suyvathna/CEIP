from enum import Enum


class RecordKind(str, Enum):
    """
    The atomic "did the Contractor actually keep this record" checks the
    required-records checklist (see fidic_clauses.py) is built from. Each
    one has a satisfaction rule in event_requirements_service.py - most
    are "is there Evidence/a Daily Log/a structured log row attached that
    would plausibly serve this purpose", not a rigid single-field check,
    since the goal is prompting the habit, not blocking on exact tagging.
    """

    OFFICIAL_WEATHER_DATA = "official_weather_data"
    DAILY_LOG_HALTED_WORK = "daily_log_halted_work"
    SITE_PHOTOS = "site_photos"
    INSTRUCTION_DOCUMENT = "instruction_document"
    CORRESPONDENCE = "correspondence"
    DELIVERY_RECORD = "delivery_record"
    INSPECTION_RECORD = "inspection_record"
    AUTHORITY_NOTICE = "authority_notice"
    SETTING_OUT_DATA = "setting_out_data"
    SITE_INVESTIGATION_REPORT = "site_investigation_report"
    SUSPENSION_INSTRUCTION = "suspension_instruction"
    PAYMENT_RECORD = "payment_record"
    GENERAL_EVIDENCE = "general_evidence"


RECORD_KIND_LABELS = {
    RecordKind.OFFICIAL_WEATHER_DATA: "Official Weather Data",
    RecordKind.DAILY_LOG_HALTED_WORK: "Daily Log showing halted/affected work",
    RecordKind.SITE_PHOTOS: "Photos of the site",
    RecordKind.INSTRUCTION_DOCUMENT: "Engineer's Instruction / RFI response",
    RecordKind.CORRESPONDENCE: "Correspondence / notice evidence",
    RecordKind.DELIVERY_RECORD: "Delivery Log entry",
    RecordKind.INSPECTION_RECORD: "Inspection Log entry",
    RecordKind.AUTHORITY_NOTICE: "Authority notice / permit correspondence",
    RecordKind.SETTING_OUT_DATA: "Setting-out / survey data",
    RecordKind.SITE_INVESTIGATION_REPORT: "Site investigation report",
    RecordKind.SUSPENSION_INSTRUCTION: "Employer's suspension instruction",
    RecordKind.PAYMENT_RECORD: "IPC / payment record",
    RecordKind.GENERAL_EVIDENCE: "Supporting evidence",
}
