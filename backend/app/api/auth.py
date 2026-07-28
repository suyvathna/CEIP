from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.auth import TokenResponse
from app.services.auth_service import (
    authenticate_user,
    create_access_token,
)

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


@router.post(
    "/login",
    response_model=TokenResponse,
)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),  # Accepts form data from Swagger UI
    db: Session = Depends(get_db),
):
    # form_data.username holds whatever was typed into the "username" box in Swagger
    user = authenticate_user(
        db,
        form_data.username,
        form_data.password,
    )

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = create_access_token(
        {
            "sub": str(user.id),
            "email": user.email,
            "role": user.role,
        }
    )

    return {
        "access_token": token,
        "token_type": "bearer",
    }


# from fastapi import APIRouter, Depends, HTTPException
# from sqlalchemy.orm import Session

# from app.db.session import get_db

# from app.schemas.auth import (
#     LoginRequest,
#     TokenResponse,
# )

# from app.services.auth_service import (
#     authenticate_user,
#     create_access_token,
# )

# router = APIRouter(
#     prefix="/auth",
#     tags=["Authentication"],
# )


# @router.post(
#     "/login",
#     response_model=TokenResponse,
# )
# def login(
#     request: LoginRequest,
#     db: Session = Depends(get_db),
# ):
#     user = authenticate_user(
#         db,
#         request.email,
#         request.password,
#     )

#     if user is None:
#         raise HTTPException(
#             status_code=401,
#             detail="Invalid email or password",
#         )

#     token = create_access_token(
#         {
#             "sub": str(user.id),
#             "email": user.email,
#             "role": user.role,
#         }
#     )

#     return {
#         "access_token": token,
#         "token_type": "bearer",
#     }