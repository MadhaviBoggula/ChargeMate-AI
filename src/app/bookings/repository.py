
from sqlalchemy.orm import Session

from app.bookings.models import Booking
from app.bookings.schemas import BookingCreate, BookingUpdate
from app.stations.models import Station

# ---------------------------------
# Create Booking
# ---------------------------------
# ---------------------------------
# Create Booking
# ---------------------------------

def create_booking(
    db,
    booking,
    driver_id
):

    # Check station exists
    station = (
        db.query(Station)
        .filter(
            Station.id == booking.station_id
        )
        .first()
    )

    if not station:
        return "station_not_found"


    # Check duplicate booking
    existing_booking = (
        db.query(Booking)
        .filter(
            Booking.driver_id == driver_id,
            Booking.station_id == booking.station_id,
            Booking.booking_time == booking.booking_time,
            Booking.status != "Cancelled"
        )
        .first()
    )

    if existing_booking:
        return "booking_exists"


    new_booking = Booking(
        driver_id=driver_id,
        station_id=booking.station_id,
        booking_time=booking.booking_time,
        status="Pending"
    )

    db.add(new_booking)
    db.commit()
    db.refresh(new_booking)

    return new_booking

# ---------------------------------
# Get Booking By ID
# ---------------------------------

def get_booking(db: Session, booking_id: int):

    return db.query(Booking).filter(
        Booking.id == booking_id
    ).first()


# ---------------------------------
# Get All Bookings
# ---------------------------------

def get_all_bookings(db: Session):

    return db.query(Booking).all()


# ---------------------------------
# Get Driver Bookings
# ---------------------------------

def get_driver_bookings(db: Session, driver_id: int):

    return db.query(Booking).filter(
        Booking.driver_id == driver_id
    ).all()


# ---------------------------------
# Update Booking
# ---------------------------------

def update_booking(
    db: Session,
    booking_id: int,
    booking: BookingUpdate
):

    existing_booking = get_booking(db, booking_id)

    if not existing_booking:
        return None

    existing_booking.booking_time = booking.booking_time
    existing_booking.status = booking.status

    db.commit()
    db.refresh(existing_booking)

    return existing_booking


# ---------------------------------
# Delete Booking
# ---------------------------------

def delete_booking(db: Session, booking_id: int):

    booking = get_booking(db, booking_id)

    if not booking:
        return None

    db.delete(booking)
    db.commit()

    return booking
