from fastapi import APIRouter, Depends, HTTPException

from sqlalchemy.orm import Session

from app.database.database import get_db

from app.auth.schemas import (
    UserCreate,
    UserLogin
)

from app.auth.repository import (
    create_user,
    get_user_by_email
)

from app.auth.services import (
    hash_password,
    authenticate_user,
    create_access_token
)

 
router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)


# ---------------------------------
# Register User
# ---------------------------------

@router.post("/register")
def register_user(
    user: UserCreate,
    db: Session = Depends(get_db)
):

    existing_user = get_user_by_email(
        db,
        user.email
    )

    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="Email already registered"
        )

    hashed_password = hash_password(
        user.password
    )

    new_user = create_user(
        db,
        user,
        hashed_password
    )

    return {
        "message": "User registered successfully",
        "user": new_user
    }


# ---------------------------------
# Login User
# ---------------------------------

@router.post("/login")
def login_user(
    user: UserLogin,
    db: Session = Depends(get_db)
):

    authenticated_user = authenticate_user(
        db,
        user.email,
        user.password
    )

    if not authenticated_user:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )

    access_token = create_access_token(
        {
            "sub": authenticated_user.email,
            "role": authenticated_user.role,
            "id": authenticated_user.id
        }
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": authenticated_user.id,
            "full_name": authenticated_user.full_name,
            "email": authenticated_user.email,
            "role": authenticated_user.role
        }
    }
