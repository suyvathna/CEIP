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