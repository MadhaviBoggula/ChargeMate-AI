from typing import Any
from uuid import UUID

from mcp.server.fastmcp import FastMCP
from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.database.session import SessionLocal
from app.models.charger import Charger
from app.models.station import Station
from app.models.user import User, UserRole
from app.schemas.owner_charger import (
    OwnerChargerCreate,
    OwnerChargerResponse,
    OwnerChargerUpdate,
)
from app.schemas.owner_station import (
    OwnerStationCreate,
    OwnerStationResponse,
    OwnerStationUpdate,
)

mcp = FastMCP("chargemate-owner-tools")


def get_authenticated_owner(db, auth_context: dict[str, Any]) -> UUID:
    """Validate the authenticated owner supplied by the MCP registry."""

    if not isinstance(auth_context, dict):
        raise ValueError("Authentication context is missing.")

    if auth_context.get("role") != UserRole.OWNER.value:
        raise PermissionError("Only owners can use these tools.")

    try:
        owner_id = UUID(str(auth_context.get("user_id")))
    except (ValueError, TypeError):
        raise PermissionError("Invalid authenticated user identity.")

    user = db.get(User, owner_id)

    if user is None or not user.is_active:
        raise PermissionError("Owner account is unavailable.")

    if user.role != UserRole.OWNER:
        raise PermissionError("Owner permissions are required.")

    return owner_id


def get_owned_station(db, owner_id: UUID, station_id: str) -> Station:
    """Find a station only if it belongs to the authenticated owner."""

    try:
        parsed_id = UUID(str(station_id))
    except (ValueError, TypeError):
        raise ValueError("Invalid station ID.")

    statement = select(Station).where(
        Station.id == parsed_id,
        Station.owner_id == owner_id,
    )

    station = db.scalar(statement)

    if station is None:
        raise LookupError("Station not found.")

    return station


def get_owned_charger(db, owner_id: UUID, charger_id: int) -> Charger:
    """Find a charger only if its parent station belongs to the owner."""

    if charger_id <= 0:
        raise ValueError("Invalid charger ID.")

    statement = (
        select(Charger)
        .join(Station, Charger.station_id == Station.id)
        .where(
            Charger.id == charger_id,
            Station.owner_id == owner_id,
        )
    )

    charger = db.scalar(statement)

    if charger is None:
        raise LookupError("Charger not found.")

    return charger


def station_response(station: Station) -> dict:
    """Convert a station model into JSON-compatible response data."""

    return OwnerStationResponse.model_validate(station).model_dump(
        mode="json"
    )


def charger_response(charger: Charger) -> dict:
    """Convert a charger model into JSON-compatible response data."""

    return OwnerChargerResponse.model_validate(charger).model_dump(
        mode="json"
    )


def error_response(exc: Exception) -> dict:
    if isinstance(exc, PermissionError):
        return {"status": "error", "detail": str(exc)}

    if isinstance(exc, LookupError):
        return {"status": "error", "detail": str(exc)}

    if isinstance(exc, (ValueError, ValidationError)):
        return {"status": "error", "detail": str(exc)}

    return {
        "status": "error",
        "detail": "The requested owner operation failed.",
    }


# ============================================================
# STATION TOOLS
# ============================================================

@mcp.tool()
def list_my_stations(auth_context: dict[str, Any]) -> dict:
    """List all charging stations belonging to the authenticated owner."""

    with SessionLocal() as db:
        try:
            owner_id = get_authenticated_owner(db, auth_context)

            statement = (
                select(Station)
                .where(Station.owner_id == owner_id)
                .order_by(Station.created_at.desc())
            )

            stations = db.scalars(statement).all()

            return {
                "status": "ok",
                "data": [station_response(s) for s in stations],
            }

        except Exception as exc:
            return error_response(exc)


@mcp.tool()
def get_station_details(
    station_id: str,
    auth_context: dict[str, Any],
) -> dict:
    """Get details of a station belonging to the authenticated owner."""

    with SessionLocal() as db:
        try:
            owner_id = get_authenticated_owner(db, auth_context)
            station = get_owned_station(db, owner_id, station_id)

            return {
                "status": "ok",
                "data": station_response(station),
            }

        except Exception as exc:
            return error_response(exc)


@mcp.tool()
def create_station(
    name: str,
    location: str,
    address: str,
    connectors: list[str],
    charger_type: str,
    power: float,
    speed: str,
    available_slots: int,
    total_slots: int,
    price_per_kwh: float,
    description: str,
    auth_context: dict[str, Any],
) -> dict:
    """Create a charging station for the authenticated owner."""

    with SessionLocal() as db:
        try:
            owner_id = get_authenticated_owner(db, auth_context)

            station_data = OwnerStationCreate.model_validate({
                "name": name,
                "location": location,
                "address": address,
                "connectors": connectors,
                "charger_type": charger_type,
                "power": power,
                "speed": speed,
                "available_slots": available_slots,
                "total_slots": total_slots,
                "price_per_kwh": price_per_kwh,
                "description": description,
            })

            station = Station(
                **station_data.model_dump(),
                owner_id=owner_id,
            )

            db.add(station)
            db.commit()
            db.refresh(station)

            return {
                "status": "ok",
                "data": station_response(station),
            }

        except Exception as exc:
            db.rollback()
            return error_response(exc)


@mcp.tool()
def update_station(
    station_id: str,
    updates: dict[str, Any],
    auth_context: dict[str, Any],
) -> dict:
    """Update details of a station belonging to the authenticated owner."""

    with SessionLocal() as db:
        try:
            owner_id = get_authenticated_owner(db, auth_context)
            station = get_owned_station(db, owner_id, station_id)

            update_data = OwnerStationUpdate.model_validate(updates)
            changes = update_data.model_dump(exclude_unset=True)

            available_slots = changes.get(
                "available_slots", station.available_slots
            )
            total_slots = changes.get(
                "total_slots", station.total_slots
            )

            if available_slots > total_slots:
                raise ValueError(
                    "Available slots cannot exceed total slots."
                )

            for field, value in changes.items():
                setattr(station, field, value)

            db.commit()
            db.refresh(station)

            return {
                "status": "ok",
                "data": station_response(station),
            }

        except Exception as exc:
            db.rollback()
            return error_response(exc)


@mcp.tool()
def deactivate_station(
    station_id: str,
    auth_context: dict[str, Any],
) -> dict:
    """Deactivate an owner's station without deleting booking history."""

    with SessionLocal() as db:
        try:
            owner_id = get_authenticated_owner(db, auth_context)
            station = get_owned_station(db, owner_id, station_id)

            station.is_active = False

            db.commit()
            db.refresh(station)

            return {
                "status": "ok",
                "data": station_response(station),
                "message": "Station deactivated successfully.",
            }

        except Exception as exc:
            db.rollback()
            return error_response(exc)


# ============================================================
# CHARGER TOOLS
# ============================================================

@mcp.tool()
def list_my_chargers(
    auth_context: dict[str, Any],
    station_id: str | None = None,
) -> dict:
    """List chargers belonging to the authenticated owner's stations."""

    with SessionLocal() as db:
        try:
            owner_id = get_authenticated_owner(db, auth_context)

            statement = (
                select(Charger)
                .join(Station, Charger.station_id == Station.id)
                .where(Station.owner_id == owner_id)
                .order_by(Charger.created_at.desc())
            )

            if station_id is not None:
                try:
                    parsed_station_id = UUID(station_id)
                except (ValueError, TypeError):
                    raise ValueError("Invalid station ID.")

                statement = statement.where(
                    Charger.station_id == parsed_station_id
                )

            chargers = db.scalars(statement).all()

            return {
                "status": "ok",
                "data": [charger_response(c) for c in chargers],
            }

        except Exception as exc:
            return error_response(exc)


@mcp.tool()
def get_charger_details(
    charger_id: int,
    auth_context: dict[str, Any],
) -> dict:
    """Get details of a charger belonging to the authenticated owner."""

    with SessionLocal() as db:
        try:
            owner_id = get_authenticated_owner(db, auth_context)
            charger = get_owned_charger(db, owner_id, charger_id)

            return {
                "status": "ok",
                "data": charger_response(charger),
            }

        except Exception as exc:
            return error_response(exc)


@mcp.tool()
def create_charger(
    station_id: str,
    charger_code: str,
    connector_type: str,
    charging_type: str,
    power_kw: float,
    auth_context: dict[str, Any],
    status: str = "active",
    availability: str = "available",
    price_per_kwh: float = 0.0,
) -> dict:
    """Create a charger under one of the authenticated owner's stations."""

    with SessionLocal() as db:
        try:
            owner_id = get_authenticated_owner(db, auth_context)

            station = get_owned_station(db, owner_id, station_id)

            charger_data = OwnerChargerCreate.model_validate({
                "station_id": station.id,
                "charger_code": charger_code,
                "connector_type": connector_type,
                "charging_type": charging_type,
                "power_kw": power_kw,
                "status": status,
                "availability": availability,
                "price_per_kwh": price_per_kwh,
            })

            charger = Charger(**charger_data.model_dump())

            db.add(charger)
            db.commit()
            db.refresh(charger)

            return {
                "status": "ok",
                "data": charger_response(charger),
                "message": "Charger created successfully.",
            }

        except IntegrityError:
            db.rollback()
            return {
                "status": "error",
                "detail": (
                    "Could not create charger. Check whether the charger "
                    "code already exists and whether the supplied values "
                    "are valid."
                ),
            }

        except Exception as exc:
            db.rollback()
            return error_response(exc)


@mcp.tool()
def update_charger(
    charger_id: int,
    updates: dict[str, Any],
    auth_context: dict[str, Any],
) -> dict:
    """Update a charger belonging to one of the authenticated owner's stations."""

    with SessionLocal() as db:
        try:
            owner_id = get_authenticated_owner(db, auth_context)
            charger = get_owned_charger(db, owner_id, charger_id)

            update_data = OwnerChargerUpdate.model_validate(updates)
            changes = update_data.model_dump(exclude_unset=True)

            for field, value in changes.items():
                setattr(charger, field, value)

            db.commit()
            db.refresh(charger)

            return {
                "status": "ok",
                "data": charger_response(charger),
                "message": "Charger updated successfully.",
            }

        except IntegrityError:
            db.rollback()
            return {
                "status": "error",
                "detail": (
                    "Could not update charger. Check the supplied values."
                ),
            }

        except Exception as exc:
            db.rollback()
            return error_response(exc)


if __name__ == "__main__":
    mcp.run(transport="stdio")
