import uuid
from datetime import date, datetime, time

from sqlalchemy import Date, DateTime, ForeignKey, String, Text, Time, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Event(Base):
    __tablename__ = "events"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id"),
        nullable=False,
    )

    # "EVT-001" style, auto-generated sequentially per project (mirrors
    # Claim.claim_no/_next_claim_no) so every Event has a short reference
    # a Contractor can cite in correspondence and a Claim's linked-events
    # list can show, instead of only a UUID.
    event_no: Mapped[str | None] = mapped_column(String(50))

    title: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    event_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )

    event_time: Mapped[time] = mapped_column(
        Time,
        nullable=False,
    )

    event_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    location: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
    )

    severity: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="Low",
    )

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="Open",
    )
    notice_given_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )
    

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )