from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.core.errors import ConflictError, NotFoundError, ValidationError
from app.models.booking import ChargingBooking
from app.models.charger import Charger
from app.models.connector import Connector
from app.models.driver_preference import DriverPreference
from app.models.favourite_station import FavouriteStation
from app.models.station import ChargingStation
from app.models.vehicle import Vehicle
from app.schemas.booking import (
    ChargerAvailabilityOut,
    StationAvailabilityOut,
)
from app.schemas.driver import VehicleCreate, VehicleUpdate
from app.services.station_service import (
    get_active_station,
    station_load_options,
)
from app.services.time_utils import as_utc

MAX_VEHICLES_PER_DRIVER = 10


# ---------------------------------------------------------------------------
# Vehicles
# ---------------------------------------------------------------------------


def list_vehicles(db: Session, driver_id: UUID) -> list[Vehicle]:
    statement = (
        select(Vehicle)
        .where(Vehicle.driver_id == driver_id)
        .order_by(Vehicle.is_primary.desc(), Vehicle.created_at)
    )
    return list(db.scalars(statement).all())


def get_vehicle(
    db: Session,
    driver_id: UUID,
    vehicle_id: UUID,
) -> Vehicle:
    vehicle = db.scalar(
        select(Vehicle).where(
            Vehicle.id == vehicle_id,
            Vehicle.driver_id == driver_id,
        )
    )

    if vehicle is None:
        raise NotFoundError("Vehicle not found.")

    return vehicle


def _clear_other_primary(
    db: Session,
    driver_id: UUID,
    keep_id: UUID | None = None,
) -> None:
    statement = select(Vehicle).where(
        Vehicle.driver_id == driver_id,
        Vehicle.is_primary.is_(True),
    )

    for vehicle in db.scalars(statement).all():
        if keep_id is None or vehicle.id != keep_id:
            vehicle.is_primary = False


def create_vehicle(
    db: Session,
    driver_id: UUID,
    payload: VehicleCreate,
) -> Vehicle:
    existing_count = db.scalar(
        select(func.count(Vehicle.id)).where(
            Vehicle.driver_id == driver_id
        )
    ) or 0

    if existing_count >= MAX_VEHICLES_PER_DRIVER:
        raise ValidationError(
            f"A driver can register at most "
            f"{MAX_VEHICLES_PER_DRIVER} vehicles."
        )

    should_be_primary = payload.is_primary or existing_count == 0

    if should_be_primary:
        _clear_other_primary(db, driver_id)

    vehicle = Vehicle(
        driver_id=driver_id,
        **payload.model_dump(exclude={"is_primary"}),
        is_primary=should_be_primary,
    )
    db.add(vehicle)

    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise ConflictError(
            "A vehicle with this registration number already exists."
        ) from exc

    db.refresh(vehicle)
    return vehicle


def update_vehicle(
    db: Session,
    driver_id: UUID,
    vehicle_id: UUID,
    payload: VehicleUpdate,
) -> Vehicle:
    vehicle = get_vehicle(db, driver_id, vehicle_id)
    data = payload.model_dump(exclude_unset=True)

    non_nullable = {
        "registration_number",
        "vehicle_type",
        "connector_type",
        "is_primary",
    }

    for key, value in data.items():
        if key in non_nullable and value is None:
            raise ValidationError(f"{key} cannot be null.")
        setattr(vehicle, key, value)

    if data.get("is_primary"):
        _clear_other_primary(db, driver_id, keep_id=vehicle.id)
        vehicle.is_primary = True

    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise ConflictError(
            "A vehicle with this registration number already exists."
        ) from exc

    db.refresh(vehicle)
    return vehicle


def delete_vehicle(
    db: Session,
    driver_id: UUID,
    vehicle_id: UUID,
) -> None:
    vehicle = get_vehicle(db, driver_id, vehicle_id)
    was_primary = vehicle.is_primary

    db.delete(vehicle)
    db.flush()

    if was_primary:
        replacement = db.scalar(
            select(Vehicle)
            .where(Vehicle.driver_id == driver_id)
            .order_by(Vehicle.created_at)
            .limit(1)
        )

        if replacement is not None:
            replacement.is_primary = True

    db.commit()


def resolve_vehicle(
    db: Session,
    driver_id: UUID,
    vehicle_id: UUID | None = None,
) -> Vehicle | None:
    """Return the requested vehicle, the preference default, or primary."""

    if vehicle_id is not None:
        return get_vehicle(db, driver_id, vehicle_id)

    preference = db.scalar(
        select(DriverPreference).where(
            DriverPreference.driver_id == driver_id
        )
    )

    if preference is not None and preference.default_vehicle_id:
        default_vehicle = db.scalar(
            select(Vehicle).where(
                Vehicle.id == preference.default_vehicle_id,
                Vehicle.driver_id == driver_id,
            )
        )

        if default_vehicle is not None:
            return default_vehicle

    return db.scalar(
        select(Vehicle)
        .where(
            Vehicle.driver_id == driver_id,
            Vehicle.is_primary.is_(True),
        )
        .order_by(Vehicle.created_at)
    )


# ---------------------------------------------------------------------------
# Preferences
# ---------------------------------------------------------------------------


def get_or_create_preferences(
    db: Session,
    driver_id: UUID,
) -> DriverPreference:
    preference = db.scalar(
        select(DriverPreference).where(
            DriverPreference.driver_id == driver_id
        )
    )

    if preference is not None:
        return preference

    preference = DriverPreference(driver_id=driver_id)
    db.add(preference)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        preference = db.scalar(
            select(DriverPreference).where(
                DriverPreference.driver_id == driver_id
            )
        )
        if preference is None:
            raise
        return preference

    db.refresh(preference)
    return preference


def update_preferences(
    db: Session,
    driver_id: UUID,
    payload,
) -> DriverPreference:
    preference = get_or_create_preferences(db, driver_id)
    data = payload.model_dump(exclude_unset=True)

    default_vehicle_id = data.get("default_vehicle_id")

    if default_vehicle_id is not None:
        get_vehicle(db, driver_id, default_vehicle_id)

    for key, value in data.items():
        setattr(preference, key, value)

    db.commit()
    db.refresh(preference)
    return preference


# ---------------------------------------------------------------------------
# Favourite stations
# ---------------------------------------------------------------------------


def list_favourites(
    db: Session,
    driver_id: UUID,
) -> list[FavouriteStation]:
    statement = (
        select(FavouriteStation)
        .options(
            selectinload(FavouriteStation.station).options(
                *station_load_options()
            )
        )
        .join(ChargingStation, FavouriteStation.station_id == ChargingStation.id)
        .where(
            FavouriteStation.driver_id == driver_id,
            ChargingStation.is_active.is_(True),
        )
        .order_by(FavouriteStation.created_at.desc())
    )
    return list(db.scalars(statement).all())


def add_favourite(
    db: Session,
    driver_id: UUID,
    station_id: UUID,
) -> FavouriteStation:
    get_active_station(db, station_id)

    existing = db.scalar(
        select(FavouriteStation).where(
            FavouriteStation.driver_id == driver_id,
            FavouriteStation.station_id == station_id,
        )
    )

    if existing is not None:
        raise ConflictError("This station is already in your favourites.")

    favourite = FavouriteStation(
        driver_id=driver_id,
        station_id=station_id,
    )
    db.add(favourite)

    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise ConflictError(
            "This station is already in your favourites."
        ) from exc

    return db.scalar(
        select(FavouriteStation)
        .options(
            selectinload(FavouriteStation.station).options(
                *station_load_options()
            )
        )
        .where(FavouriteStation.id == favourite.id)
    )


def remove_favourite(
    db: Session,
    driver_id: UUID,
    station_id: UUID,
) -> None:
    favourite = db.scalar(
        select(FavouriteStation).where(
            FavouriteStation.driver_id == driver_id,
            FavouriteStation.station_id == station_id,
        )
    )

    if favourite is None:
        raise NotFoundError("Favourite station not found.")

    db.delete(favourite)
    db.commit()


# ---------------------------------------------------------------------------
# Compatibility
# ---------------------------------------------------------------------------


def compatible_stations(
    db: Session,
    driver_id: UUID,
    *,
    vehicle_id: UUID | None = None,
    city: str | None = None,
    limit: int = 100,
) -> list[dict]:
    vehicle = resolve_vehicle(db, driver_id, vehicle_id)

    if vehicle is None:
        raise ValidationError(
            "Register a vehicle first so compatibility can be checked."
        )

    connector_type = vehicle.connector_type

    statement = (
        select(ChargingStation)
        .options(*station_load_options())
        .where(ChargingStation.is_active.is_(True))
        .order_by(ChargingStation.name)
    )

    if city:
        statement = statement.where(
            func.lower(ChargingStation.city) == city.lower()
        )

    stations = list(db.scalars(statement).all())
    matches: list[dict] = []

    for station in stations:
        matched_charger_ids = [
            charger.id
            for charger in station.chargers
            if charger.status == "active"
            and any(
                connector.status == "active"
                and connector.connector_type.lower()
                == connector_type.lower()
                for connector in charger.connectors
            )
        ]

        if matched_charger_ids:
            matches.append(
                {
                    "station": station,
                    "compatible_charger_ids": matched_charger_ids,
                    "matched_connector_type": connector_type,
                }
            )

    return matches[: max(1, min(limit, 200))]


# ---------------------------------------------------------------------------
# Availability
# ---------------------------------------------------------------------------


def station_availability(
    db: Session,
    station_id: UUID,
) -> StationAvailabilityOut:
    station = get_active_station(db, station_id)
    now = datetime.now(timezone.utc)

    charger_ids = [charger.id for charger in station.chargers]

    active_bookings: dict[UUID, ChargingBooking] = {}

    if charger_ids:
        rows = db.scalars(
            select(ChargingBooking).where(
                ChargingBooking.charger_id.in_(charger_ids),
                ChargingBooking.status == "CONFIRMED",
                ChargingBooking.start_at <= now,
                ChargingBooking.end_at > now,
            )
        ).all()

        active_bookings = {booking.charger_id: booking for booking in rows}

    chargers: list[ChargerAvailabilityOut] = []

    for charger in station.chargers:
        current = active_bookings.get(charger.id)
        connector_types = sorted(
            {
                connector.connector_type
                for connector in charger.connectors
                if connector.status == "active"
            }
        )

        available_now = charger.status == "active" and current is None

        chargers.append(
            ChargerAvailabilityOut(
                charger_id=charger.id,
                charger_code=charger.charger_code,
                charging_type=charger.charging_type,
                power_kw=charger.power_kw,
                price_per_kwh=charger.price_per_kwh,
                status=charger.status,
                connector_types=connector_types,
                available_now=available_now,
                booked_until=as_utc(current.end_at) if current else None,
                next_available_at=(
                    as_utc(current.end_at) if current else None
                ),
            )
        )

    return StationAvailabilityOut(
        station_id=station.id,
        station_name=station.name,
        timezone=station.timezone,
        as_of=now,
        chargers=chargers,
    )


def resolve_matching_connector(
    charger: Charger,
    connector_type: str | None,
) -> Connector | None:
    active = [
        connector
        for connector in charger.connectors
        if connector.status == "active"
    ]

    if connector_type:
        for connector in active:
            if connector.connector_type.lower() == connector_type.lower():
                return connector
        return None

    return active[0] if active else None
