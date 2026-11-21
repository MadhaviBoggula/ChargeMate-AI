from datetime import timedelta

from app.services.token import (
    create_access_token,
    decode_access_token,
)


def test_access_token_is_created():
    token = create_access_token("test-user-123", "owner")

    assert isinstance(token, str)
    assert len(token) > 0


def test_access_token_contains_user_id_and_role():
    token = create_access_token("test-user-123", "owner")

    payload = decode_access_token(token)

    assert payload is not None
    assert payload["sub"] == "test-user-123"
    assert payload["role"] == "owner"
    assert payload["jti"]


def test_invalid_token_is_rejected():
    payload = decode_access_token("invalid-token")

    assert payload is None


def test_expired_token_is_rejected():
    token = create_access_token(
        "test-user-123",
        "driver",
        expires_delta=timedelta(seconds=-1),
    )

    assert decode_access_token(token) is None
