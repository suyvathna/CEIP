from datetime import date, timedelta
from uuid import UUID

from psycopg2 import IntegrityError
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.project import Project
from app.schemas.project import (
    ProjectCreate,
    ProjectMilestonesUpdate,
    ProjectStatusUpdate,
)

# Manually-set states: once a PM marks a project Completed or puts it On
# Hold, that decision is a business fact, not something today's date
# should silently overwrite. Everything else ("Planning" / "In Progress")
# is derived fresh on every read from planned_start vs. today - see
# compute_effective_status.
MANUAL_STATUSES = {"Completed", "On Hold"}


def _compute_completion_date(planned_start: date, duration_days: int) -> date:
    return planned_start + timedelta(days=max(duration_days or 0, 0))


def compute_effective_status(project: Project) -> str:
    """
    "Planning" and "In Progress" are never trusted from the stored column -
    they're recomputed from today's date every time a project is read, so
    a project created months ago as "Planning" correctly flips to
    "In Progress" the moment its Commencement Date arrives, with nothing
    to remember to click. "Completed" and "On Hold" are manual overrides
    (see update_project_status) and always win: a project that has
    overrun its planned Completion Date must keep showing "In Progress"
    (with the overdue flag on ProjectResponse), not silently become
    "Completed" just because a date passed - that overrun is very often
    the whole reason a claim exists.
    """
    if project.status in MANUAL_STATUSES:
        return project.status

    if date.today() < project.planned_start:
        return "Planning"

    return "In Progress"


def _hydrate(project: Project) -> Project:
    project.status = compute_effective_status(project)
    return project


def create_project(db: Session, project: ProjectCreate) -> Project:
    payload = project.model_dump()
    payload["planned_finish"] = _compute_completion_date(
        payload["planned_start"], payload["duration_days"]
    )

    db_project = Project(**payload)

    db.add(db_project)
    db.commit()
    db.refresh(db_project)

    # Engine A materialises the new project's compliance register
    # immediately rather than waiting for tomorrow's sweep - a PM who
    # creates a project on Monday should see the Sub-Clause 8.3 initial
    # programme deadline on Monday, not Tuesday.
    _regenerate_compliance(db, db_project.id)

    return _hydrate(db_project)


def _regenerate_compliance(db: Session, project_id: UUID) -> None:
    """
    Rebuild a project's Engine A register after anything that could move
    its deadlines.

    Imported locally rather than at module level: compliance_service
    reaches into Engine B, and project_service is imported early by the
    projects router, so a module-level import would tie the whole
    project API to both engines loading cleanly. Failures are swallowed -
    a register that will rebuild itself on the next tick is not worth
    failing a project save over.
    """
    try:
        from app.services.compliance_service import regenerate_for_project

        regenerate_for_project(db, project_id)
    except Exception:  # noqa: BLE001 - see docstring
        import logging

        logging.getLogger(__name__).exception(
            "Compliance regeneration failed for project %s", project_id
        )
        db.rollback()


def get_projects(db: Session):
    statement = select(Project).order_by(Project.created_at.desc())
    projects = db.scalars(statement).all()
    return [_hydrate(p) for p in projects]


def get_project(db: Session, project_id: UUID):
    project = db.get(Project, project_id)
    return _hydrate(project) if project else None


def update_project(db: Session, project_id: UUID, project: ProjectCreate):
    db_project = db.get(Project, project_id)

    if not db_project:
        return None

    payload = project.model_dump()
    payload["planned_finish"] = _compute_completion_date(
        payload["planned_start"], payload["duration_days"]
    )

    for key, value in payload.items():
        setattr(db_project, key, value)

    db.commit()
    db.refresh(db_project)

    # The Commencement Date and Time for Completion may just have moved,
    # which re-dates every monthly obligation on the project.
    _regenerate_compliance(db, db_project.id)

    return _hydrate(db_project)


def update_milestones(
    db: Session, project_id: UUID, payload: ProjectMilestonesUpdate
) -> Project | None:
    """
    Set contract milestones and engine periods.

    exclude_unset is the whole point: this is a genuine PATCH, so sending
    only taking_over_date leaves everything else alone. Compare
    update_project above, which setattr's every field on ProjectCreate
    and therefore resets anything the caller didn't resend - the exact
    behaviour these fields are kept out of that schema to avoid.

    Regenerates the register synchronously afterwards, because a
    Taking-Over Certificate entered this morning changes the entire
    close-out schedule and retires every monthly obligation after it. A
    PM who enters that date wants to see the consequences immediately,
    not tomorrow.
    """
    db_project = db.get(Project, project_id)

    if not db_project:
        return None

    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(db_project, key, value)

    db.commit()
    db.refresh(db_project)

    _regenerate_compliance(db, db_project.id)
    db.refresh(db_project)

    return _hydrate(db_project)


def update_project_status(
    db: Session, project_id: UUID, payload: ProjectStatusUpdate
) -> Project | None:
    db_project = db.get(Project, project_id)

    if not db_project:
        return None

    if payload.status == "In Progress":
        # "Resume" - clears a manual On Hold/Completed override and goes
        # back to date-driven auto status.
        db_project.status = "Planning"
    elif payload.status in MANUAL_STATUSES:
        db_project.status = payload.status
    else:
        raise ValueError(
            f"'{payload.status}' is not a valid manual status. "
            "Use 'Completed', 'On Hold', or 'In Progress' (to resume)."
        )

    db.commit()
    db.refresh(db_project)

    return _hydrate(db_project)


def delete_project(db: Session, project_id: UUID):
    db_project = db.get(Project, project_id)

    if not db_project:
        return None

    try:
        db.delete(db_project)
        db.commit()
    except IntegrityError:
        db.rollback()
        raise ValueError(
            "This project still has events recorded under it. "
            "Delete those first, or keep the project as a record."
        )

    return db_project