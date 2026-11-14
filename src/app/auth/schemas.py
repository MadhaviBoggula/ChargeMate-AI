from pydantic import BaseModel, EmailStr
from datetime import datetime


# -----------------------------
# Register User
# -----------------------------
class UserCreate(BaseModel):
    full_name: str
    email: EmailStr
    password: str
    role: str


# -----------------------------
# Login User
# -----------------------------
class UserLogin(BaseModel):
    email: EmailStr
    password: str


# -----------------------------
# User Response
# -----------------------------
class UserResponse(BaseModel):
    id: int
    full_name: str
    email: EmailStr
    role: str
    created_at: datetime

    model_config = {
        "from_attributes": True
    }


# -----------------------------
# Token Response
# -----------------------------
class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"