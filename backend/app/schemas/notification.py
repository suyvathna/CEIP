from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, computed_field

from app.constants.notifications import (
    ENGINE_DESCRIPTIONS,
    ENGINE_LABELS,
    engine_for_category,
)


class NotificationOut(BaseModel):
    id: UUID
    project_id: UUID
    user_id: UUID | None
    category: str
    severity: str
    title: str
    body: str | None
    clause_code: str | None
    source_type: str
    source_id: UUID | None
    stage: str | None
    link_path: str | None
    due_date: date | None
    days_remaining: int | None
    is_read: bool
    read_at: datetime | None
    is_resolved: bool
    resolved_at: datetime | None
    resolved_reason: str | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @computed_field
    @property
    def engine(self) -> str:
        """
        "A" or "B" - which logic loop raised this.

        Derived from the category rather than stored, so it can never
        drift out of step with it. Surfaced on every alert because the
        distinction is genuinely hard to see from the alert text: "submit
        the monthly progress report" and "give a Notice of Claim" both
        read as tasks with dates, and the difference between a recurring
        calendar duty and a one-shot time-bar is exactly what tells a PM
        how hard to run.
        """
        return engine_for_category(self.category)

    @computed_field
    @property
    def engine_label(self) -> str:
        return ENGINE_LABELS.get(self.engine, self.engine)


class NotificationSummaryOut(BaseModel):
    total: int
    critical: int
    warning: int
    info: int

    # Split so the bell can say "3 compliance, 2 time-bars" rather than
    # just "5".
    engine_a: int = 0
    engine_b: int = 0


class EngineInfoOut(BaseModel):
    """Reference data so the UI's engine labels and the backend's can
    never disagree about what A and B mean."""

    key: str
    label: str
    description: str


class EnginesOut(BaseModel):
    engines: list[EngineInfoOut]


def engine_reference() -> dict:
    return {
        "engines": [
            {
                "key": key,
                "label": label,
                "description": ENGINE_DESCRIPTIONS[key],
            }
            for key, label in ENGINE_LABELS.items()
        ]
    }


class MarkAllReadOut(BaseModel):
    marked: int
