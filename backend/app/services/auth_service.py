from datetime import datetime, timedelta, timezone
from uuid import UUID  # <--- Add this import

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.user import User
from app.repositories.user_repository import (
    get_user,
    get_user_by_email,
)
from app.services.security_service import verify_password

SECRET_KEY = "change-this-secret-key-for-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

# FIXED: Removed "/api" to match your actual route prefix
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/auth/login",
)


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


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM],
        )

        user_id_str: str = payload.get("sub")

        if user_id_str is None:
            raise credentials_exception

        # Safely convert string back to UUID for DB lookup
        user_id = UUID(user_id_str)

    except (JWTError, ValueError):
        raise credentials_exception

    user = get_user(
        db,
        user_id,
    )

    if user is None:
        raise credentials_exception

    return user

def require_admin(
    current_user: User = Depends(get_current_user),
):
    if current_user.role != "Admin":
        raise HTTPException(
            status_code=403,
            detail="Admin access required",
        )

    return current_user


def require_engineer(
    current_user: User = Depends(get_current_user),
):
    if current_user.role not in [
        "Admin",
        "Engineer",
    ]:
        raise HTTPException(
            status_code=403,
            detail="Engineer access required",
        )

    return current_user


def require_viewer(
    current_user: User = Depends(get_current_user),
):
    if current_user.role not in [
        "Admin",
        "Engineer",
        "Viewer",
    ]:
        raise HTTPException(
            status_code=403,
            detail="Permission denied",
        )

    return current_user