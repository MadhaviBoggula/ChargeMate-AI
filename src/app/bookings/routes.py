from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.driver.models import Driver

from app.auth.dependencies import (
    get_current_user,
    get_current_admin,
    get_current_driver
)

from app.bookings.schemas import (
    BookingCreate,
    BookingUpdate
)

from app.bookings.services import (
    create_booking_service,
    get_booking_service,
    get_all_bookings_service,
    get_driver_bookings_service,
    update_booking_service,
    cancel_booking_service,
    delete_booking_service
)


router = APIRouter(
    prefix="/bookings",
    tags=["Bookings"]
)


# ---------------------------------
# Create Booking API - Driver
# ---------------------------------

@router.post("/")
def create_booking_api(
    booking: BookingCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_driver)
):

    driver = (
        db.query(Driver)
        .filter(Driver.email == current_user.email)
        .first()
    )

    if not driver:
        raise HTTPException(
            status_code=404,
            detail="Driver profile not found"
        )

    result = create_booking_service(
    db,
    booking,
    driver.id
)

    if result == "station_not_found":
        raise HTTPException(
        status_code=404,
        detail="Station not found"
    )

    if result == "booking_exists":
        raise HTTPException(
        status_code=400,
        detail="Booking already exists for this time"
    )

    return result

# ---------------------------------
# Get All Bookings - Admin / Operator
# ---------------------------------

@router.get("/")
def get_all_bookings_api(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):

    if current_user.role not in ["admin", "operator"]:
        raise HTTPException(
            status_code=403,
            detail="Access denied"
        )

    return get_all_bookings_service(db)


# ---------------------------------
# Get My Bookings - Driver
# ---------------------------------

@router.get("/my")
def get_my_bookings_api(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_driver)
):

    driver = (
        db.query(Driver)
        .filter(Driver.email == current_user.email)
        .first()
    )

    if not driver:
        raise HTTPException(
            status_code=404,
            detail="Driver profile not found"
        )

    return get_driver_bookings_service(
        db,
        driver.id
    )


# ---------------------------------
# Get Booking By ID
# ---------------------------------

@router.get("/{booking_id}")
def get_booking_api(
    booking_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):

    booking = get_booking_service(
        db,
        booking_id
    )

    if not booking:
        raise HTTPException(
            status_code=404,
            detail="Booking not found"
        )

    if current_user.role == "driver":

        driver = (
            db.query(Driver)
            .filter(Driver.email == current_user.email)
            .first()
        )

        if not driver:
            raise HTTPException(
                status_code=404,
                detail="Driver profile not found"
            )

        if booking.driver_id != driver.id:
            raise HTTPException(
                status_code=403,
                detail="You cannot access another driver's booking"
            )

    if current_user.role not in [
        "admin",
        "operator",
        "driver"
    ]:
        raise HTTPException(
            status_code=403,
            detail="Access denied"
        )

    return booking


# ---------------------------------
# Update Booking - Admin / Operator
# ---------------------------------

@router.put("/{booking_id}")
def update_booking_api(
    booking_id: int,
    booking: BookingUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):

    if current_user.role not in [
        "admin",
        "operator"
    ]:
        raise HTTPException(
            status_code=403,
            detail="Only admin and operator can update bookings"
        )

    try:

        result = update_booking_service(
            db,
            booking_id,
            booking
        )

    except ValueError as error:

        raise HTTPException(
            status_code=400,
            detail=str(error)
        )

    if not result:

        raise HTTPException(
            status_code=404,
            detail="Booking not found"
        )

    return result


# ---------------------------------
# Cancel Booking - Driver
# ---------------------------------

@router.post("/{booking_id}/cancel")
def cancel_booking_api(
    booking_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_driver)
):

    booking = get_booking_service(
        db,
        booking_id
    )

    if not booking:
        raise HTTPException(
            status_code=404,
            detail="Booking not found"
        )


    driver = (
        db.query(Driver)
        .filter(Driver.email == current_user.email)
        .first()
    )

    if not driver:
        raise HTTPException(
            status_code=404,
            detail="Driver profile not found"
        )


    if booking.driver_id != driver.id:
        raise HTTPException(
            status_code=403,
            detail="You cannot cancel another driver's booking"
        )


    try:

        return cancel_booking_service(
            db,
            booking_id
        )

    except ValueError as error:

        raise HTTPException(
            status_code=400,
            detail=str(error)
        )


# ---------------------------------
# Delete Booking - Admin
# ---------------------------------

@router.delete("/{booking_id}")
def delete_booking_api(
    booking_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_admin)
):

    result = delete_booking_service(
        db,
        booking_id
    )

    if not result:
        raise HTTPException(
            status_code=404,
            detail="Booking not found"
        )

    return {
        "message": "Booking deleted successfully"
    }