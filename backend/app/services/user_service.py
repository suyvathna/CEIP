from uuid import UUID

from sqlalchemy.orm import Session

from app.models.user import User
from app.repositories.user_repository import (
    create_user,
    get_user,
    get_user_by_email,
    get_users,
)
from app.schemas.user import UserCreate
from app.services.security_service import hash_password


def create_user_service(
    db: Session,
    user: UserCreate,
):
    existing = get_user_by_email(
        db,
        user.email,
    )

    if existing:
        return None

    db_user = User(
        full_name=user.full_name,
        email=user.email,
        hashed_password=hash_password(
            user.password,
        ),
    )

    return create_user(
        db,
        db_user,
    )


def get_users_service(
    db: Session,
):
    return get_users(db)


def get_user_service(
    db: Session,
    user_id: UUID,
):
    return get_user(
        db,
        user_id,
    )