
import jwt
import pytest

from services.auth.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)


@pytest.fixture(autouse=True)
def jwt_settings(monkeypatch):
    monkeypatch.setenv(
        "WORKFLOW_JWT_SECRET",
        "unit-test-secret-not-for-production-123456789",
    )

    monkeypatch.setenv(
        "WORKFLOW_JWT_ISSUER",
        "manuagent",
    )

    monkeypatch.setenv(
        "WORKFLOW_JWT_AUDIENCE",
        "manuagent-api",
    )

    monkeypatch.setenv(
        "WORKFLOW_ACCESS_TOKEN_MINUTES",
        "30",
    )


def test_password_hash():
    password = "StrongPassword123!"

    hashed = hash_password(password)

    assert hashed != password
    assert verify_password(password, hashed)


def test_wrong_password():
    hashed = hash_password(
        "StrongPassword123!"
    )

    assert not verify_password(
        "WrongPassword123!",
        hashed,
    )


def test_create_and_decode_token():
    token = create_access_token(
        user_id=1001
    )

    payload = decode_access_token(token)

    assert payload["sub"] == "1001"
    assert payload["type"] == "access"


def test_invalid_token():
    with pytest.raises(jwt.PyJWTError):
        decode_access_token(
            "invalid.jwt.token"
        )


def test_tampered_token():
    token = create_access_token(1001)

    tampered = token[:-5] + "abcde"

    with pytest.raises(jwt.PyJWTError):
        decode_access_token(tampered)


def test_password_too_short():
    with pytest.raises(ValueError):
        hash_password("123456")
