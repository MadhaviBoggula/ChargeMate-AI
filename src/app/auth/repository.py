from sqlalchemy.orm import Session

from app.auth.models import User
from app.auth.schemas import UserCreate
from app.driver.models import Driver


# ---------------------------------
# Create User
# ---------------------------------
def create_user(
    db: Session,
    user: UserCreate,
    hashed_password: str
):

    new_user = User(
        full_name=user.full_name,
        email=user.email,
        password=hashed_password,
        role=user.role.lower()
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # Create Driver record if role is driver
    if user.role.lower() == "driver":

        driver = Driver(
            full_name=user.full_name,
            email=user.email,
            phone=user.phone
        )

        db.add(driver)
        db.commit()

    return new_user


# ---------------------------------
# Get User By Email
# ---------------------------------
def get_user_by_email(
    db: Session,
    email: str
):

    return (
        db.query(User)
        .filter(User.email == email)
        .first()
    )


# ---------------------------------
# Get User By ID
# ---------------------------------
def get_user_by_id(
    db: Session,
    user_id: int
):

    return (
        db.query(User)
        .filter(User.id == user_id)
        .first()
    )