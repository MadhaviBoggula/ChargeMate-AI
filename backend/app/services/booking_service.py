from __future__ import annotations

import uuid
from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.core.errors import ConflictError, NotFoundError, ValidationError
from app.models.booking import ChargingBooking
from app.models.charger import Charger
from app.models.pending_confirmation import PendingConfirmation
from app.models.station import ChargingStation
from app.models.vehicle import Vehicle
from app.schemas.booking import (
    BOOKING_SLOT_MINUTES,
    MAX_BOOKING_MINUTES,
    AvailableSlot,
    BookingProposalCreate,
)
from app.services.driver_service import (
    resolve_matching_connector,
    resolve_vehicle,
)
from app.services.station_service import get_active_station
from app.services.time_utils import (
    align_up,
    as_utc,
    ensure_utc,
    get_zone,
    is_aligned,
    local_iso,
)

CANCELLATION_CUTOFF = timedelta(minutes=30)
PROPOSAL_TTL = timedelta(minutes=15)
MAX_SLOT_WINDOW = timedelta(days=7)


# ---------------------------------------------------------------------------
# Slot search
# ---------------------------------------------------------------------------


def _window(
    station: ChargingStation,
    start_at: datetime | None,
    end_at: datetime | None,
    day: date | None,
) -> tuple[datetime, datetime]:
    tz_name = station.timezone
    now = datetime.now(timezone.utc)

    if day is not None and start_at is None:
        zone = get_zone(tz_name)
        window_start = datetime.combine(day, time.min, tzinfo=zone).astimezone(
            timezone.utc
        )
        window_end = window_start + timedelta(days=1)
    else:
        window_start = ensure_utc(start_at, tz_name) if start_at else now
        window_end = (
            ensure_utc(end_at, tz_name)
            if end_at
            else window_start + timedelta(days=1)
        )

    if window_end <= window_start:
        raise ValidationError("The slot window end must be after its start.")

    if window_end - window_start > MAX_SLOT_WINDOW:
        raise ValidationError("The slot window cannot exceed 7 days.")

    if window_start < now:
        window_start = now

    return window_start, window_end


def search_available_slots(
    db: Session,
    station_id: UUID,
    *,
    start_at: datetime | None = None,
    end_at: datetime | None = None,
    day: date | None = None,
    duration_minutes: int = BOOKING_SLOT_MINUTES,
    connector_type: str | None = None,
    charging_type: str | None = None,
    max_price_per_kwh: Decimal | None = None,
    limit: int = 50,
) -> list[AvailableSlot]:
    """Return bookable slots derived from charger data and bookings."""

    if (
        duration_minutes < BOOKING_SLOT_MINUTES
        or duration_minutes > MAX_BOOKING_MINUTES
        or duration_minutes % BOOKING_SLOT_MINUTES != 0
    ):
        raise ValidationError(
            "Duration must be a multiple of 30 minutes between 30 and 240."
        )

    station = get_active_station(db, station_id)
    tz_name = station.timezone
    window_start, window_end = _window(station, start_at, end_at, day)

    candidate_chargers: list[tuple[Charger, object]] = []

    for charger in station.chargers:
        if charger.status != "active":
            continue

        if charging_type and charger.charging_type != charging_type.upper():
            continue

        if (
            max_price_per_kwh is not None
            and charger.price_per_kwh > max_price_per_kwh
        ):
            continue

        connector = resolve_matching_connector(charger, connector_type)

        if connector is None:
            continue

        candidate_chargers.append((charger, connector))

    if not candidate_chargers:
        return []

    charger_ids = [charger.id for charger, _ in candidate_chargers]

    booked_intervals: dict[UUID, list[tuple[datetime, datetime]]] = {}

    rows = db.execute(
        select(
            ChargingBooking.charger_id,
            ChargingBooking.start_at,
            ChargingBooking.end_at,
        ).where(
            ChargingBooking.charger_id.in_(charger_ids),
            ChargingBooking.status == "CONFIRMED",
            ChargingBooking.start_at < window_end,
            ChargingBooking.end_at > window_start,
        )
    ).all()

    for charger_id, booking_start, booking_end in rows:
        booked_intervals.setdefault(charger_id, []).append(
            (as_utc(booking_start), as_utc(booking_end))
        )

    duration = timedelta(minutes=duration_minutes)
    slots: list[AvailableSlot] = []

    for charger, connector in candidate_chargers:
        cursor = align_up(window_start, BOOKING_SLOT_MINUTES, tz_name)
        intervals = booked_intervals.get(charger.id, [])

        while cursor + duration <= window_end:
            slot_end = cursor + duration
            overlaps = any(
                cursor < existing_end and slot_end > existing_start
                for existing_start, existing_end in intervals
            )

            if not overlaps:
                estimated_price = (
                    charger.power_kw
                    * Decimal(duration_minutes)
                    / Decimal(60)
                    * charger.price_per_kwh
                ).quantize(Decimal("0.01"))

                slots.append(
                    AvailableSlot(
                        station_id=station.id,
                        charger_id=charger.id,
                        charger_code=charger.charger_code,
                        charging_type=charger.charging_type,
                        connector_type=connector.connector_type,
                        power_kw=charger.power_kw,
                        price_per_kwh=charger.price_per_kwh,
                        estimated_price=estimated_price,
                        start_at=cursor,
                        end_at=slot_end,
                        duration_minutes=duration_minutes,
                        timezone=tz_name,
                        local_start=local_iso(cursor, tz_name),
                        local_end=local_iso(slot_end, tz_name),
                    )
                )

            cursor += timedelta(minutes=BOOKING_SLOT_MINUTES)

    slots.sort(key=lambda slot: (slot.start_at, slot.charger_code))

    return slots[: max(1, min(limit, 200))]


# ---------------------------------------------------------------------------
# Proposals
# ---------------------------------------------------------------------------


def _load_station_charger(
    db: Session,
    station_id: UUID,
    charger_id: UUID,
) -> tuple[ChargingStation, Charger]:
    station = get_active_station(db, station_id)
    charger = next(
        (item for item in station.chargers if item.id == charger_id),
        None,
    )

    if charger is None:
        raise NotFoundError("Charger not found at this station.")

    return station, charger


def _overlapping_booking_count(
    db: Session,
    charger_id: UUID,
    start_at: datetime,
    end_at: datetime,
) -> int:
    statement = select(func.count(ChargingBooking.id)).where(
        ChargingBooking.charger_id == charger_id,
        ChargingBooking.status == "CONFIRMED",
        ChargingBooking.start_at < end_at,
        ChargingBooking.end_at > start_at,
    )
    return int(db.scalar(statement) or 0)


def _resolved_vehicle(
    db: Session,
    driver_id: UUID,
    vehicle_id: UUID | None,
) -> Vehicle | None:
    return resolve_vehicle(db, driver_id, vehicle_id)


def prepare_booking(
    db: Session,
    driver_id: UUID,
    payload: BookingProposalCreate,
    *,
    conversation_id: UUID | None = None,
) -> PendingConfirmation:
    """Create a reviewable proposal without reserving the slot."""

    station, charger = _load_station_charger(
        db,
        payload.station_id,
        payload.charger_id,
    )
    tz_name = station.timezone

    start_at = ensure_utc(payload.start_at, tz_name)
    end_at = start_at + timedelta(minutes=payload.duration_minutes)
    now = datetime.now(timezone.utc)

    if start_at < now:
        raise ValidationError("The booking start time must be in the future.")

    if not is_aligned(start_at, BOOKING_SLOT_MINUTES, tz_name):
        raise ValidationError(
            "Bookings must start on a 30-minute slot boundary."
        )

    if charger.status != "active":
        raise ConflictError("This charger is not accepting bookings.")

    vehicle = _resolved_vehicle(db, driver_id, payload.vehicle_id)
    connector_type = payload.connector_type

    if vehicle is not None and connector_type is None:
        connector_type = vehicle.connector_type

    connector = resolve_matching_connector(charger, connector_type)

    if connector is None:
        raise ConflictError(
            "This charger does not support the requested connector type."
        )

    if (
        vehicle is not None
        and vehicle.connector_type.lower()
        != connector.connector_type.lower()
    ):
        raise ValidationError(
            "The selected vehicle is not compatible with this charger."
        )

    if _overlapping_booking_count(db, charger.id, start_at, end_at):
        raise ConflictError(
            "The selected slot is no longer available. Choose another slot."
        )

    estimated_price = (
        charger.power_kw
        * Decimal(payload.duration_minutes)
        / Decimal(60)
        * charger.price_per_kwh
    ).quantize(Decimal("0.01"))

    summary = {
        "station_id": str(station.id),
        "station_name": station.name,
        "charger_id": str(charger.id),
        "charger_code": charger.charger_code,
        "connector_type": connector.connector_type,
        "start_at": start_at.isoformat(),
        "end_at": end_at.isoformat(),
        "local_start": local_iso(start_at, tz_name),
        "local_end": local_iso(end_at, tz_name),
        "timezone": tz_name,
        "duration_minutes": payload.duration_minutes,
        "price_per_kwh": str(charger.price_per_kwh),
        "estimated_price": str(estimated_price),
        "vehicle": (
            {
                "vehicle_id": str(vehicle.id),
                "registration_number": vehicle.registration_number,
                "connector_type": vehicle.connector_type,
            }
            if vehicle is not None
            else None
        ),
    }

    proposal = PendingConfirmation(
        user_id=driver_id,
        conversation_id=conversation_id,
        action="confirm_booking",
        tool="confirm_booking",
        arguments={
            "station_id": str(station.id),
            "charger_id": str(charger.id),
            "vehicle_id": str(vehicle.id) if vehicle else None,
            "connector_type": connector.connector_type,
            "start_at": start_at.isoformat(),
            "end_at": end_at.isoformat(),
            "duration_minutes": payload.duration_minutes,
            "estimated_price": str(estimated_price),
        },
        summary=summary,
        status="pending",
        expires_at=now + PROPOSAL_TTL,
    )
    db.add(proposal)
    db.commit()
    db.refresh(proposal)
    return proposal


def get_pending_proposal(
    db: Session,
    driver_id: UUID,
    confirmation_id: UUID,
) -> PendingConfirmation:
    proposal = db.scalar(
        select(PendingConfirmation).where(
            PendingConfirmation.id == confirmation_id,
            PendingConfirmation.user_id == driver_id,
            PendingConfirmation.tool == "confirm_booking",
        )
    )

    if proposal is None:
        raise NotFoundError("Booking proposal not found.")

    return proposal


def _booking_reference(now: datetime) -> str:
    return f"CM-{now:%Y%m%d}-{uuid.uuid4().hex[:6].upper()}"


def confirm_booking(
    db: Session,
    driver_id: UUID,
    confirmation_id: UUID,
) -> ChargingBooking:
    """Revalidate availability and create the booking transactionally."""

    now = datetime.now(timezone.utc)

    proposal = db.scalar(
        select(PendingConfirmation)
        .where(
            PendingConfirmation.id == confirmation_id,
            PendingConfirmation.user_id == driver_id,
            PendingConfirmation.tool == "confirm_booking",
        )
        .with_for_update()
    )

    if proposal is None:
        raise NotFoundError("Booking proposal not found.")

    if proposal.status != "pending":
        raise ConflictError(
            "This proposal has already been resolved. Start a new booking."
        )

    if proposal.expires_at is not None and as_utc(
        proposal.expires_at
    ) <= now:
        proposal.status = "expired"
        proposal.resolved_at = now
        db.commit()
        raise ConflictError(
            "This proposal has expired. Search for a slot again."
        )

    arguments = proposal.arguments or {}

    try:
        charger_id = UUID(str(arguments["charger_id"]))
        station_id = UUID(str(arguments["station_id"]))
        start_at = datetime.fromisoformat(str(arguments["start_at"]))
        end_at = datetime.fromisoformat(str(arguments["end_at"]))
    except (KeyError, TypeError, ValueError) as exc:
        raise ValidationError("The proposal data is invalid.") from exc

    start_at = ensure_utc(start_at)
    end_at = ensure_utc(end_at)

    charger = db.scalar(
        select(Charger)
        .where(Charger.id == charger_id)
        .with_for_update()
    )

    if charger is None:
        raise NotFoundError("Charger not found.")

    station = db.get(ChargingStation, station_id)

    if (
        station is None
        or not station.is_active
        or charger.station_id != station.id
    ):
        raise ConflictError("This station is no longer accepting bookings.")

    if charger.status != "active":
        raise ConflictError("This charger is not accepting bookings.")

    if end_at <= start_at:
        raise ValidationError("The proposal interval is invalid.")

    if start_at < now:
        raise ConflictError("This slot is in the past. Search again.")

    if _overlapping_booking_count(db, charger.id, start_at, end_at):
        raise ConflictError(
            "The selected slot was taken. Choose another available slot."
        )

    vehicle_id = arguments.get("vehicle_id")

    booking = ChargingBooking(
        booking_reference=_booking_reference(now),
        driver_id=driver_id,
        station_id=station.id,
        charger_id=charger.id,
        vehicle_id=UUID(str(vehicle_id)) if vehicle_id else None,
        connector_type=str(arguments.get("connector_type") or ""),
        start_at=start_at,
        end_at=end_at,
        status="CONFIRMED",
        estimated_price=(
            Decimal(str(arguments["estimated_price"]))
            if arguments.get("estimated_price") is not None
            else None
        ),
    )
    db.add(booking)

    proposal.status = "confirmed"
    proposal.resolved_at = now

    try:
        db.flush()
    except IntegrityError as exc:
        db.rollback()
        raise ConflictError(
            "The selected slot was taken. Choose another available slot."
        ) from exc

    proposal.result = {
        "booking_id": str(booking.id),
        "booking_reference": booking.booking_reference,
    }

    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise ConflictError(
            "The selected slot was taken. Choose another available slot."
        ) from exc

    return get_booking_by_id(db, driver_id, booking.id)


def get_booking_by_id(
    db: Session,
    driver_id: UUID,
    booking_id: UUID,
) -> ChargingBooking:
    booking = db.scalar(
        _booking_statement().where(
            ChargingBooking.id == booking_id,
            ChargingBooking.driver_id == driver_id,
        )
    )

    if booking is None:
        raise NotFoundError("Booking not found.")

    return booking


def _booking_statement():
    return select(ChargingBooking).options(
        selectinload(ChargingBooking.station),
        selectinload(ChargingBooking.charger),
        selectinload(ChargingBooking.vehicle),
    )


def get_booking(
    db: Session,
    driver_id: UUID,
    booking_reference: str,
) -> ChargingBooking:
    booking = db.scalar(
        _booking_statement().where(
            ChargingBooking.booking_reference == booking_reference,
            ChargingBooking.driver_id == driver_id,
        )
    )

    if booking is None:
        raise NotFoundError("Booking not found.")

    return booking


def list_bookings(
    db: Session,
    driver_id: UUID,
    *,
    status: str | None = None,
    station_id: UUID | None = None,
    upcoming_only: bool = False,
    skip: int = 0,
    limit: int = 100,
) -> list[ChargingBooking]:
    statement = _booking_statement().where(
        ChargingBooking.driver_id == driver_id
    )

    if status is not None:
        statement = statement.where(ChargingBooking.status == status)

    if station_id is not None:
        statement = statement.where(ChargingBooking.station_id == station_id)

    if upcoming_only:
        statement = statement.where(
            ChargingBooking.status == "CONFIRMED",
            ChargingBooking.end_at > datetime.now(timezone.utc),
        )
        statement = statement.order_by(ChargingBooking.start_at)
    else:
        statement = statement.order_by(ChargingBooking.start_at.desc())

    statement = (
        statement.offset(max(skip, 0))
        .limit(min(max(limit, 1), 200))
    )

    return list(db.scalars(statement).all())


def cancel_booking(
    db: Session,
    driver_id: UUID,
    booking_reference: str,
) -> ChargingBooking:
    booking = db.scalar(
        _booking_statement()
        .where(
            ChargingBooking.booking_reference == booking_reference,
            ChargingBooking.driver_id == driver_id,
        )
        .with_for_update()
    )

    if booking is None:
        raise NotFoundError("Booking not found.")

    if booking.status != "CONFIRMED":
        raise ConflictError(
            f"This booking cannot be cancelled because it is "
            f"{booking.status.lower()}."
        )

    now = datetime.now(timezone.utc)

    if as_utc(booking.start_at) - now <= CANCELLATION_CUTOFF:
        raise ConflictError(
            "Bookings can only be cancelled more than 30 minutes before "
            "the start time."
        )

    booking.status = "CANCELLED"
    booking.cancelled_at = now
    db.commit()
    db.refresh(booking)
    return booking


def booking_payload(booking: ChargingBooking) -> dict:
    station = booking.station
    tz_name = station.timezone if station else None

    return {
        "id": booking.id,
        "booking_reference": booking.booking_reference,
        "driver_id": booking.driver_id,
        "station_id": booking.station_id,
        "charger_id": booking.charger_id,
        "vehicle_id": booking.vehicle_id,
        "connector_type": booking.connector_type,
        "start_at": as_utc(booking.start_at),
        "end_at": as_utc(booking.end_at),
        "status": booking.status,
        "estimated_price": booking.estimated_price,
        "cancelled_at": booking.cancelled_at,
        "created_at": booking.created_at,
        "updated_at": booking.updated_at,
        "station_name": station.name if station else None,
        "charger_code": booking.charger.charger_code if booking.charger else None,
        "timezone": tz_name,
        "local_start": (
            local_iso(as_utc(booking.start_at), tz_name)
            if tz_name
            else None
        ),
        "local_end": (
            local_iso(as_utc(booking.end_at), tz_name)
            if tz_name
            else None
        ),
    }
