from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.project import ProjectCreate, ProjectResponse
from app.services.project_service import (
    create_project,
    get_project,
    get_projects,
)

router = APIRouter(
    prefix="/projects",
    tags=["Projects"],
)


@router.post("/", response_model=ProjectResponse)
def create_new_project(
    project: ProjectCreate,
    db: Session = Depends(get_db),
):
    return create_project(db, project)


@router.get("/", response_model=list[ProjectResponse])
def read_projects(
    db: Session = Depends(get_db),
):
    return get_projects(db)


@router.get("/{project_id}", response_model=ProjectResponse)
def read_project(
    project_id: UUID,
    db: Session = Depends(get_db),
):
    project = get_project(db, project_id)

    if project is None:
        raise HTTPException(
            status_code=404,
            detail="Project not found",
        )

    return project