"""
Structured child tables for a DailyLog, one per repeatable table in the
reference site-log template: Observed Weather Conditions, Manpower Log,
Equipment Log, Delivery Log, Inspection Log, HSE, and Visitors.

Each row belongs to exactly one DailyLog. These are intentionally simple
(no independent lifecycle, no own API routes) - they're created, replaced,
or removed together with their parent DailyLog, the same "replace on save"
pattern the codebase already uses for DailyLogEventLink.
"""

import uuid
from datetime import datetime, time

from sqlalchemy import Boolean, DateTime, ForeignKey, Numeric, String, Text, Time, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class WeatherObservation(Base):
    """
    "Observed Weather Conditions" - a same-day, timestamped log of what
    actually happened on site (as opposed to the forecast-style Weather
    Report/Daily Snapshot above it). caused_delay is the field that
    matters most for a claim: it's what turns a weather note into
    corroboration for a Sub-Clause 8.5(c) adverse-weather EOT ground.
    """

    __tablename__ = "daily_log_weather_observations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    daily_log_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("daily_logs.id", ondelete="CASCADE"), nullable=False)

    observed_time: Mapped[time | None] = mapped_column(Time)
    caused_delay: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    sky: Mapped[str | None] = mapped_column(String(100))
    temp_avg_c: Mapped[float | None] = mapped_column(Numeric(4, 1))
    precipitation: Mapped[str | None] = mapped_column(String(100))
    wind: Mapped[str | None] = mapped_column(String(100))
    ground_condition: Mapped[str | None] = mapped_column(String(100))
    calamity: Mapped[str | None] = mapped_column(String(100))
    comments: Mapped[str | None] = mapped_column(Text)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ManpowerEntry(Base):
    """One contractor/trade/position row in the Manpower Log."""

    __tablename__ = "daily_log_manpower_entries"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    daily_log_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("daily_logs.id", ondelete="CASCADE"), nullable=False)

    company: Mapped[str | None] = mapped_column(String(200))
    trade: Mapped[str | None] = mapped_column(String(100))
    position: Mapped[str | None] = mapped_column(String(100))
    workers_count: Mapped[int] = mapped_column(nullable=False, server_default="0")
    hours: Mapped[float | None] = mapped_column(Numeric(5, 2))
    comments: Mapped[str | None] = mapped_column(Text)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class EquipmentEntry(Base):
    """One piece-of-equipment row in the Equipment Log."""

    __tablename__ = "daily_log_equipment_entries"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    daily_log_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("daily_logs.id", ondelete="CASCADE"), nullable=False)

    equipment_name: Mapped[str] = mapped_column(String(200), nullable=False)
    equipment_type: Mapped[str | None] = mapped_column(String(100))
    hours_operating: Mapped[float | None] = mapped_column(Numeric(4, 1))
    hours_idle: Mapped[float | None] = mapped_column(Numeric(4, 1))
    inspected: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    inspection_time: Mapped[time | None] = mapped_column(Time)
    location: Mapped[str | None] = mapped_column(String(200))
    comments: Mapped[str | None] = mapped_column(Text)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class DeliveryEntry(Base):
    """One delivery row in the Delivery Log."""

    __tablename__ = "daily_log_delivery_entries"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    daily_log_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("daily_logs.id", ondelete="CASCADE"), nullable=False)

    delivery_time: Mapped[time | None] = mapped_column(Time)
    delivered_from: Mapped[str | None] = mapped_column(String(200))
    tracking_number: Mapped[str | None] = mapped_column(String(100))
    contents: Mapped[str | None] = mapped_column(Text)
    comments: Mapped[str | None] = mapped_column(Text)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class InspectionEntry(Base):
    """One inspection row in the Inspection Log."""

    __tablename__ = "daily_log_inspection_entries"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    daily_log_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("daily_logs.id", ondelete="CASCADE"), nullable=False)

    start_time: Mapped[time | None] = mapped_column(Time)
    end_time: Mapped[time | None] = mapped_column(Time)
    inspection_type: Mapped[str | None] = mapped_column(String(150))
    inspecting_entity: Mapped[str | None] = mapped_column(String(150))
    inspector_name: Mapped[str | None] = mapped_column(String(150))
    location_area: Mapped[str | None] = mapped_column(String(150))
    comments: Mapped[str | None] = mapped_column(Text)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class HSEEntry(Base):
    """
    One HSE row - toolbox talks, incidents, near misses, PPE/housekeeping
    findings. Not in the source template as its own table (those events
    were buried as "(HSE)" notes-log rows), but pulled out into a proper
    log because an HSE incident/near-miss record is exactly the kind of
    contemporaneous evidence that matters for Clause 6 obligations and
    insurance/liability purposes - a free-text note is too easy to lose.
    """

    __tablename__ = "daily_log_hse_entries"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    daily_log_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("daily_logs.id", ondelete="CASCADE"), nullable=False)

    entry_time: Mapped[time | None] = mapped_column(Time)
    category: Mapped[str | None] = mapped_column(String(50))
    description: Mapped[str | None] = mapped_column(Text)
    action_taken: Mapped[str | None] = mapped_column(Text)
    reported_by: Mapped[str | None] = mapped_column(String(150))

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class VisitorEntry(Base):
    """One visitor row in the Visitor Log (Employer, Engineer, authority, etc. site visits)."""

    __tablename__ = "daily_log_visitor_entries"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    daily_log_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("daily_logs.id", ondelete="CASCADE"), nullable=False)

    time_in: Mapped[time | None] = mapped_column(Time)
    time_out: Mapped[time | None] = mapped_column(Time)
    visitor_name: Mapped[str | None] = mapped_column(String(150))
    company: Mapped[str | None] = mapped_column(String(200))
    purpose: Mapped[str | None] = mapped_column(Text)
    host_name: Mapped[str | None] = mapped_column(String(150))

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
