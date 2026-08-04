from datetime import date
from uuid import UUID

from pydantic import BaseModel, computed_field

from app.constants.notifications import ENGINE_LABELS, engine_for_category


class DeadlineItemOut(BaseModel):
    """
    One live deadline, from whichever engine raised it.

    Flat and source-agnostic on purpose: the dashboard's job is to rank
    everything the Contractor could lose by the date it would lose it,
    not to keep compliance obligations, claims, determinations and
    instructions in separate tidy boxes. A 3.5 notice due tomorrow
    outranks a progress report due next week, and the UI should not have
    to reconcile four different payload shapes to work that out.
    """

    source_type: str
    source_id: UUID
    project_id: UUID
    project_name: str
    category: str
    reference: str | None
    title: str
    stage: str
    stage_label: str
    clause_code: str | None
    deadline: date
    days_remaining: int
    status: str
    severity: str
    link_path: str

    @computed_field
    @property
    def engine(self) -> str:
        """
        "A" (ALWAYS DO - the calendar requires it) or "B" (DO-IN-CASE -
        something happened and a clock started). The single most useful
        thing to know about a deadline before deciding how hard to run.
        """
        return engine_for_category(self.category)

    @computed_field
    @property
    def engine_label(self) -> str:
        return ENGINE_LABELS.get(self.engine, self.engine)


class DeadlineFeedOut(BaseModel):
    generated_for: date
    total: int
    overdue: int
    critical: int

    # How the open deadlines split between the two engines - the headline
    # answer to "how much of this is routine paperwork and how much is a
    # clock running against me".
    engine_a: int = 0
    engine_b: int = 0

    items: list[DeadlineItemOut]
