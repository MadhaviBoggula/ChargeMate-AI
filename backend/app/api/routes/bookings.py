
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.database.session import get_db
from app.models.booking import Booking
from app.models.user import User, UserRole
from app.schemas.booking import BookingCreate, BookingResponse
from app.services.booking_service import (
    BookingServiceError,
    cancel_booking as cancel_booking_service,
    create_booking as create_booking_service,
)

router = APIRouter(tags=["Bookings"])


def require_driver(user: User) -> None:
    if user.role != UserRole.DRIVER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only drivers can create or cancel bookings.",
        )


def raise_booking_error(error: BookingServiceError) -> None:
    raise HTTPException(
        status_code=error.status_code,
        detail=error.detail,
    )


@router.post(
    "/",
    response_model=BookingResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_booking(
    payload: BookingCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    require_driver(user)

    try:
        return create_booking_service(
            db=db,
            user_id=user.id,
            station_id=payload.station_id,
            booking_time=payload.booking_time,
            duration_minutes=payload.duration_minutes,
        )
    except BookingServiceError as error:
        raise_booking_error(error)


@router.get("/my", response_model=list[BookingResponse])
def list_my_bookings(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    require_driver(user)

    return (
        db.query(Booking)
        .filter(Booking.user_id == user.id)
        .order_by(Booking.booking_time.desc())
        .all()
    )


@router.get("/{booking_id}", response_model=BookingResponse)
def get_booking(
    booking_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    booking = db.get(Booking, booking_id)

    if booking is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found.",
        )

    if user.role == UserRole.DRIVER and booking.user_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You cannot access another driver's booking.",
        )

    if user.role not in (UserRole.DRIVER, UserRole.OWNER):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied.",
        )

    return booking


@router.post(
    "/{booking_id}/cancel",
    response_model=BookingResponse,
)
def cancel_booking(
    booking_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    require_driver(user)

    try:
        return cancel_booking_service(
            db=db,
            booking_id=booking_id,
            user_id=user.id,
        )
    except BookingServiceError as error:
        raise_booking_error(error)
