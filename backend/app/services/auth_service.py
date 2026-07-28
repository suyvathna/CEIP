from datetime import datetime, timedelta, timezone

from jose import jwt
from sqlalchemy.orm import Session

from app.repositories.user_repository import (
    get_user_by_email,
)
from app.services.security_service import (
    verify_password,
)

SECRET_KEY = "change-this-secret-key-for-production"

ALGORITHM = "HS256"

ACCESS_TOKEN_EXPIRE_MINUTES = 60


def authenticate_user(
    db: Session,
    email: str,
    password: str,
):
    user = get_user_by_email(
        db,
        email,
    )

    if user is None:
        return None

    if not verify_password(
        password,
        user.hashed_password,
    ):
        return None

    return user


def create_access_token(
    data: dict,
):
    payload = data.copy()

    expire = datetime.now(
        timezone.utc,
    ) + timedelta(
        minutes=ACCESS_TOKEN_EXPIRE_MINUTES,
    )

    payload.update(
        {
            "exp": expire,
        }
    )

    return jwt.encode(
        payload,
        SECRET_KEY,
        algorithm=ALGORITHM,
    )