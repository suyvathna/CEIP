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

    event_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("events.id"),
        nullable=False,
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