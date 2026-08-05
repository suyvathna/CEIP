from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.intelligence import IntelligenceSearchResult
from app.services.intelligence_service import (
    intelligence_search,
)

router = APIRouter(
    prefix="/intelligence",
    tags=["Evidence Intelligence"],
)


@router.get(
    "/search",
    response_model=list[IntelligenceSearchResult],
)
def search(
    q: str,
    project_id: UUID | None = None,
    db: Session = Depends(get_db),
):
    return intelligence_search(
        db,
        q,
        project_id,
    )