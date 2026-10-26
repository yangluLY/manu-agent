
from dataclasses import dataclass

import jwt
from fastapi import (
    Depends,
    HTTPException,
    status,
)
from fastapi.security import (
    HTTPAuthorizationCredentials,
    HTTPBearer,
)
from sqlalchemy.orm import Session

from services.auth.security import (
    decode_access_token,
)
from services.database.models.user import User
from services.database.session import SessionLocal

bearer = HTTPBearer(auto_error=False)


@dataclass(frozen=True)
class CurrentUser:
    user_id: str
    roles: frozenset[str]


def get_db():
    with SessionLocal() as db:
        yield db


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(
        bearer
    ),
    db: Session = Depends(get_db),
) -> CurrentUser:
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="未登录",
            headers={
                "WWW-Authenticate": "Bearer",
            },
        )

    try:
        payload = decode_access_token(
            credentials.credentials
        )

        user_id = int(payload["sub"])

        if user_id <= 0:
            raise ValueError("用户 ID 无效")

    except (
        jwt.PyJWTError,
        ValueError,
        TypeError,
    ):
        raise HTTPException(
            status_code=401,
            detail="登录凭证无效或已过期",
            headers={
                "WWW-Authenticate": "Bearer",
            },
        ) from None

    user = db.get(User, user_id)

    if user is None or not user.is_active:
        raise HTTPException(
            status_code=401,
            detail="用户不存在或已被禁用",
        )

    return CurrentUser(
        user_id=str(user.id),
        roles=frozenset({user.role}),
    )
