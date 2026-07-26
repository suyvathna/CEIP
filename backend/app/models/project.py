import uuid
from datetime import date, datetime

from sqlalchemy import Date, DateTime, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    project_code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)

    project_name: Mapped[str] = mapped_column(String(255), nullable=False)

    client_name: Mapped[str] = mapped_column(String(255), nullable=False)

    contractor_name: Mapped[str | None] = mapped_column(String(255))

    engineer_name: Mapped[str | None] = mapped_column(String(255))

    contract_type: Mapped[str] = mapped_column(String(100), nullable=False)

    country: Mapped[str] = mapped_column(String(100), nullable=False)

    city: Mapped[str] = mapped_column(String(100), nullable=False)

    planned_start: Mapped[date] = mapped_column(Date)

    planned_finish: Mapped[date] = mapped_column(Date)

    status: Mapped[str] = mapped_column(
        String(50),
        default="Planning",
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