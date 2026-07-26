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
    return db.query(Project).order_by(Project.created_at.desc()).all()


def get_project(db: Session, project_id):
    return db.query(Project).filter(Project.id == project_id).first()