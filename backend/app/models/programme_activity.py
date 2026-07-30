import uuid
from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Activity(Base):
    """
    A single activity in the project's Accepted Programme (SCL Protocol
    terminology). Phase-1 scope: finish-to-start logic only (see
    ActivityPredecessor), planned + actual dates, no resource/cost
    loading. This is intentionally the simplest model that still supports
    a real forward/backward-pass critical path calculation - see
    services/cpm_service.py.
    """

    __tablename__ = "activities"

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

    activity_code: Mapped[str] = mapped_column(String(50), nullable=False)

    name: Mapped[str] = mapped_column(String(255), nullable=False)

    planned_start: Mapped[date] = mapped_column(Date, nullable=False)

    planned_finish: Mapped[date] = mapped_column(Date, nullable=False)

    actual_start: Mapped[date | None] = mapped_column(Date)

    actual_finish: Mapped[date | None] = mapped_column(Date)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )


class ActivityPredecessor(Base):
    """Finish-to-start dependency: activity_id cannot start until
    predecessor_id finishes."""

    __tablename__ = "activity_predecessors"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    activity_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("activities.id"),
        nullable=False,
    )

    predecessor_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("activities.id"),
        nullable=False,
    )


class EventActivityImpact(Base):
    """
    The causal link between a logged delay Event and a specific programme
    Activity: how many days that event is estimated (or, once agreed via
    a ClaimFact, agreed) to have impacted the activity, and which party's
    risk it falls under. This is the "fragnet" input the CPM/TIA
    calculation in cpm_service.py runs against.
    """

    __tablename__ = "event_activity_impacts"

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

    activity_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("activities.id"),
        nullable=False,
    )

    impact_days: Mapped[int] = mapped_column(Integer, nullable=False)

    risk_category: Mapped[str] = mapped_column(String(20), nullable=False)

    notes: Mapped[str | None] = mapped_column(String(500))

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
