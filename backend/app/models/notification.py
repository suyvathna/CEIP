import uuid
from datetime import date, datetime

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Notification(Base):
    """
    One alert in the PM's stream. Both engines write here and nothing
    else does, so the bell menu is the single answer to "what is about to
    hurt me".

    The interesting column is dedupe_key. A scheduler that re-notifies on
    every tick trains people to ignore it within a week, so each alert
    carries a key built from what it is about plus how urgent it has
    become - typically "<source>:<id>:<severity>" or
    "<source>:<id>:<days-bucket>". Re-running the tick on the same day
    is a no-op; a deadline crossing from 10 days out to 2 days out
    produces a genuinely new alert, because the key changed. That is the
    whole escalation mechanism, and it needs no timers or state machine
    of its own.
    """

    __tablename__ = "notifications"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id"),
        nullable=False,
        index=True,
    )

    # Null means project-wide: everyone with access to the project sees
    # it. Per-user targeting exists for a later permissions model (see
    # the note on User.role) without needing another migration then.
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
    )

    category: Mapped[str] = mapped_column(String(30), nullable=False, index=True)

    severity: Mapped[str] = mapped_column(String(20), nullable=False, index=True)

    title: Mapped[str] = mapped_column(String(255), nullable=False)

    body: Mapped[str | None] = mapped_column(Text)

    clause_code: Mapped[str | None] = mapped_column(String(40))

    # What this alert is about: "obligation" | "claim" | "event" |
    # "determination" | "variation". Free text rather than an FK, because
    # a notification must survive the deletion of whatever raised it -
    # an alert history that silently loses rows is not a history.
    source_type: Mapped[str] = mapped_column(String(30), nullable=False)

    source_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))

    # Which deadline on that source this alert is about ("notice",
    # "notice_of_dissatisfaction", "due", ...). Stored as its own column
    # rather than parsed back out of dedupe_key, because it is what
    # identifies the alert for RESOLUTION: raising a fresh alert for a
    # stage, or the deadline being met, retires every earlier live alert
    # on the same (source, stage).
    stage: Mapped[str | None] = mapped_column(String(60), index=True)

    # Frontend route to open when the alert is clicked, e.g.
    # "/projects/<id>/claims/<id>". Built server-side so the client
    # doesn't have to reimplement the routing table per source type.
    link_path: Mapped[str | None] = mapped_column(String(255))

    due_date: Mapped[date | None] = mapped_column(Date)

    days_remaining: Mapped[int | None] = mapped_column(Integer)

    dedupe_key: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True,
        index=True,
    )

    is_read: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default="false",
        index=True,
    )

    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # "Read" is a human saying they've seen it. "Resolved" is the system
    # saying it no longer applies - the report went in, the obligation was
    # waived, the deadline moved and a newer alert replaced this one.
    #
    # Conflating the two was the original mistake: alerts were write-only,
    # so the bell badge could only ever climb. A PM who did everything
    # asked of them still saw 29 unread, which is indistinguishable from a
    # PM who did nothing, and makes the whole stream worthless.
    is_resolved: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default="false",
        index=True,
    )

    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Why it stopped applying - shown in the alert history so a resolved
    # alert reads as "this got done" rather than just vanishing.
    resolved_reason: Mapped[str | None] = mapped_column(String(255))

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        index=True,
    )
