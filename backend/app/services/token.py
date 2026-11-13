from datetime import datetime, timedelta, timezone

import jwt
from jwt import InvalidTokenError

from app.core.config import settings


def get_jwt_secret() -> str:
    """Get the JWT secret from application settings."""
    if not settings.jwt_secret_key:
        raise RuntimeError("JWT_SECRET_KEY is not configured.")

    return settings.jwt_secret_key.get_secret_value()


def create_access_token(
    subject: str,
    expires_delta: timedelta | None = None,
) -> str:
    """Create a signed JWT access token."""

    now = datetime.now(timezone.utc)

    if expires_delta is None:
        expires_delta = timedelta(
            minutes=settings.access_token_expire_minutes
        )

    payload = {
        "sub": subject,
        "iat": now,
        "exp": now + expires_delta,
    }

    return jwt.encode(
        payload,
        get_jwt_secret(),
        algorithm=settings.jwt_algorithm,
    )


def decode_access_token(token: str) -> dict | None:
    """Decode and validate a JWT access token."""

    try:
        payload = jwt.decode(
            token,
            get_jwt_secret(),
            algorithms=[settings.jwt_algorithm],
        )

        if not payload.get("sub"):
            return None

        return payload

    except InvalidTokenError:
        return None