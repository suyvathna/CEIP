from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, computed_field


# Kept short and Cambodia-practical rather than a full ISO 4217 list -
# FIDIC contracts here are overwhelmingly USD-denominated (including
# almost all ADB/World Bank/JICA-funded work), with KHR and THB the
# realistic alternatives on private local jobs.
SUPPORTED_CURRENCIES = ["USD", "KHR", "THB", "EUR"]


class ProjectCreate(BaseModel):
    project_code: str
    project_name: str
    client_name: str
    contractor_name: str | None = None
    engineer_name: str | None = None
    contract_type: str
    contract_no: str | None = None
    site_address: str | None = None
    country: str
    city: str

    # planned_start is the Commencement Date. planned_finish is NOT
    # accepted here - it's always computed server-side as
    # planned_start + duration_days (see project_service.create_project /
    # update_project), so the stored Completion Date can never drift out
    # of sync with the duration the Contractor actually agreed.
    planned_start: date
    duration_days: int = 0

    currency: str = "USD"
    contract_value: float | None = None

    # FIDIC 2017 Sub-Clause 20.2 default periods (days). Left as optional
    # with the unamended FIDIC defaults so creating a project the old way
    # still works; override these when the contract's Particular
    # Conditions (or an MDB Harmonised Edition, common on ADB/World
    # Bank-funded work) amends them. NOTE: since this schema also backs
    # the project update endpoint, an update PUT must resend the
    # project's current period values or they will reset to these
    # defaults - the edit form does this automatically.
    notice_period_days: int = 28
    detailed_claim_period_days: int = 84
    engineer_late_notice_flag_days: int = 14
    engineer_response_period_days: int = 42


class ProjectStatusUpdate(BaseModel):
    # "In Progress" here means "clear the manual override and go back to
    # date-driven auto status" - it's how a project gets taken off
    # "On Hold" again.
    status: str


class ProjectMilestonesUpdate(BaseModel):
    """
    Contract milestones and engine periods, updated through their own
    PATCH rather than through ProjectCreate.

    That separation is deliberate and it fixes a real trap. ProjectCreate
    doubles as the update body, and project_service.update_project
    setattr's every field on it - so any field added there is silently
    reset to its default by an edit form that doesn't resend it (the
    existing note on the Sub-Clause 20.2 periods above says exactly
    this). Putting milestones in that schema would mean a PM editing a
    project's city could blank its Taking-Over Certificate date and
    retire half the compliance register without touching it. Every field
    here is optional and only what's sent gets written.
    """

    contract_edition: str | None = None

    # Contract Data: starts the 28-day clocks for the Performance
    # Security (4.2) and the Advance Payment guarantee (14.2).
    letter_of_acceptance_date: date | None = None

    # Sub-Clause 10.1. Starts the 84-day Statement at Completion clock
    # (14.10) and the Defects Notification Period.
    taking_over_date: date | None = None

    # Sub-Clause 11.9. Starts the 56-day Final Statement clock (14.11).
    performance_certificate_date: date | None = None

    defects_notification_period_days: int | None = None
    progress_report_due_days: int | None = None
    statement_due_days: int | None = None
    engineer_determination_period_days: int | None = None
    nod_period_days: int | None = None
    deemed_variation_notice_days: int | None = None
    variation_proposal_period_days: int | None = None
    compliance_alert_lead_days: int | None = None


class ProjectResponse(ProjectCreate):
    id: UUID
    status: str
    planned_finish: date
    created_at: datetime
    updated_at: datetime

    # Read-only here on purpose - written through
    # PATCH /projects/{id}/milestones, never through the main update
    # body. See ProjectMilestonesUpdate.
    contract_edition: str = "FIDIC 2017"
    letter_of_acceptance_date: date | None = None
    taking_over_date: date | None = None
    performance_certificate_date: date | None = None
    defects_notification_period_days: int = 365
    progress_report_due_days: int = 7
    statement_due_days: int = 7
    engineer_determination_period_days: int = 42
    nod_period_days: int = 28
    deemed_variation_notice_days: int = 7
    variation_proposal_period_days: int = 28
    compliance_alert_lead_days: int = 7

    model_config = ConfigDict(from_attributes=True)

    @computed_field
    @property
    def is_overdue(self) -> bool:
        return (
            self.status == "In Progress"
            and date.today() > self.planned_finish
        )

    @computed_field
    @property
    def days_overdue(self) -> int:
        if not self.is_overdue:
            return 0
        return (date.today() - self.planned_finish).days
