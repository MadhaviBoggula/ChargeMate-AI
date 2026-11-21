from __future__ import annotations

import json
from typing import Any

from app.models.charger import Charger
from app.models.charging_session import ChargingSession
from app.models.driver_preference import DriverPreference
from app.models.favourite_station import FavouriteStation
from app.models.station import ChargingStation
from app.models.vehicle import Vehicle
from app.schemas.booking import AvailableSlot, StationAvailabilityOut
from app.services.booking_service import booking_payload
from app.services.time_utils import as_utc


def _money(value) -> str | None:
    return None if value is None else str(value)


def connector_summary(connector) -> dict[str, Any]:
    return {
        "id": str(connector.id),
        "connector_type": connector.connector_type,
        "power_kw": str(connector.power_kw),
        "status": connector.status,
    }


def charger_summary(charger: Charger) -> dict[str, Any]:
    return {
        "id": str(charger.id),
        "station_id": str(charger.station_id),
        "charger_code": charger.charger_code,
        "charging_type": charger.charging_type,
        "power_kw": str(charger.power_kw),
        "status": charger.status,
        "availability": charger.availability,
        "price_per_kwh": str(charger.price_per_kwh),
        "connectors": [
            connector_summary(connector)
            for connector in charger.connectors
        ],
    }


def station_summary(station: ChargingStation) -> dict[str, Any]:
    return {
        "id": str(station.id),
        "owner_id": str(station.owner_id),
        "name": station.name,
        "description": station.description,
        "address_line1": station.address_line1,
        "address_line2": station.address_line2,
        "city": station.city,
        "state": station.state,
        "pincode": station.pincode,
        "latitude": station.latitude,
        "longitude": station.longitude,
        "timezone": station.timezone,
        "is_active": station.is_active,
        "connector_types": station.connector_types,
        "min_price_per_kwh": _money(station.min_price_per_kwh),
        "max_power_kw": _money(station.max_power_kw),
        "total_chargers": station.total_chargers,
        "available_chargers": station.available_chargers,
    }


def station_detail(station: ChargingStation) -> dict[str, Any]:
    return {
        **station_summary(station),
        "chargers": [
            charger_summary(charger) for charger in station.chargers
        ],
    }


def session_summary(session: ChargingSession) -> dict[str, Any]:
    return {
        "id": str(session.id),
        "station_id": str(session.station_id),
        "station_name": session.station.name if session.station else None,
        "charger_id": str(session.charger_id),
        "charger_code": (
            session.charger.charger_code if session.charger else None
        ),
        "driver_id": str(session.driver_id) if session.driver_id else None,
        "booking_id": str(session.booking_id) if session.booking_id else None,
        "started_at": as_utc(session.started_at).isoformat(),
        "ended_at": (
            as_utc(session.ended_at).isoformat()
            if session.ended_at
            else None
        ),
        "energy_kwh": str(session.energy_kwh),
        "duration_minutes": session.duration_minutes,
        "price_per_kwh": str(session.price_per_kwh),
        "revenue": str(session.revenue),
        "status": session.status,
    }


def vehicle_summary(vehicle: Vehicle) -> dict[str, Any]:
    return {
        "id": str(vehicle.id),
        "registration_number": vehicle.registration_number,
        "nickname": vehicle.nickname,
        "vehicle_model": vehicle.vehicle_model,
        "vehicle_type": vehicle.vehicle_type,
        "manufacturing_year": vehicle.manufacturing_year,
        "battery_capacity_kwh": _money(vehicle.battery_capacity_kwh),
        "connector_type": vehicle.connector_type,
        "is_primary": vehicle.is_primary,
    }


def preference_summary(preference: DriverPreference) -> dict[str, Any]:
    return {
        "driver_id": str(preference.driver_id),
        "preferred_connector_type": preference.preferred_connector_type,
        "preferred_charging_type": preference.preferred_charging_type,
        "max_price_per_kwh": _money(preference.max_price_per_kwh),
        "preferred_city": preference.preferred_city,
        "default_vehicle_id": (
            str(preference.default_vehicle_id)
            if preference.default_vehicle_id
            else None
        ),
    }


def favourite_summary(favourite: FavouriteStation) -> dict[str, Any]:
    station = favourite.station

    return {
        "id": str(favourite.id),
        "station_id": str(favourite.station_id),
        "station": station_summary(station) if station else None,
        "created_at": as_utc(favourite.created_at).isoformat(),
    }


def slot_summary(slot: AvailableSlot) -> dict[str, Any]:
    return slot.model_dump(mode="json")


def availability_summary(
    availability: StationAvailabilityOut,
) -> dict[str, Any]:
    return availability.model_dump(mode="json")


def booking_summary(booking) -> dict[str, Any]:
    """Return a JSON-native booking payload for MCP responses."""

    return json.loads(json.dumps(booking_payload(booking), default=str))
