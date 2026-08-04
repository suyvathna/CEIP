from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.project import (
    ProjectCreate,
    ProjectMilestonesUpdate,
    ProjectResponse,
    ProjectStatusUpdate,
)
from app.services.project_service import (
    create_project,
    delete_project,
    get_project,
    get_projects,
    update_milestones,
    update_project,
    update_project_status,
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


@router.patch("/{project_id}/milestones", response_model=ProjectResponse)
def update_project_milestones(
    project_id: UUID,
    payload: ProjectMilestonesUpdate,
    db: Session = Depends(get_db),
):
    """
    Set the contract milestones and engine periods Engine A and Engine B
    measure everything from: Letter of Acceptance, Taking-Over
    Certificate, Performance Certificate, the Defects Notification
    Period, and the Sub-Clause 3.7 / 3.5 / 13.3 windows.

    A true PATCH - only the fields sent are written. That is why these
    live here rather than on PUT /projects/{id}, whose body is
    ProjectCreate and which setattr's every field on it: a PM editing a
    project's city through the ordinary edit form would otherwise blank
    its Taking-Over date and silently retire half the compliance
    register.

    Saving here regenerates the register immediately, so entering a
    Taking-Over Certificate shows the 14.10 Statement at Completion
    deadline and closes out the monthly obligations on the spot.
    """
    updated = update_milestones(db, project_id, payload)

    if updated is None:
        raise HTTPException(
            status_code=404,
            detail="Project not found",
        )

    return updated


@router.patch("/{project_id}/status", response_model=ProjectResponse)
def update_project_status_endpoint(
    project_id: UUID,
    payload: ProjectStatusUpdate,
    db: Session = Depends(get_db),
):
    """
    Manually mark a project Completed or On Hold, or resume one ("In
    Progress") that was previously On Hold. "Planning"/"In Progress" are
    otherwise derived automatically from the Commencement Date - this
    endpoint exists for the two states that are a business decision, not
    something a calendar date should decide alone.
    """
    try:
        updated = update_project_status(db, project_id, payload)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

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
    try:
        deleted = delete_project(db, project_id)
    except ValueError as e:
        raise HTTPException(
            status_code=409,
            detail=str(e),
        )

    if deleted is None:
        raise HTTPException(
            status_code=404,
            detail="Project not found",
        )

    return {"message": "Project deleted successfully"}