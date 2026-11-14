from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.auth.repository import get_user_by_email
from app.auth.services import SECRET_KEY, ALGORITHM


oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/auth/login"
)


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):

    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials"
    )

    try:

        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )

        email = payload.get("sub")

        if email is None:
            raise credentials_exception

    except JWTError:
        raise credentials_exception

    user = get_user_by_email(
        db,
        email
    )

    if user is None:
        raise credentials_exception

    return user


# ---------------------------------
# Admin Only
# ---------------------------------

def get_current_admin(
    current_user=Depends(get_current_user)
):
    if current_user.role != "admin":
        raise HTTPException(
            status_code=403,
            detail="Access denied. Admin only."
        )

    return current_user


# ---------------------------------
# Driver Only
# ---------------------------------

def get_current_driver(
    current_user=Depends(get_current_user)
):
    if current_user.role != "driver":
        raise HTTPException(
            status_code=403,
            detail="Access denied. Driver only."
        )

    return current_user


# ---------------------------------
# Operator Only
# ---------------------------------

def get_current_operator(
    current_user=Depends(get_current_user)
):
    if current_user.role != "operator":
        raise HTTPException(
            status_code=403,
            detail="Access denied. Operator only."
        )

    return current_user