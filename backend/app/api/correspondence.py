from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.correspondence import CorrespondenceCreate, CorrespondenceResponse
from app.services.correspondence_service import (
    create_correspondence_service,
    delete_correspondence_service,
    get_correspondence_service,
    get_project_correspondence_service,
    update_correspondence_service,
)

router = APIRouter(
    prefix="/correspondence",
    tags=["Correspondence"],
)


@router.post("/", response_model=CorrespondenceResponse)
def create_correspondence(
    correspondence: CorrespondenceCreate,
    db: Session = Depends(get_db),
):
    return create_correspondence_service(db, correspondence)


@router.get(
    "/project/{project_id}",
    response_model=list[CorrespondenceResponse],
)
def read_project_correspondence(
    project_id: UUID,
    db: Session = Depends(get_db),
):
    return get_project_correspondence_service(db, project_id)


@router.get("/{correspondence_id}", response_model=CorrespondenceResponse)
def read_correspondence(
    correspondence_id: UUID,
    db: Session = Depends(get_db),
):
    correspondence = get_correspondence_service(db, correspondence_id)

    if correspondence is None:
        raise HTTPException(status_code=404, detail="Correspondence not found")

    return correspondence


@router.put("/{correspondence_id}", response_model=CorrespondenceResponse)
def update_correspondence(
    correspondence_id: UUID,
    correspondence: CorrespondenceCreate,
    db: Session = Depends(get_db),
):
    updated = update_correspondence_service(db, correspondence_id, correspondence)

    if updated is None:
        raise HTTPException(status_code=404, detail="Correspondence not found")

    return updated


@router.delete("/{correspondence_id}")
def delete_correspondence(
    correspondence_id: UUID,
    db: Session = Depends(get_db),
):
    try:
        deleted = delete_correspondence_service(db, correspondence_id)
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))

    if deleted is None:
        raise HTTPException(status_code=404, detail="Correspondence not found")

    return {"message": "Correspondence deleted successfully"}
