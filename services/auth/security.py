
import os
from datetime import datetime, timedelta, timezone

import jwt
from dotenv import load_dotenv
from pwdlib import PasswordHash

load_dotenv()

password_hasher = PasswordHash.recommended()


def hash_password(password: str) -> str:
    if len(password) < 12:
        raise ValueError("密码长度至少为 12 位")

    return password_hasher.hash(password)


def verify_password(
    plain_password: str,
    password_hash: str,
) -> bool:
    return password_hasher.verify(
        plain_password,
        password_hash,
    )


def get_jwt_settings():
    secret = os.getenv("WORKFLOW_JWT_SECRET")
    issuer = os.getenv("WORKFLOW_JWT_ISSUER")
    audience = os.getenv("WORKFLOW_JWT_AUDIENCE")

    if not secret or len(secret) < 32:
        raise RuntimeError(
            "WORKFLOW_JWT_SECRET 必须至少包含 32 个字符"
        )

    if not issuer or not audience:
        raise RuntimeError(
            "JWT issuer/audience 未配置"
        )

    minutes = int(
        os.getenv(
            "WORKFLOW_ACCESS_TOKEN_MINUTES",
            "30",
        )
    )

    if not 1 <= minutes <= 1440:
        raise ValueError(
            "Token 有效期必须在 1～1440 分钟之间"
        )

    return secret, issuer, audience, minutes


def create_access_token(user_id: int) -> str:
    secret, issuer, audience, minutes = (
        get_jwt_settings()
    )

    now = datetime.now(timezone.utc)  # noqa: UP017

    payload = {
        "sub": str(user_id),
        "iss": issuer,
        "aud": audience,
        "iat": now,
        "nbf": now,
        "exp": now + timedelta(minutes=minutes),
        "type": "access",
    }

    return jwt.encode(
        payload,
        secret,
        algorithm="HS256",
    )


def decode_access_token(token: str) -> dict:
    secret, issuer, audience, _ = (
        get_jwt_settings()
    )

    payload = jwt.decode(
        token,
        secret,
        algorithms=["HS256"],
        issuer=issuer,
        audience=audience,
        options={
            "require": [
                "sub",
                "iss",
                "aud",
                "iat",
                "nbf",
                "exp",
                "type",
            ],
        },
    )

    if payload.get("type") != "access":
        raise jwt.InvalidTokenError(
            "Token 类型不正确"
        )

    return payload
