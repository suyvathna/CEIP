from app.models.user import User
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.orm import Session


def create_user(db: Session, user: User):
    db.add(user)
    db.commit()
    db.refresh(user)

    return user


def get_users(db: Session):
    return db.scalars(select(User)).all()


def get_user(db: Session, user_id: UUID):
    # db.get is the canonical 2.0 way to fetch by Primary Key
    return db.get(User, user_id)


def get_user_by_email(
    db: Session,
    email: str,
):
    return db.scalars(
        select(User).where(User.email == email)
    ).first()