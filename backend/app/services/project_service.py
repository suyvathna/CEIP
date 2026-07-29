from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.project import Project
from app.schemas.project import ProjectCreate


def create_project(db: Session, project: ProjectCreate) -> Project:
    db_project = Project(**project.model_dump())

    db.add(db_project)
    db.commit()
    db.refresh(db_project)

    return db_project


def get_projects(db: Session):
    statement = select(Project).order_by(Project.created_at.desc())
    return db.scalars(statement).all()


def get_project(db: Session, project_id: UUID):
    return db.get(Project, project_id)


def update_project(db: Session, project_id: UUID, project: ProjectCreate):
    db_project = db.get(Project, project_id)

    if not db_project:
        return None

    for key, value in project.model_dump().items():
        setattr(db_project, key, value)

    db.commit()
    db.refresh(db_project)

    return db_project


def delete_project(db: Session, project_id: UUID):
    db_project = db.get(Project, project_id)

    if not db_project:
        return None

    db.delete(db_project)
    db.commit()

    return db_project