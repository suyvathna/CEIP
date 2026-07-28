from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class EvidenceSearchItem(BaseModel):
    id: UUID
    event_id: UUID
    filename: str
    object_name: str
    content_type: str
    created_at: datetime

    model_config = {
        "from_attributes": True
    }


class EvidenceSearchResponse(BaseModel):
    total_results: int
    evidence: list[EvidenceSearchItem]