from typing import Annotated
from uuid import UUID

from email_validator import EmailNotValidError, validate_email
from pydantic import AfterValidator, BaseModel, ConfigDict, Field

from app.models.user import UserRole


def _validate_account_email(value: str) -> str:
    """Validate an account email, allowing reserved demo domains."""

    try:
        validate_email(
            value,
            check_deliverability=False,
            test_environment=True,
        )
    except EmailNotValidError as exc:
        raise ValueError(str(exc)) from exc

    return value


AccountEmail = Annotated[str, AfterValidator(_validate_account_email)]


class UserRegister(BaseModel):
    name: str = Field(min_length=4, max_length=255)
    email: AccountEmail = Field(min_length=4, max_length=255)
    password: str = Field(min_length=8, max_length=128)
    role: UserRole

class UserLogin(BaseModel):
    email: AccountEmail
    password: str = Field(min_length=1, max_length=128)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    email: AccountEmail
    role: UserRole
    is_active: bool