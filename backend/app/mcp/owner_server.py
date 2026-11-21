"""Owner MCP server: nine database-backed tools for a station owner.

Every tool derives the acting owner from the backend-injected
``auth_context``. Sensitive mutations return a ``confirmation_request``
until the backend executes them with ``approved=True``.
"""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from mcp.server.fastmcp import FastMCP

from app.core.config import settings
from app.core.errors import ValidationError
from app.mcp.db import session_scope
from app.mcp.auth import AuthContext, parse_auth_context, resolve_user
from app.mcp.serializers import (
    session_summary,
    station_detail,
    station_summary,
)
from app.mcp.tooling import (
    confirmation_required,
    guarded,
    ok,
    run_server,
)
from app.schemas.station import (
    RevenueSummary,
    StationCreate,
    StationUpdate,
)
from app.services import owner_service

mcp = FastMCP("chargemate-owner-tools")

ROLE = "owner"


def _context(db, auth_context) -> AuthContext:
    context = parse_auth_context(auth_context, ROLE)
    resolve_user(db, context, ROLE)
    return context


def _uuid(value: Any, field: str) -> UUID:
    try:
        return UUID(str(value))
    except (TypeError, ValueError) as exc:
        raise ValidationError(f"{field} must be a valid UUID.") from exc


def _datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value))
    except ValueError as exc:
        raise ValidationError("Timestamps must be ISO-8601 values.") from exc


# ---------------------------------------------------------------------------
# Read tools
# ---------------------------------------------------------------------------


@guarded
def get_owner_stations(
    include_inactive: bool = False,
    auth_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """List the authenticated owner's charging stations."""

    with session_scope() as db:
        context = _context(db, auth_context)
        stations = owner_service.list_owned_stations(
            db,
            context.user_id,
        )
        data = [
            station_summary(station)
            for station in stations
            if include_inactive or station.is_active
        ]
        return ok({"count": len(data), "stations": data})


@guarded
def get_station_details(
    station_id: str,
    auth_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Return one owned station with its chargers and connectors."""

    with session_scope() as db:
        context = _context(db, auth_context)
        station = owner_service.get_owned_station(
            db,
            context.user_id,
            _uuid(station_id, "station_id"),
        )
        return ok(station_detail(station))


@guarded
def get_charging_sessions(
    station_id: str | None = None,
    charger_id: str | None = None,
    start_at: str | None = None,
    end_at: str | None = None,
    status: str | None = None,
    limit: int = 50,
    auth_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """List charging sessions across the owner's network."""

    with session_scope() as db:
        context = _context(db, auth_context)
        sessions = owner_service.list_sessions(
            db,
            context.user_id,
            station_id=_uuid(station_id, "station_id") if station_id else None,
            charger_id=_uuid(charger_id, "charger_id") if charger_id else None,
            start_at=_datetime(start_at),
            end_at=_datetime(end_at),
            status=status,
            limit=limit,
        )
        data = [session_summary(session) for session in sessions]
        return ok({"count": len(data), "sessions": data})


@guarded
def get_station_revenue(
    station_id: str | None = None,
    start_at: str | None = None,
    end_at: str | None = None,
    auth_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Calculate revenue from completed sessions for a station or network."""

    with session_scope() as db:
        context = _context(db, auth_context)
        period_start = _datetime(start_at)
        period_end = _datetime(end_at)

        if station_id:
            summary = owner_service.station_revenue(
                db,
                context.user_id,
                _uuid(station_id, "station_id"),
                start_at=period_start,
                end_at=period_end,
            )
            return ok(summary.model_dump(mode="json"))

        analytics = owner_service.owner_analytics(
            db,
            context.user_id,
            start_at=period_start,
            end_at=period_end,
        )
        summary = RevenueSummary(
            station_id=None,
            start_at=period_start,
            end_at=period_end,
            session_count=analytics.session_count,
            total_energy_kwh=analytics.total_energy_kwh,
            total_revenue=analytics.total_revenue,
        )
        return ok(summary.model_dump(mode="json"))


@guarded
def get_station_analytics(
    station_id: str | None = None,
    start_at: str | None = None,
    end_at: str | None = None,
    auth_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Return operational analytics for one station or the whole network."""

    with session_scope() as db:
        context = _context(db, auth_context)
        period_start = _datetime(start_at)
        period_end = _datetime(end_at)

        if station_id:
            analytics = owner_service.station_analytics(
                db,
                context.user_id,
                _uuid(station_id, "station_id"),
                start_at=period_start,
                end_at=period_end,
            )
            return ok(analytics.model_dump(mode="json"))

        network = owner_service.owner_analytics(
            db,
            context.user_id,
            start_at=period_start,
            end_at=period_end,
        )
        return ok(network.model_dump(mode="json"))


# ---------------------------------------------------------------------------
# Sensitive mutations
# ---------------------------------------------------------------------------


@guarded
def create_station(
    name: str,
    city: str,
    state: str,
    pincode: str,
    description: str | None = None,
    address_line1: str | None = None,
    address_line2: str | None = None,
    latitude: float | None = None,
    longitude: float | None = None,
    timezone: str = "Asia/Kolkata",
    chargers: list[dict[str, Any]] | None = None,
    auth_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Register a new charging station for the authenticated owner."""

    with session_scope() as db:
        context = _context(db, auth_context)

        payload = {
            "name": name,
            "city": city,
            "state": state,
            "pincode": pincode,
            "description": description,
            "address_line1": address_line1,
            "address_line2": address_line2,
            "latitude": latitude,
            "longitude": longitude,
            "timezone": timezone,
            "chargers": chargers or [],
        }

        if not context.approved:
            return confirmation_required(
                tool="create_station",
                action="create_station",
                arguments={key: value for key, value in payload.items()},
                summary={
                    "name": name,
                    "city": city,
                    "state": state,
                    "charger_count": len(chargers or []),
                },
            )

        station = owner_service.create_station(
            db,
            context.user_id,
            StationCreate.model_validate(payload),
        )
        return ok(station_detail(station))


@guarded
def update_station(
    station_id: str,
    name: str | None = None,
    description: str | None = None,
    address_line1: str | None = None,
    address_line2: str | None = None,
    city: str | None = None,
    state: str | None = None,
    pincode: str | None = None,
    latitude: float | None = None,
    longitude: float | None = None,
    timezone: str | None = None,
    is_active: bool | None = None,
    auth_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Update details of an owned station."""

    with session_scope() as db:
        context = _context(db, auth_context)
        target = _uuid(station_id, "station_id")

        changes = {
            key: value
            for key, value in {
                "name": name,
                "description": description,
                "address_line1": address_line1,
                "address_line2": address_line2,
                "city": city,
                "state": state,
                "pincode": pincode,
                "latitude": latitude,
                "longitude": longitude,
                "timezone": timezone,
                "is_active": is_active,
            }.items()
            if value is not None
        }

        if not changes:
            raise ValidationError("No station fields were supplied to update.")

        arguments = {"station_id": str(target), **changes}

        if not context.approved:
            return confirmation_required(
                tool="update_station",
                action="update_station",
                arguments=arguments,
                summary={
                    "station_id": str(target),
                    "changes": changes,
                },
            )

        station = owner_service.update_station(
            db,
            context.user_id,
            target,
            StationUpdate.model_validate(changes),
        )
        return ok(station_detail(station))


@guarded
def update_charger_status(
    charger_id: str,
    status: str,
    auth_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Change the operational status of an owned charger."""

    normalized = str(status).strip().lower()

    if normalized not in {"active", "inactive", "maintenance", "faulted"}:
        raise ValidationError(
            "status must be one of active, inactive, maintenance, faulted."
        )

    with session_scope() as db:
        context = _context(db, auth_context)
        target = _uuid(charger_id, "charger_id")

        if not context.approved:
            return confirmation_required(
                tool="update_charger_status",
                action="update_charger_status",
                arguments={
                    "charger_id": str(target),
                    "status": normalized,
                },
                summary={
                    "charger_id": str(target),
                    "status": normalized,
                },
            )

        charger = owner_service.set_charger_status(
            db,
            context.user_id,
            target,
            normalized,
        )
        return ok(
            {
                "id": str(charger.id),
                "station_id": str(charger.station_id),
                "charger_code": charger.charger_code,
                "status": charger.status,
                "availability": charger.availability,
            }
        )


@guarded
def update_charging_price(
    charger_id: str,
    price_per_kwh: Decimal | str | float,
    auth_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Update the per-kWh charging price of an owned charger."""

    price = Decimal(str(price_per_kwh))

    if price < 0:
        raise ValidationError("price_per_kwh cannot be negative.")

    with session_scope() as db:
        context = _context(db, auth_context)
        target = _uuid(charger_id, "charger_id")

        if not context.approved:
            return confirmation_required(
                tool="update_charging_price",
                action="update_charging_price",
                arguments={
                    "charger_id": str(target),
                    "price_per_kwh": str(price),
                },
                summary={
                    "charger_id": str(target),
                    "price_per_kwh": str(price),
                },
            )

        charger = owner_service.set_charger_price(
            db,
            context.user_id,
            target,
            price,
        )
        return ok(
            {
                "id": str(charger.id),
                "station_id": str(charger.station_id),
                "charger_code": charger.charger_code,
                "price_per_kwh": str(charger.price_per_kwh),
            }
        )


OWNER_TOOLS = (
    get_owner_stations,
    get_station_details,
    get_charging_sessions,
    get_station_revenue,
    get_station_analytics,
    create_station,
    update_station,
    update_charger_status,
    update_charging_price,
)

for _tool in OWNER_TOOLS:
    mcp.add_tool(_tool)


if __name__ == "__main__":
    run_server(
        mcp,
        default_host=settings.mcp_owner_host,
        default_port=settings.mcp_owner_port,
    )
