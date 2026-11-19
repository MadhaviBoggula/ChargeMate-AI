
from sqlalchemy.orm import Session

from app.bookings.schemas import BookingCreate, BookingUpdate
from app.bookings.repository import (
    create_booking,
    get_booking,
    get_all_bookings,
    get_driver_bookings,
    update_booking,
    delete_booking
)


# ---------------------------------
# Allowed Booking Status
# ---------------------------------

ALLOWED_STATUSES = [
    "Pending",
    "Approved",
    "Rejected",
    "Completed",
    "Cancelled"
]


# ---------------------------------
# Create Booking Service
# ---------------------------------
def create_booking_service(
    db,
    booking,
    driver_id
):

    return create_booking(
        db,
        booking,
        driver_id
    )


# ---------------------------------
# Get Booking Service
# ---------------------------------

def get_booking_service(
    db: Session,
    booking_id: int
):

    return get_booking(db, booking_id)


# ---------------------------------
# Get All Bookings Service
# ---------------------------------

def get_all_bookings_service(db: Session):

    return get_all_bookings(db)


# ---------------------------------
# Get Driver Bookings Service
# ---------------------------------

def get_driver_bookings_service(
    db: Session,
    driver_id: int
):

    return get_driver_bookings(db, driver_id)


# ---------------------------------
# Update Booking Service
# ---------------------------------

def update_booking_service(
    db: Session,
    booking_id: int,
    booking: BookingUpdate
):

    if booking.status not in ALLOWED_STATUSES:
        raise ValueError("Invalid booking status")

    existing_booking = get_booking(db, booking_id)

    if not existing_booking:
        return None

    if existing_booking.status in ["Cancelled", "Rejected", "Completed"]:
        raise ValueError("This booking cannot be updated")

    return update_booking(
        db,
        booking_id,
        booking
    )


# ---------------------------------
# Cancel Booking Service
# ---------------------------------

def cancel_booking_service(
    db: Session,
    booking_id: int
):

    existing_booking = get_booking(db, booking_id)

    if not existing_booking:
        return None

    if existing_booking.status in ["Completed", "Rejected"]:
        raise ValueError("This booking cannot be cancelled")

    existing_booking.status = "Cancelled"

    db.commit()
    db.refresh(existing_booking)

    return existing_booking


# ---------------------------------
# Delete Booking Service
# ---------------------------------

def delete_booking_service(
    db: Session,
    booking_id: int
):

    return delete_booking(db, booking_id)
