"""Driver MCP server: fifteen database-backed tools for an EV driver.

Identity always comes from the backend-injected ``auth_context``. A
booking is only created by ``confirm_booking`` after the backend marks
the call approved from an explicit user action; ``prepare_booking``
never reserves a slot.
"""
from __future__ import annotations

from datetime import date as date_type
from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from mcp.server.fastmcp import FastMCP

from app.core.config import settings
from app.core.errors import ValidationError
from app.mcp.auth import AuthContext, parse_auth_context, resolve_user
from app.mcp.db import session_scope
from app.mcp.serializers import (
    availability_summary,
    booking_summary,
    favourite_summary,
    preference_summary,
    slot_summary,
    station_detail,
    station_summary,
)
from app.mcp.tooling import (
    confirmation_required,
    guarded,
    ok,
    run_server,
)
from app.schemas.booking import BookingProposalCreate
from app.schemas.driver import DriverPreferenceUpdate
from app.services import booking_service, driver_service, station_service

mcp = FastMCP("chargemate-driver-tools")

ROLE = "driver"


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


def _decimal(value: Any) -> Decimal | None:
    if value is None or value == "":
        return None
    return Decimal(str(value))


# ---------------------------------------------------------------------------
# Discovery
# ---------------------------------------------------------------------------


@guarded
def search_stations(
    city: str | None = None,
    connector_type: str | None = None,
    charging_type: str | None = None,
    min_power_kw: Decimal | str | float | None = None,
    max_price_per_kwh: Decimal | str | float | None = None,
    available_only: bool = False,
    limit: int = 50,
    auth_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Search active charging stations by location, connector, speed, price."""

    with session_scope() as db:
        _context(db, auth_context)
        stations = station_service.search_stations(
            db,
            city=city,
            connector_type=connector_type,
            charging_type=charging_type,
            min_power_kw=_decimal(min_power_kw),
            max_price_per_kwh=_decimal(max_price_per_kwh),
            available_only=available_only,
            limit=limit,
        )
        data = [station_summary(station) for station in stations]
        return ok({"count": len(data), "stations": data})


@guarded
def get_station_details(
    station_id: str,
    auth_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Return a station with its chargers and connectors."""

    with session_scope() as db:
        _context(db, auth_context)
        station = station_service.get_active_station(
            db,
            _uuid(station_id, "station_id"),
        )
        return ok(station_detail(station))


@guarded
def check_station_availability(
    station_id: str,
    auth_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Return database-derived charger availability for a station."""

    with session_scope() as db:
        _context(db, auth_context)
        availability = driver_service.station_availability(
            db,
            _uuid(station_id, "station_id"),
        )
        return ok(availability_summary(availability))


@guarded
def filter_compatible_stations(
    vehicle_id: str | None = None,
    city: str | None = None,
    limit: int = 50,
    auth_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Find stations compatible with a registered vehicle's connector."""

    with session_scope() as db:
        context = _context(db, auth_context)
        matches = driver_service.compatible_stations(
            db,
            context.user_id,
            vehicle_id=_uuid(vehicle_id, "vehicle_id") if vehicle_id else None,
            city=city,
            limit=limit,
        )
        data = [
            {
                "station": station_summary(match["station"]),
                "compatible_charger_ids": [
                    str(charger_id)
                    for charger_id in match["compatible_charger_ids"]
                ],
                "matched_connector_type": match["matched_connector_type"],
            }
            for match in matches
        ]
        return ok({"count": len(data), "stations": data})


# ---------------------------------------------------------------------------
# Preferences and favourites
# ---------------------------------------------------------------------------


@guarded
def get_driver_preferences(
    auth_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Retrieve the authenticated driver's charging preferences."""

    with session_scope() as db:
        context = _context(db, auth_context)
        preference = driver_service.get_or_create_preferences(
            db,
            context.user_id,
        )
        return ok(preference_summary(preference))


@guarded
def update_driver_preferences(
    preferred_connector_type: str | None = None,
    preferred_charging_type: str | None = None,
    max_price_per_kwh: Decimal | str | float | None = None,
    preferred_city: str | None = None,
    default_vehicle_id: str | None = None,
    auth_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Update the authenticated driver's charging preferences."""

    with session_scope() as db:
        context = _context(db, auth_context)

        payload = DriverPreferenceUpdate(
            preferred_connector_type=preferred_connector_type,
            preferred_charging_type=(
                preferred_charging_type.upper()
                if preferred_charging_type
                else None
            ),
            max_price_per_kwh=_decimal(max_price_per_kwh),
            preferred_city=preferred_city,
            default_vehicle_id=(
                _uuid(default_vehicle_id, "default_vehicle_id")
                if default_vehicle_id
                else None
            ),
        )
        preference = driver_service.update_preferences(
            db,
            context.user_id,
            payload,
        )
        return ok(preference_summary(preference))


@guarded
def get_favourite_stations(
    auth_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """List the authenticated driver's favourite stations."""

    with session_scope() as db:
        context = _context(db, auth_context)
        favourites = driver_service.list_favourites(db, context.user_id)
        data = [favourite_summary(item) for item in favourites]
        return ok({"count": len(data), "favourites": data})


@guarded
def add_favourite_station(
    station_id: str,
    auth_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Save a station to the authenticated driver's favourites."""

    with session_scope() as db:
        context = _context(db, auth_context)
        favourite = driver_service.add_favourite(
            db,
            context.user_id,
            _uuid(station_id, "station_id"),
        )
        return ok(favourite_summary(favourite))


@guarded
def remove_favourite_station(
    station_id: str,
    auth_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Remove a station from the authenticated driver's favourites."""

    with session_scope() as db:
        context = _context(db, auth_context)
        driver_service.remove_favourite(
            db,
            context.user_id,
            _uuid(station_id, "station_id"),
        )
        return ok({"station_id": str(station_id), "removed": True})


# ---------------------------------------------------------------------------
# Booking lifecycle
# ---------------------------------------------------------------------------


@guarded
def search_available_slots(
    station_id: str,
    date: str | None = None,
    start_at: str | None = None,
    end_at: str | None = None,
    duration_minutes: int = 30,
    connector_type: str | None = None,
    charging_type: str | None = None,
    max_price_per_kwh: Decimal | str | float | None = None,
    limit: int = 20,
    auth_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Find available charger slots using station, date, and duration."""

    day = None

    if date:
        try:
            day = date_type.fromisoformat(str(date))
        except ValueError as exc:
            raise ValidationError("date must be in YYYY-MM-DD format.") from exc

    with session_scope() as db:
        _context(db, auth_context)
        slots = booking_service.search_available_slots(
            db,
            _uuid(station_id, "station_id"),
            start_at=_datetime(start_at),
            end_at=_datetime(end_at),
            day=day,
            duration_minutes=duration_minutes,
            connector_type=connector_type,
            charging_type=charging_type,
            max_price_per_kwh=_decimal(max_price_per_kwh),
            limit=limit,
        )
        data = [slot_summary(slot) for slot in slots]
        return ok({"count": len(data), "slots": data})


@guarded
def prepare_booking(
    station_id: str,
    charger_id: str,
    start_at: str,
    duration_minutes: int = 30,
    vehicle_id: str | None = None,
    connector_type: str | None = None,
    auth_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Prepare a booking summary; this does not reserve the slot."""

    start = _datetime(start_at)

    if start is None:
        raise ValidationError("start_at is required.")

    with session_scope() as db:
        context = _context(db, auth_context)
        proposal = booking_service.prepare_booking(
            db,
            context.user_id,
            BookingProposalCreate(
                station_id=_uuid(station_id, "station_id"),
                charger_id=_uuid(charger_id, "charger_id"),
                start_at=start,
                duration_minutes=duration_minutes,
                vehicle_id=(
                    _uuid(vehicle_id, "vehicle_id") if vehicle_id else None
                ),
                connector_type=connector_type,
            ),
            conversation_id=context.conversation_id,
        )

        return confirmation_required(
            tool="confirm_booking",
            action="confirm_booking",
            arguments={"proposal_id": str(proposal.id)},
            summary=proposal.summary,
            detail=(
                "Review this booking summary. The slot is not reserved "
                "until the driver explicitly confirms."
            ),
        )


@guarded
def confirm_booking(
    proposal_id: str,
    auth_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Revalidate availability and create the booking after confirmation."""

    with session_scope() as db:
        context = _context(db, auth_context)
        target = _uuid(proposal_id, "proposal_id")

        if not context.approved:
            proposal = booking_service.get_pending_proposal(
                db,
                context.user_id,
                target,
            )
            return confirmation_required(
                tool="confirm_booking",
                action="confirm_booking",
                arguments={"proposal_id": str(target)},
                summary=proposal.summary,
                detail=(
                    "The driver must explicitly confirm this booking in "
                    "the application before it can be created."
                ),
            )

        booking = booking_service.confirm_booking(
            db,
            context.user_id,
            target,
        )
        return ok(
            {
                "booking": booking_summary(booking),
                "message": "Booking confirmed.",
            }
        )


@guarded
def get_my_bookings(
    status: str | None = None,
    upcoming_only: bool = False,
    limit: int = 50,
    auth_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Retrieve the authenticated driver's bookings."""

    with session_scope() as db:
        context = _context(db, auth_context)
        bookings = booking_service.list_bookings(
            db,
            context.user_id,
            status=status,
            upcoming_only=upcoming_only,
            limit=limit,
        )
        data = [booking_summary(booking) for booking in bookings]
        return ok({"count": len(data), "bookings": data})


@guarded
def get_booking_details(
    booking_reference: str,
    auth_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Retrieve details of one of the driver's bookings."""

    with session_scope() as db:
        context = _context(db, auth_context)
        booking = booking_service.get_booking(
            db,
            context.user_id,
            booking_reference,
        )
        return ok(booking_summary(booking))


@guarded
def cancel_booking(
    booking_reference: str,
    auth_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Cancel an eligible upcoming booking owned by the driver."""

    with session_scope() as db:
        context = _context(db, auth_context)

        if not context.approved:
            booking = booking_service.get_booking(
                db,
                context.user_id,
                booking_reference,
            )
            return confirmation_required(
                tool="cancel_booking",
                action="cancel_booking",
                arguments={"booking_reference": booking_reference},
                summary=booking_summary(booking),
                detail=(
                    "Cancelling a booking requires an explicit user "
                    "confirmation in the application."
                ),
            )

        booking = booking_service.cancel_booking(
            db,
            context.user_id,
            booking_reference,
        )
        return ok(
            {
                "booking": booking_summary(booking),
                "message": "Booking cancelled.",
            }
        )


DRIVER_TOOLS = (
    search_stations,
    get_station_details,
    check_station_availability,
    filter_compatible_stations,
    get_driver_preferences,
    update_driver_preferences,
    get_favourite_stations,
    add_favourite_station,
    remove_favourite_station,
    search_available_slots,
    prepare_booking,
    confirm_booking,
    get_my_bookings,
    get_booking_details,
    cancel_booking,
)

for _tool in DRIVER_TOOLS:
    mcp.add_tool(_tool)


if __name__ == "__main__":
    run_server(
        mcp,
        default_host=settings.mcp_driver_host,
        default_port=settings.mcp_driver_port,
    )
