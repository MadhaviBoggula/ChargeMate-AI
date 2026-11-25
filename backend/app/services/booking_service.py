
from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.booking import Booking
from app.models.station import Station


ACTIVE_BOOKING_STATUSES = ("Pending", "Approved")
ALLOWED_DURATIONS = (30, 60, 120)


class BookingServiceError(Exception):
    """An expected booking operation error."""

    def __init__(self, detail: str, status_code: int = 400):
        self.detail = detail
        self.status_code = status_code
        super().__init__(detail)


def _validate_booking_time(booking_time: datetime) -> None:
    if booking_time.tzinfo is None or booking_time.utcoffset() is None:
        raise BookingServiceError(
            "booking_time must include a timezone.",
            422,
        )

    if booking_time <= datetime.now(timezone.utc):
        raise BookingServiceError(
            "Booking time must be in the future.",
            422,
        )


def _maximum_existing_overlap(
    bookings: list[Booking],
    requested_start: datetime,
    requested_end: datetime,
) -> int:
    """Calculate the maximum simultaneous existing reservations."""

    active_count = sum(
        1
        for booking in bookings
        if booking.booking_time <= requested_start
        and booking.end_time > requested_start
    )

    maximum_count = active_count
    events: list[tuple[datetime, int]] = []

    for booking in bookings:
        if requested_start < booking.booking_time < requested_end:
            events.append((booking.booking_time, 1))

        if requested_start < booking.end_time < requested_end:
            events.append((booking.end_time, -1))

    # Process reservation endings before beginnings at equal timestamps.
    events.sort(key=lambda event: (event[0], event[1]))

    for _, change in events:
        active_count += change
        maximum_count = max(maximum_count, active_count)

    return maximum_count


def create_booking(
    db: Session,
    user_id: UUID,
    station_id: UUID,
    booking_time: datetime,
    duration_minutes: int,
) -> Booking:
    """Create a booking without exceeding overlapping station capacity."""

    _validate_booking_time(booking_time)

    if duration_minutes not in ALLOWED_DURATIONS:
        raise BookingServiceError(
            "Duration must be 30, 60, or 120 minutes.",
            422,
        )

    requested_end = booking_time + timedelta(
        minutes=duration_minutes
    )

    try:
        # Serialize booking creation for this station.
        station = db.scalar(
            select(Station)
            .where(Station.id == station_id)
            .with_for_update()
        )

        if station is None or not station.is_active:
            raise BookingServiceError(
                "Active charging station not found.",
                404,
            )

        existing_bookings = list(
            db.scalars(
                select(Booking).where(
                    Booking.station_id == station_id,
                    Booking.status.in_(ACTIVE_BOOKING_STATUSES),
                    Booking.booking_time < requested_end,
                    Booking.end_time > booking_time,
                )
            ).all()
        )

        maximum_overlap = _maximum_existing_overlap(
            existing_bookings,
            booking_time,
            requested_end,
        )

        # The requested booking consumes one additional slot.
        if maximum_overlap + 1 > station.total_slots:
            raise BookingServiceError(
                "The station has no available capacity for "
                "the selected reservation time and duration.",
                409,
            )

        booking = Booking(
            user_id=user_id,
            station_id=station_id,
            booking_time=booking_time,
            duration_minutes=duration_minutes,
            end_time=requested_end,
            status="Pending",
        )

        db.add(booking)
        db.commit()
        db.refresh(booking)

        return booking

    except Exception:
        db.rollback()
        raise


def cancel_booking(
    db: Session,
    booking_id: UUID,
    user_id: UUID,
) -> Booking:
    """Cancel a driver's booking and release its reserved capacity."""

    try:
        booking = db.get(Booking, booking_id)

        if booking is None or booking.user_id != user_id:
            raise BookingServiceError(
                "Booking not found.",
                404,
            )

        # Lock the station so cancellation and new reservations
        # are serialized against each other.
        station = db.scalar(
            select(Station)
            .where(Station.id == booking.station_id)
            .with_for_update()
        )

        if station is None:
            raise BookingServiceError(
                "Charging station not found.",
                404,
            )

        # Reload after acquiring the station lock.
        booking = db.scalar(
            select(Booking)
            .where(Booking.id == booking_id)
            .with_for_update()
        )

        if booking is None or booking.user_id != user_id:
            raise BookingServiceError(
                "Booking not found.",
                404,
            )

        if booking.status in ("Completed", "Rejected", "Cancelled"):
            raise BookingServiceError(
                "This booking cannot be cancelled.",
                400,
            )

        booking.status = "Cancelled"

        db.commit()
        db.refresh(booking)

        return booking

    except Exception:
        db.rollback()
        raise
