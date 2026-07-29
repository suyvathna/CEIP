from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class IntelligenceSearchResult(BaseModel):
    id: UUID
    item_type: str
    title: str
    created_at: datetime

    model_config = {
        "from_attributes": True
    }