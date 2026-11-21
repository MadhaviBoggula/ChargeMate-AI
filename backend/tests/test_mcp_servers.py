import asyncio
from datetime import datetime, timedelta, timezone

import pytest

from app.mcp import db as mcp_db
from app.mcp import driver_server, owner_server
from app.models.user import User
from app.services.time_utils import align_up
from app.services.token import create_access_token

from tests.helpers import (
    create_station,
    make_driver,
    make_owner_headers,
)

OWNER_TOOL_NAMES = {
    "get_owner_stations",
    "get_station_details",
    "get_charging_sessions",
    "get_station_revenue",
    "get_station_analytics",
    "create_station",
    "update_station",
    "update_charger_status",
    "update_charging_price",
}

DRIVER_TOOL_NAMES = {
    "search_stations",
    "get_station_details",
    "check_station_availability",
    "filter_compatible_stations",
    "get_driver_preferences",
    "update_driver_preferences",
    "get_favourite_stations",
    "add_favourite_station",
    "remove_favourite_station",
    "search_available_slots",
    "prepare_booking",
    "confirm_booking",
    "get_my_bookings",
    "get_booking_details",
    "cancel_booking",
}


@pytest.fixture
def mcp_sessions(session_factory, monkeypatch):
    """Run MCP tools against the same isolated database as the API."""

    monkeypatch.setattr(mcp_db, "mcp_session_factory", session_factory)
    return session_factory


def owner_context(user, approved=False):
    return {
        "user_id": str(user.id),
        "role": "owner",
        "conversation_id": None,
        "approved": approved,
    }


def driver_context(user, approved=False, conversation_id=None):
    return {
        "user_id": str(user.id),
        "role": "driver",
        "conversation_id": (
            str(conversation_id) if conversation_id else None
        ),
        "approved": approved,
    }


def test_owner_server_registers_nine_tools():
    tools = asyncio.run(owner_server.mcp.list_tools())

    assert len(tools) == 9
    assert {tool.name for tool in tools} == OWNER_TOOL_NAMES


def test_driver_server_registers_fifteen_tools():
    tools = asyncio.run(driver_server.mcp.list_tools())

    assert len(tools) == 15
    assert {tool.name for tool in tools} == DRIVER_TOOL_NAMES


def test_tools_reject_missing_auth_context(mcp_sessions):
    result = owner_server.get_owner_stations()

    assert result["status"] == "error"
    assert result["error"] == "unauthorized"


def test_tools_reject_spoofed_role(mcp_sessions, db_session):
    _, driver = make_driver(db_session)

    result = owner_server.get_owner_stations(
        auth_context={
            "user_id": str(driver.id),
            "role": "owner",
            "conversation_id": None,
        }
    )

    assert result["status"] == "error"
    assert result["error"] == "unauthorized"


def test_driver_tool_rejects_owner_identity(mcp_sessions, db_session):
    make_owner_headers(db_session)
    owner = db_session.query(User).filter_by(role="owner").one()

    result = driver_server.get_driver_preferences(
        auth_context={
            "user_id": str(owner.id),
            "role": "driver",
            "conversation_id": None,
        }
    )

    assert result["status"] == "error"
    assert result["error"] == "unauthorized"


def test_owner_creates_station_only_after_confirmation(
    mcp_sessions,
    client,
    db_session,
):
    make_owner_headers(db_session)
    owner = db_session.query(User).filter_by(role="owner").one()

    preview = owner_server.create_station(
        name="MCP Station",
        city="Vijayawada",
        state="Andhra Pradesh",
        pincode="520010",
        chargers=[
            {
                "charger_code": "MCP-DC-01",
                "charging_type": "DC",
                "power_kw": "50.00",
                "price_per_kwh": "17.00",
                "connectors": [
                    {"connector_type": "CCS2", "power_kw": "50.00"}
                ],
            }
        ],
        auth_context=owner_context(owner),
    )

    assert preview["status"] == "confirmation_required"
    request = preview["confirmation_request"]
    assert request["tool"] == "create_station"
    assert request["summary"]["charger_count"] == 1

    listed_before = owner_server.get_owner_stations(
        auth_context=owner_context(owner)
    )
    assert listed_before["data"]["count"] == 0

    created = owner_server.create_station(
        **request["arguments"],
        auth_context=owner_context(owner, approved=True),
    )

    assert created["status"] == "ok"
    assert created["data"]["name"] == "MCP Station"
    assert created["data"]["total_chargers"] == 1

    listed_after = owner_server.get_owner_stations(
        auth_context=owner_context(owner)
    )
    assert listed_after["data"]["count"] == 1


def test_owner_charger_mutations_require_confirmation(
    mcp_sessions,
    client,
    db_session,
):
    owner_headers = make_owner_headers(db_session)
    station = create_station(client, owner_headers)
    charger_id = station["chargers"][0]["id"]
    owner = db_session.query(User).filter_by(role="owner").one()

    status_preview = owner_server.update_charger_status(
        charger_id=charger_id,
        status="maintenance",
        auth_context=owner_context(owner),
    )
    assert status_preview["status"] == "confirmation_required"

    status_done = owner_server.update_charger_status(
        **status_preview["confirmation_request"]["arguments"],
        auth_context=owner_context(owner, approved=True),
    )
    assert status_done["status"] == "ok"
    assert status_done["data"]["status"] == "maintenance"

    price_preview = owner_server.update_charging_price(
        charger_id=charger_id,
        price_per_kwh="15.50",
        auth_context=owner_context(owner),
    )
    assert price_preview["status"] == "confirmation_required"

    price_done = owner_server.update_charging_price(
        **price_preview["confirmation_request"]["arguments"],
        auth_context=owner_context(owner, approved=True),
    )
    assert price_done["status"] == "ok"
    assert price_done["data"]["price_per_kwh"] == "15.50"


def test_owner_cannot_read_another_owners_station(
    mcp_sessions,
    client,
    db_session,
):
    owner_a_headers = make_owner_headers(db_session, "mcp-owner-a@example.com")
    make_owner_headers(db_session, "mcp-owner-b@example.com")

    station = create_station(client, owner_a_headers)

    owner_b = (
        db_session.query(User)
        .filter_by(email="mcp-owner-b@example.com")
        .one()
    )

    result = owner_server.get_station_details(
        station_id=station["id"],
        auth_context=owner_context(owner_b),
    )

    assert result["status"] == "error"
    assert result["error"] == "not_found"


def test_driver_discovery_and_favourites(
    mcp_sessions,
    client,
    db_session,
):
    owner_headers = make_owner_headers(db_session)
    _, driver = make_driver(db_session)
    station = create_station(client, owner_headers)

    context = driver_context(driver)

    search = driver_server.search_stations(
        city="Vijayawada",
        auth_context=context,
    )
    assert search["status"] == "ok"
    assert search["data"]["count"] == 1

    availability = driver_server.check_station_availability(
        station_id=station["id"],
        auth_context=context,
    )
    assert availability["status"] == "ok"
    assert availability["data"]["chargers"][0]["available_now"] is True

    added = driver_server.add_favourite_station(
        station_id=station["id"],
        auth_context=context,
    )
    assert added["status"] == "ok"

    favourites = driver_server.get_favourite_stations(
        auth_context=context
    )
    assert favourites["data"]["count"] == 1

    removed = driver_server.remove_favourite_station(
        station_id=station["id"],
        auth_context=context,
    )
    assert removed["status"] == "ok"

    assert (
        driver_server.get_favourite_stations(auth_context=context)["data"][
            "count"
        ]
        == 0
    )


def test_driver_booking_tools_end_to_end(
    mcp_sessions,
    client,
    db_session,
):
    owner_headers = make_owner_headers(db_session)
    _, driver = make_driver(db_session)
    station = create_station(client, owner_headers)
    charger_id = station["chargers"][0]["id"]
    context = driver_context(driver)

    client.post(
        "/api/v1/driver/vehicles",
        headers={
            "Authorization": "Bearer "
            + create_access_token(str(driver.id), "driver")
        },
        json={
            "registration_number": "AP16 MCP 1111",
            "connector_type": "CCS2",
        },
    )

    compatible = driver_server.filter_compatible_stations(
        auth_context=context
    )
    assert compatible["status"] == "ok"
    assert compatible["data"]["count"] == 1

    slot = align_up(
        datetime.now(timezone.utc) + timedelta(hours=3),
        30,
        "Asia/Kolkata",
    )

    slots = driver_server.search_available_slots(
        station_id=station["id"],
        start_at=slot.isoformat(),
        end_at=(slot + timedelta(hours=1)).isoformat(),
        auth_context=context,
    )
    assert slots["status"] == "ok"
    assert slots["data"]["count"] >= 1

    proposal = driver_server.prepare_booking(
        station_id=station["id"],
        charger_id=charger_id,
        start_at=slot.isoformat(),
        auth_context=context,
    )

    assert proposal["status"] == "confirmation_required"
    request = proposal["confirmation_request"]
    assert request["tool"] == "confirm_booking"
    assert request["summary"]["charger_code"] == "CMC-DC-01"

    unapproved = driver_server.confirm_booking(
        proposal_id=request["arguments"]["proposal_id"],
        auth_context=context,
    )
    assert unapproved["status"] == "confirmation_required"

    confirmed = driver_server.confirm_booking(
        proposal_id=request["arguments"]["proposal_id"],
        auth_context=driver_context(driver, approved=True),
    )

    assert confirmed["status"] == "ok", confirmed
    booking = confirmed["data"]["booking"]
    reference = booking["booking_reference"]

    assert booking["status"] == "CONFIRMED"

    mine = driver_server.get_my_bookings(auth_context=context)
    assert mine["data"]["count"] == 1

    details = driver_server.get_booking_details(
        booking_reference=reference,
        auth_context=context,
    )
    assert details["status"] == "ok"

    cancel_preview = driver_server.cancel_booking(
        booking_reference=reference,
        auth_context=context,
    )
    assert cancel_preview["status"] == "confirmation_required"

    cancelled = driver_server.cancel_booking(
        booking_reference=reference,
        auth_context=driver_context(driver, approved=True),
    )
    assert cancelled["status"] == "ok"
    assert cancelled["data"]["booking"]["status"] == "CANCELLED"


def test_driver_cannot_read_another_drivers_booking(
    mcp_sessions,
    client,
    db_session,
):
    owner_headers = make_owner_headers(db_session)
    _, driver_a = make_driver(db_session, "mcp-driver-a@example.com")
    _, driver_b = make_driver(db_session, "mcp-driver-b@example.com")
    station = create_station(client, owner_headers)

    slot = align_up(
        datetime.now(timezone.utc) + timedelta(hours=4),
        30,
        "Asia/Kolkata",
    )

    proposal = driver_server.prepare_booking(
        station_id=station["id"],
        charger_id=station["chargers"][0]["id"],
        start_at=slot.isoformat(),
        auth_context=driver_context(driver_a),
    )
    proposal_id = proposal["confirmation_request"]["arguments"]["proposal_id"]

    confirmed = driver_server.confirm_booking(
        proposal_id=proposal_id,
        auth_context=driver_context(driver_a, approved=True),
    )
    reference = confirmed["data"]["booking"]["booking_reference"]

    result = driver_server.get_booking_details(
        booking_reference=reference,
        auth_context=driver_context(driver_b),
    )

    assert result["status"] == "error"
    assert result["error"] == "not_found"
