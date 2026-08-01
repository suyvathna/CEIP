from datetime import date, datetime, time
from uuid import UUID

from pydantic import BaseModel


# --- Daily Snapshot ---------------------------------------------------------

class DailySnapshotSlot(BaseModel):
    time: str
    condition: str | None = None
    temp_c: float | None = None


# --- Observed Weather Conditions --------------------------------------------

class WeatherObservationCreate(BaseModel):
    observed_time: time | None = None
    caused_delay: bool = False
    sky: str | None = None
    temp_avg_c: float | None = None
    precipitation: str | None = None
    wind: str | None = None
    ground_condition: str | None = None
    calamity: str | None = None
    comments: str | None = None


class WeatherObservationResponse(WeatherObservationCreate):
    id: UUID
    model_config = {"from_attributes": True}


# --- Manpower Log ------------------------------------------------------------

class ManpowerEntryCreate(BaseModel):
    company: str | None = None
    trade: str | None = None
    position: str | None = None
    workers_count: int = 0
    hours: float | None = None
    comments: str | None = None


class ManpowerEntryResponse(ManpowerEntryCreate):
    id: UUID
    model_config = {"from_attributes": True}


# --- Equipment Log -------------------------------------------------------------

class EquipmentEntryCreate(BaseModel):
    equipment_name: str
    equipment_type: str | None = None
    hours_operating: float | None = None
    hours_idle: float | None = None
    inspected: bool = False
    inspection_time: time | None = None
    location: str | None = None
    comments: str | None = None


class EquipmentEntryResponse(EquipmentEntryCreate):
    id: UUID
    model_config = {"from_attributes": True}


# --- Delivery Log --------------------------------------------------------------

class DeliveryEntryCreate(BaseModel):
    delivery_time: time | None = None
    delivered_from: str | None = None
    tracking_number: str | None = None
    contents: str | None = None
    comments: str | None = None


class DeliveryEntryResponse(DeliveryEntryCreate):
    id: UUID
    model_config = {"from_attributes": True}


# --- Inspection Log --------------------------------------------------------------

class InspectionEntryCreate(BaseModel):
    start_time: time | None = None
    end_time: time | None = None
    inspection_type: str | None = None
    inspecting_entity: str | None = None
    inspector_name: str | None = None
    location_area: str | None = None
    comments: str | None = None


class InspectionEntryResponse(InspectionEntryCreate):
    id: UUID
    model_config = {"from_attributes": True}


# --- HSE Log -----------------------------------------------------------------------

class HSEEntryCreate(BaseModel):
    entry_time: time | None = None
    category: str | None = None
    description: str | None = None
    action_taken: str | None = None
    reported_by: str | None = None


class HSEEntryResponse(HSEEntryCreate):
    id: UUID
    model_config = {"from_attributes": True}


# --- Visitor Log -------------------------------------------------------------------

class VisitorEntryCreate(BaseModel):
    time_in: time | None = None
    time_out: time | None = None
    visitor_name: str | None = None
    company: str | None = None
    purpose: str | None = None
    host_name: str | None = None


class VisitorEntryResponse(VisitorEntryCreate):
    id: UUID
    model_config = {"from_attributes": True}


# --- Daily Log -----------------------------------------------------------------------

class DailyLogCreate(BaseModel):
    project_id: UUID
    event_id: UUID | None = None
    diary_date: date

    # Weather Report
    temp_low_c: float | None = None
    temp_high_c: float | None = None
    temp_avg_c: float | None = None
    precip_since_midnight_mm: float | None = None
    precip_2_days_ago_mm: float | None = None
    precip_3_days_ago_mm: float | None = None
    humidity_low_pct: int | None = None
    humidity_avg_pct: int | None = None
    humidity_high_pct: int | None = None
    dew_point_c: float | None = None
    wind_avg_kmh: float | None = None
    wind_max_kmh: float | None = None
    wind_gust_kmh: float | None = None

    daily_snapshot: list[DailySnapshotSlot] = []

    # Notes
    work_completed: str | None = None
    delays: str | None = None
    engineer_instruction: str | None = None
    tomorrow_plan: str | None = None
    remarks: str | None = None

    # Narrative overflow
    manpower_notes: str | None = None
    equipment_notes: str | None = None
    materials_notes: str | None = None
    hse_notes: str | None = None
    visitor_notes: str | None = None

    additional_event_ids: list[UUID] = []

    # Structured logs - full replace on every create/update, same pattern
    # already used for additional_event_ids.
    weather_observations: list[WeatherObservationCreate] = []
    manpower_entries: list[ManpowerEntryCreate] = []
    equipment_entries: list[EquipmentEntryCreate] = []
    delivery_entries: list[DeliveryEntryCreate] = []
    inspection_entries: list[InspectionEntryCreate] = []
    hse_entries: list[HSEEntryCreate] = []
    visitor_entries: list[VisitorEntryCreate] = []


class DailyLogResponse(BaseModel):
    id: UUID
    project_id: UUID
    event_id: UUID | None
    diary_date: date

    temp_low_c: float | None
    temp_high_c: float | None
    temp_avg_c: float | None
    precip_since_midnight_mm: float | None
    precip_2_days_ago_mm: float | None
    precip_3_days_ago_mm: float | None
    humidity_low_pct: int | None
    humidity_avg_pct: int | None
    humidity_high_pct: int | None
    dew_point_c: float | None
    wind_avg_kmh: float | None
    wind_max_kmh: float | None
    wind_gust_kmh: float | None

    # Nullable in the database (any Daily Log row that predates this field -
    # i.e. every diary entry migrated from the old flat schema - has NULL
    # here, not []), so this has to accept None even though the API
    # always normalizes it to a list before returning (see
    # daily_log_service._hydrate). Declaring it as list-only here is what
    # previously caused a ResponseValidationError - and a "Failed to
    # fetch" in the browser, since the crash happens after the CORS
    # middleware has already let the request through - for every project
    # with pre-existing Daily Log/Diary entries.
    daily_snapshot: list[DailySnapshotSlot] | None = []

    work_completed: str | None
    delays: str | None
    engineer_instruction: str | None
    tomorrow_plan: str | None
    remarks: str | None

    manpower_notes: str | None
    equipment_notes: str | None
    materials_notes: str | None
    hse_notes: str | None
    visitor_notes: str | None

    created_at: datetime
    updated_at: datetime

    linked_event_ids: list[UUID] = []

    weather_observations: list[WeatherObservationResponse] = []
    manpower_entries: list[ManpowerEntryResponse] = []
    equipment_entries: list[EquipmentEntryResponse] = []
    delivery_entries: list[DeliveryEntryResponse] = []
    inspection_entries: list[InspectionEntryResponse] = []
    hse_entries: list[HSEEntryResponse] = []
    visitor_entries: list[VisitorEntryResponse] = []

    # Convenience totals for the Manpower Log header ("91 Workers | 728.0
    # Man Hours" in the template) - computed, not stored, so they can
    # never drift from the underlying rows.
    total_workers: int = 0
    total_man_hours: float = 0.0

    photo_count: int = 0

    model_config = {
        "from_attributes": True
    }
