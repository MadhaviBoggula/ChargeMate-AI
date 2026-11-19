from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.user import User, UserRole
from app.services.token import decode_access_token


bearer_scheme = HTTPBearer(
    scheme_name="Bearer Token",
    description="Paste the JWT access token returned by /api/v1/auth/login.",
    auto_error=False,
)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    """Identify the user associated with a valid access token."""

    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired authentication token.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if credentials is None:
        raise unauthorized

    payload = decode_access_token(credentials.credentials)

    if not payload:
        raise unauthorized

    try:
        user_id = UUID(payload["sub"])
    except (ValueError, TypeError, KeyError):
        raise unauthorized

    user = db.get(User, user_id)

    if user is None or not user.is_active:
        raise unauthorized

    return user


def get_owner_id(
    current_user: User = Depends(get_current_user),
):
    role = current_user.role

    role_value = (
        role.value if hasattr(role, "value") else role
    )

    if not isinstance(role_value, str) or role_value.lower() != "owner":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only owners can access this resource",
        )

    return current_user.id
