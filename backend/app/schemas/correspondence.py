from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel

from app.constants.correspondence import CorrespondenceDirection, CorrespondenceMethod


class CorrespondenceCreate(BaseModel):
    project_id: UUID
    # Left blank for the common case (auto-generated "COR-001" style, see
    # correspondence_service._next_correspondence_no); editable so a
    # Contractor can tie it to their own transmittal numbering instead,
    # the same convention Event.event_no / Claim.claim_no already follow.
    correspondence_no: str | None = None
    direction: CorrespondenceDirection
    correspondence_date: date
    reference: str | None = None
    subject: str
    method: CorrespondenceMethod | None = None
    related_to: str | None = None
    summary: str | None = None


class CorrespondenceResponse(BaseModel):
    id: UUID
    project_id: UUID
    correspondence_no: str | None
    direction: CorrespondenceDirection
    correspondence_date: date
    reference: str | None
    subject: str
    method: CorrespondenceMethod | None
    related_to: str | None
    summary: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True
    }
