from typing import Any
from uuid import UUID

from mcp.server.fastmcp import FastMCP
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.database.session import SessionLocal
from app.models.charger import Charger
from app.models.station import Station
from app.models.user import User, UserRole


mcp = FastMCP("chargemate-driver-tools")


# ---------------------------------------------------------
# Authentication
# ---------------------------------------------------------

def get_authenticated_driver(
    db: Session,
    auth_context: dict[str, Any],
) -> UUID:
    """
    Validate the trusted identity injected by the MCP client.

    Never accept a driver ID from ordinary LLM tool arguments.
    """

    if not isinstance(auth_context, dict):
        raise ValueError("Authentication context is missing.")

    if auth_context.get("role") != UserRole.DRIVER.value:
        raise PermissionError("Only drivers can use these tools.")

    try:
        driver_id = UUID(str(auth_context.get("user_id")))
    except (ValueError, TypeError):
        raise PermissionError("Invalid authenticated user identity.")

    user = db.get(User, driver_id)

    if user is None or not user.is_active:
        raise PermissionError("Driver account is unavailable.")

    if user.role != UserRole.DRIVER:
        raise PermissionError("Driver permissions are required.")

    return driver_id


# ---------------------------------------------------------
# Response helpers
# ---------------------------------------------------------

def station_summary(station: Station) -> dict[str, Any]:
    """Return JSON-compatible station information."""

    return {
        "id": str(station.id),
        "name": station.name,
        "location": station.location,
        "address": station.address,
        "connectors": station.connectors or [],
        "charger_type": station.charger_type,
        "power": station.power,
        "speed": station.speed,
        "available_slots": station.available_slots,
        "total_slots": station.total_slots,
        "price_per_kwh": station.price_per_kwh,
        "description": station.description,
        "is_active": station.is_active,
    }


def charger_summary(charger: Charger) -> dict[str, Any]:
    """Return JSON-compatible charger information."""

    return {
        "id": charger.id,
        "station_id": str(charger.station_id),
        "charger_code": charger.charger_code,
        "connector_type": charger.connector_type,
        "charging_type": charger.charging_type,
        "power_kw": float(charger.power_kw),
        "status": charger.status,
        "availability": charger.availability,
        "price_per_kwh": float(charger.price_per_kwh),
    }


def is_available(charger: Charger) -> bool:
    """Check whether a charger can currently be used."""

    return (
        str(charger.status).lower() == "active"
        and str(charger.availability).lower() == "available"
    )


# ---------------------------------------------------------
# Tool 1: Search charging stations
# ---------------------------------------------------------

@mcp.tool()
def search_stations(
    auth_context: dict[str, Any],
    query: str = "",
    connector_type: str = "",
    charging_type: str = "",
    min_power_kw: float | None = None,
    max_price_per_kwh: float | None = None,
    limit: int = 20,
) -> dict[str, Any]:
    """
    Search active charging stations.

    Supports text, connector, charging type, minimum power,
    and maximum price filters.
    """

    with SessionLocal() as db:
        get_authenticated_driver(db, auth_context)

        statement = select(Station).where(
            Station.is_active.is_(True)
        )

        if query.strip():
            search_term = f"%{query.strip()}%"
            statement = statement.where(
                or_(
                    Station.name.ilike(search_term),
                    Station.location.ilike(search_term),
                    Station.address.ilike(search_term),
                )
            )

        stations = db.scalars(
            statement.order_by(Station.name).limit(
                max(1, min(limit, 50))
            )
        ).all()

        results = []

        for station in stations:
            if connector_type:
                requested_connector = connector_type.strip().lower()

                station_connectors = [
                    str(value).lower()
                    for value in (station.connectors or [])
                ]

                charger_matches = any(
                    charger.connector_type.lower()
                    == requested_connector
                    and is_available(charger)
                    for charger in station.chargers
                )

                if (
                    requested_connector not in station_connectors
                    and not charger_matches
                ):
                    continue

            if charging_type:
                requested_type = charging_type.strip().upper()

                if station.charger_type.upper() != requested_type:
                    if not any(
                        charger.charging_type.upper() == requested_type
                        and is_available(charger)
                        for charger in station.chargers
                    ):
                        continue

            if (
                min_power_kw is not None
                and station.power < min_power_kw
                and not any(
                    float(charger.power_kw) >= min_power_kw
                    and is_available(charger)
                    for charger in station.chargers
                )
            ):
                continue

            if (
                max_price_per_kwh is not None
                and station.price_per_kwh > max_price_per_kwh
                and not any(
                    float(charger.price_per_kwh)
                    <= max_price_per_kwh
                    and is_available(charger)
                    for charger in station.chargers
                )
            ):
                continue

            results.append(station_summary(station))

        return {
            "status": "ok",
            "count": len(results),
            "stations": results,
        }


# ---------------------------------------------------------
# Tool 2: Get station details
# ---------------------------------------------------------

@mcp.tool()
def get_station_details(
    auth_context: dict[str, Any],
    station_id: str,
) -> dict[str, Any]:
    """Get details and charger information for one active station."""

    with SessionLocal() as db:
        get_authenticated_driver(db, auth_context)

        try:
            parsed_id = UUID(station_id)
        except (ValueError, TypeError):
            return {
                "status": "error",
                "detail": "Invalid station ID.",
            }

        station = db.get(Station, parsed_id)

        if station is None or not station.is_active:
            return {
                "status": "error",
                "detail": "Active station not found.",
            }

        return {
            "status": "ok",
            "station": station_summary(station),
            "chargers": [
                charger_summary(charger)
                for charger in station.chargers
            ],
        }


# ---------------------------------------------------------
# Tool 3: Check station availability
# ---------------------------------------------------------

@mcp.tool()
def check_station_availability(
    auth_context: dict[str, Any],
    station_id: str,
) -> dict[str, Any]:
    """
    Check station slot counts and currently available chargers.

    Reports station-level slot counts separately from charger-level
    availability because they are different database fields.
    """

    with SessionLocal() as db:
        get_authenticated_driver(db, auth_context)

        try:
            parsed_id = UUID(station_id)
        except (ValueError, TypeError):
            return {
                "status": "error",
                "detail": "Invalid station ID.",
            }

        station = db.get(Station, parsed_id)

        if station is None or not station.is_active:
            return {
                "status": "error",
                "detail": "Active station not found.",
            }

        active_chargers = [
            charger
            for charger in station.chargers
            if str(charger.status).lower() == "active"
        ]

        available_chargers = [
            charger
            for charger in active_chargers
            if is_available(charger)
        ]

        return {
            "status": "ok",
            "station_id": str(station.id),
            "station_name": station.name,
            "station_slots": {
                "available": station.available_slots,
                "total": station.total_slots,
            },
            "charger_counts": {
                "active": len(active_chargers),
                "available": len(available_chargers),
            },
            "available_chargers": [
                charger_summary(charger)
                for charger in available_chargers
            ],
        }


# ---------------------------------------------------------
# Tool 4: Find compatible charging stations
# ---------------------------------------------------------

@mcp.tool()
def filter_compatible_stations(
    auth_context: dict[str, Any],
    connector_type: str,
    charging_type: str = "",
    min_power_kw: float | None = None,
    max_price_per_kwh: float | None = None,
    limit: int = 20,
) -> dict[str, Any]:
    """
    Find active stations with an available compatible charger.

    Compatibility is checked against the actual charger records.
    """

    with SessionLocal() as db:
        get_authenticated_driver(db, auth_context)

        requested_connector = connector_type.strip().lower()

        if not requested_connector:
            return {
                "status": "error",
                "detail": "Connector type is required.",
            }

        requested_type = charging_type.strip().upper()

        if requested_type and requested_type not in {"AC", "DC"}:
            return {
                "status": "error",
                "detail": "Charging type must be AC or DC.",
            }

        stations = db.scalars(
            select(Station)
            .where(Station.is_active.is_(True))
            .order_by(Station.name)
        ).all()

        results = []

        for station in stations:
            matching_chargers = []

            for charger in station.chargers:
                if not is_available(charger):
                    continue

                if (
                    charger.connector_type.strip().lower()
                    != requested_connector
                ):
                    continue

                if (
                    requested_type
                    and charger.charging_type.upper() != requested_type
                ):
                    continue

                if (
                    min_power_kw is not None
                    and float(charger.power_kw) < min_power_kw
                ):
                    continue

                if (
                    max_price_per_kwh is not None
                    and float(charger.price_per_kwh)
                    > max_price_per_kwh
                ):
                    continue

                matching_chargers.append(
                    charger_summary(charger)
                )

            if matching_chargers:
                results.append({
                    "station": station_summary(station),
                    "compatible_chargers": matching_chargers,
                })

            if len(results) >= max(1, min(limit, 50)):
                break

        return {
            "status": "ok",
            "connector_type": connector_type,
            "charging_type": requested_type or None,
            "count": len(results),
            "stations": results,
        }


if __name__ == "__main__":
    mcp.run(transport="stdio")
