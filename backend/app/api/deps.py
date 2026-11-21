from collections.abc import Callable
from uuid import UUID

from fastapi import Depends, HTTPException, Request, status
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


def _role_value(user: User) -> str:
    return user.role.value if hasattr(user.role, "value") else str(user.role)


def get_current_user(
    request: Request,
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

    token_role = payload.get("role")

    if not isinstance(token_role, str) or token_role != _role_value(user):
        raise unauthorized

    # Read by the request logging middleware after the response is built.
    request.state.user_id = str(user.id)
    request.state.role = _role_value(user)

    return user


def require_role(*allowed_roles: UserRole) -> Callable:
    """Build a dependency that requires one of the supplied roles."""

    allowed = {
        role.value if hasattr(role, "value") else str(role)
        for role in allowed_roles
    }

    def dependency(
        current_user: User = Depends(get_current_user),
    ) -> User:
        if _role_value(current_user) not in allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to access this resource.",
            )

        return current_user

    return dependency


get_current_owner = require_role(UserRole.OWNER)
get_current_driver = require_role(UserRole.DRIVER)


def get_owner_id(
    current_user: User = Depends(get_current_owner),
) -> UUID:
    """Return the authenticated owner's ID for ownership-scoped queries."""

    return current_user.id


def get_driver_id(
    current_user: User = Depends(get_current_driver),
) -> UUID:
    """Return the authenticated driver's ID for ownership-scoped queries."""

    return current_user.id
