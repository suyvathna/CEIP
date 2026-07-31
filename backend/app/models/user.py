import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    full_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
    )

    hashed_password: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    # CEIP has no Engineer login role - this platform is Contractor-side
    # only, and the Engineer never has a User row at all (see the note on
    # ClaimAccessToken for how the Engineer sees a claim instead: a
    # read-only PDF, never platform access). "Contractor" is the only
    # role in use for now; per-company permission tiers (Admin vs. site
    # staff, say) are a later concern, not something this column tries to
    # model yet.
    role: Mapped[str] = mapped_column(
        String(20),
        default="Contractor",
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )