from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.project import ProjectCreate, ProjectResponse
from app.services.project_service import (
    create_project,
    delete_project,
    get_project,
    get_projects,
    update_project,
)
from app.models.user import User

from app.services.auth_service import (get_current_user)

router = APIRouter(
    prefix="/projects",
    tags=["Projects"],
    #dependencies=[Depends(get_current_user)]    # this line ensures that all endpoints in this router require authentication
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


@router.put("/{project_id}", response_model=ProjectResponse)
def update_existing_project(
    project_id: UUID,
    project: ProjectCreate,
    db: Session = Depends(get_db),
):
    updated = update_project(db, project_id, project)

    if updated is None:
        raise HTTPException(
            status_code=404,
            detail="Project not found",
        )

    return updated


@router.delete("/{project_id}")
def delete_existing_project(
    project_id: UUID,
    db: Session = Depends(get_db),
):
    deleted = delete_project(db, project_id)

    if deleted is None:
        raise HTTPException(
            status_code=404,
            detail="Project not found",
        )

    return {"message": "Project deleted successfully"}