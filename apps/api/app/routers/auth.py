
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
)
from sqlalchemy import select
from sqlalchemy.orm import Session

from apps.api.app.dependencies.auth import (
    CurrentUser,
    get_current_user,
    get_db,
)
from apps.api.app.schemas.auth import (
    LoginRequest,
    TokenResponse,
    UserResponse,
)
from services.auth.security import (
    create_access_token,
    verify_password,
)
from services.database.models.user import User

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


@router.post(
    "/login",
    response_model=TokenResponse,
)
def login(
    request: LoginRequest,
    db: Session = Depends(get_db),
):
    username = request.username.strip()

    user = db.scalar(
        select(User).where(
            User.username == username
        )
    )

    if (
        user is None
        or not user.is_active
        or not verify_password(
            request.password,
            user.password_hash,
        )
    ):
        raise HTTPException(
            status_code=401,
            detail="用户名或密码错误",
        )

    return TokenResponse(
        access_token=create_access_token(
            user.id
        ),
    )


@router.get(
    "/me",
    response_model=UserResponse,
)
def get_me(
    current_user: CurrentUser = Depends(
        get_current_user
    ),
    db: Session = Depends(get_db),
):
    user = db.get(
        User,
        int(current_user.user_id),
    )

    if user is None or not user.is_active:
        raise HTTPException(
            status_code=401,
            detail="用户不存在或已被禁用",
        )

    return UserResponse(
        id=user.id,
        username=user.username,
        role=user.role,
        is_active=user.is_active,
    )
