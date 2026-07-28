from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class EvidenceResponse(BaseModel):
    id: UUID
    event_id: UUID
    filename: str
    object_name: str
    content_type: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)