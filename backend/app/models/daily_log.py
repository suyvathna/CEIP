import uuid
from datetime import date, datetime


from sqlalchemy import Date, DateTime, ForeignKey, Numeric, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class DailyLog(Base):
    """
    Formerly "Daily Diary". Renamed to "Daily Log" to match the paper/PDF
    site-diary format Cambodian contractors already produce daily (see
    the project's reference template), and restructured so each of that
    template's sections - Weather Report, Rain Records, Manpower/
    Equipment/Delivery/Inspection logs, HSE, Visitors, Photos - has a real
    home in the data model instead of being flattened into a handful of
    free-text boxes.
    """

    __tablename__ = "daily_logs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    # A site log is fundamentally a date-based, project-level record - not
    # a child of a single Event. project_id is the required owner; event_id
    # is kept as an optional "primary related event" for backward
    # compatibility. Any further events a log entry turns out to be
    # relevant to are linked via DailyLogEventLink instead of forcing a
    # 1:1 shape.
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id"),
        nullable=False,
    )

    event_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("events.id"),
        nullable=True,
    )

    diary_date: Mapped[date] = mapped_column(Date, nullable=False)

    # --- Weather Report -------------------------------------------------
    # One flat row per day. Deliberately just two averages, not a full
    # forecast-style breakdown (low/high/dew/wind/precip-history) - a PM
    # filling this in by hand every day needs the gist, not a weather
    # station log; the rain events that actually matter for a claim are
    # captured with real time windows and photos in WeatherObservation
    # ("Rain Records") below instead.
    temp_avg_c: Mapped[float | None] = mapped_column(Numeric(4, 1))
    humidity_avg_pct: Mapped[int | None] = mapped_column()

    # --- Notes (site activity / plan) -------------------------------------
    work_completed: Mapped[str | None] = mapped_column(Text)
    delays: Mapped[str | None] = mapped_column(Text)
    engineer_instruction: Mapped[str | None] = mapped_column(Text)
    tomorrow_plan: Mapped[str | None] = mapped_column(Text)
    remarks: Mapped[str | None] = mapped_column(Text)

    # --- Narrative overflow for the structured logs below -----------------
    # The structured ManpowerEntry/EquipmentEntry/etc. tables carry the
    # per-row detail the template shows in tables; these free-text fields
    # (renamed from the old flat manpower/equipment/materials/safety/
    # visitors columns) stay as a place for anything that doesn't fit a
    # row - e.g. "night shift crew added from 6pm due to concrete pour".
    manpower_notes: Mapped[str | None] = mapped_column(Text)
    equipment_notes: Mapped[str | None] = mapped_column(Text)
    materials_notes: Mapped[str | None] = mapped_column(Text)
    hse_notes: Mapped[str | None] = mapped_column(Text)
    visitor_notes: Mapped[str | None] = mapped_column(Text)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )


class DailyLogEventLink(Base):
    """
    Many-to-many: a single log entry commonly touches more than one logged
    Event (e.g. one day's log mentions a weather delay AND a late
    instruction). event_id on DailyLog itself only captures one primary
    link; this table captures the rest without forcing a log to belong to
    just one event.
    """

    __tablename__ = "daily_log_event_links"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    daily_log_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("daily_logs.id"),
        nullable=False,
    )

    event_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("events.id"),
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
