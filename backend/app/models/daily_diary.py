import uuid
from datetime import date, datetime


from sqlalchemy import Date, DateTime, ForeignKey, Integer, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class DailyDiary(Base):
    __tablename__ = "daily_diaries"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    # A site diary is fundamentally a date-based, project-level record -
    # not a child of a single Event. project_id is now the required owner;
    # event_id is kept as an optional "primary related event" for backward
    # compatibility (existing rows were backfilled from their old event's
    # project). Any further events a diary entry turns out to be relevant
    # to are linked via DiaryEventLink instead of forcing a 1:1 shape.
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

    work_completed: Mapped[str | None] = mapped_column(Text)

    manpower: Mapped[int | None] = mapped_column(Integer)

    equipment: Mapped[str | None] = mapped_column(Text)

    materials: Mapped[str | None] = mapped_column(Text)

    delays: Mapped[str | None] = mapped_column(Text)

    safety: Mapped[str | None] = mapped_column(Text)

    visitors: Mapped[str | None] = mapped_column(Text)

    engineer_instruction: Mapped[str | None] = mapped_column(Text)

    tomorrow_plan: Mapped[str | None] = mapped_column(Text)

    remarks: Mapped[str | None] = mapped_column(Text)

    diary_date: Mapped[date] = mapped_column(Date, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )


class DiaryEventLink(Base):
    """
    Many-to-many: a single diary entry commonly touches more than one
    logged Event (e.g. one day's diary mentions a weather delay AND a late
    instruction). event_id on DailyDiary itself only captures one primary
    link; this table captures the rest without forcing a diary to belong
    to just one event.
    """

    __tablename__ = "diary_event_links"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    diary_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("daily_diaries.id"),
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
