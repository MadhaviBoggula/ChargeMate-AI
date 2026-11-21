import asyncio
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from uuid import UUID

from app.agents.shared.runtime import build_agent_graph
from app.mcp import driver_server
from app.models.booking import ChargingBooking
from app.models.charging_session import ChargingSession
from app.services.token import create_access_token
from app.services.time_utils import align_up

from tests.fakes import FakeLLMClient, build_initial_state
from tests.helpers import (
    TEST_PASSWORD,
    create_station,
    make_driver,
    make_owner_headers,
)


def register(client, email, role):
    response = client.post(
        "/api/v1/auth/register",
        json={
            "name": f"{role.title()} User",
            "email": email,
            "password": TEST_PASSWORD,
            "role": role,
        },
    )
    assert response.status_code == 201, response.text

    login = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": TEST_PASSWORD},
    )
    assert login.status_code == 200

    return {
        "Authorization": f"Bearer {login.json()['access_token']}"
    }, response.json()


def test_driver_journey_discover_book_view_cancel(client):
    owner_headers, _ = register(
        client,
        "e2e-owner@example.com",
        "owner",
    )
    driver_headers, _ = register(
        client,
        "e2e-driver@example.com",
        "driver",
    )

    station = create_station(client, owner_headers)

    vehicle = client.post(
        "/api/v1/driver/vehicles",
        headers=driver_headers,
        json={
            "registration_number": "AP16 E2E 0001",
            "vehicle_model": "Tata Nexon EV",
            "connector_type": "CCS2",
        },
    )
    assert vehicle.status_code == 201

    preferences = client.put(
        "/api/v1/driver/preferences",
        headers=driver_headers,
        json={
            "preferred_connector_type": "CCS2",
            "preferred_charging_type": "DC",
            "max_price_per_kwh": "25.00",
        },
    )
    assert preferences.status_code == 200

    # Discovery
    discovery = client.get(
        "/api/v1/stations",
        params={"city": "Vijayawada", "connector_type": "CCS2"},
    )
    assert discovery.status_code == 200
    assert [item["id"] for item in discovery.json()] == [station["id"]]

    compatible = client.get(
        "/api/v1/driver/compatible-stations",
        headers=driver_headers,
    )
    assert compatible.status_code == 200
    assert compatible.json()[0]["compatible_charger_ids"] == [
        station["chargers"][0]["id"]
    ]

    availability = client.get(
        f"/api/v1/stations/{station['id']}/availability",
    )
    assert availability.status_code == 200
    assert availability.json()["chargers"][0]["available_now"] is True

    favourite = client.post(
        f"/api/v1/driver/favourites/{station['id']}",
        headers=driver_headers,
    )
    assert favourite.status_code == 201

    # Slot search
    slot = align_up(
        datetime.now(timezone.utc) + timedelta(hours=3),
        30,
        "Asia/Kolkata",
    )

    slots = client.get(
        f"/api/v1/stations/{station['id']}/available-slots",
        params={
            "start_at": slot.isoformat(),
            "end_at": (slot + timedelta(hours=1)).isoformat(),
        },
    )
    assert slots.status_code == 200
    assert any(
        datetime.fromisoformat(item["start_at"]) == slot
        for item in slots.json()
    )

    # Proposal -> explicit confirmation -> booking
    proposal = client.post(
        "/api/v1/bookings/proposals",
        headers=driver_headers,
        json={
            "station_id": station["id"],
            "charger_id": station["chargers"][0]["id"],
            "start_at": slot.isoformat(),
            "duration_minutes": 30,
        },
    )
    assert proposal.status_code == 201, proposal.text

    confirmation_id = proposal.json()["confirmation_id"]

    confirmed = client.post(
        f"/api/v1/bookings/{confirmation_id}/confirm",
        headers=driver_headers,
    )
    assert confirmed.status_code == 201, confirmed.text
    reference = confirmed.json()["booking_reference"]

    mine = client.get("/api/v1/bookings", headers=driver_headers)
    assert mine.status_code == 200
    assert [item["booking_reference"] for item in mine.json()] == [reference]

    cancelled = client.post(
        f"/api/v1/bookings/{reference}/cancel",
        headers=driver_headers,
    )
    assert cancelled.status_code == 200
    assert cancelled.json()["status"] == "CANCELLED"

    # The cancelled slot becomes bookable again.
    slots_after = client.get(
        f"/api/v1/stations/{station['id']}/available-slots",
        params={
            "start_at": slot.isoformat(),
            "end_at": (slot + timedelta(hours=1)).isoformat(),
        },
    )
    assert any(
        datetime.fromisoformat(item["start_at"]) == slot
        for item in slots_after.json()
    )


def test_owner_journey_analytics_and_management(client, db_session):
    owner_headers = make_owner_headers(db_session)
    station = create_station(client, owner_headers)
    charger_id = station["chargers"][0]["id"]

    _, driver = make_driver(db_session)
    now = datetime.now(timezone.utc)

    db_session.add(
        ChargingSession(
            station_id=UUID(station["id"]),
            charger_id=UUID(charger_id),
            driver_id=driver.id,
            started_at=now - timedelta(days=1),
            ended_at=now - timedelta(days=1, minutes=-30),
            energy_kwh=Decimal("15.000"),
            duration_minutes=30,
            price_per_kwh=Decimal("18.00"),
            revenue=Decimal("270.00"),
            status="completed",
        )
    )
    db_session.commit()

    stations = client.get("/api/v1/owner/stations", headers=owner_headers)
    assert stations.status_code == 200
    assert len(stations.json()) == 1

    revenue = client.get("/api/v1/owner/revenue", headers=owner_headers)
    assert revenue.status_code == 200
    assert Decimal(str(revenue.json()["total_revenue"])) == Decimal("270.00")

    analytics = client.get("/api/v1/owner/analytics", headers=owner_headers)
    assert analytics.status_code == 200
    assert analytics.json()["session_count"] == 1

    status_update = client.patch(
        f"/api/v1/owner/chargers/{charger_id}/status",
        headers=owner_headers,
        json={"status": "maintenance"},
    )
    assert status_update.status_code == 200
    assert status_update.json()["status"] == "maintenance"

    price_update = client.patch(
        f"/api/v1/owner/chargers/{charger_id}/price",
        headers=owner_headers,
        json={"price_per_kwh": "16.50"},
    )
    assert price_update.status_code == 200
    assert Decimal(str(price_update.json()["price_per_kwh"])) == Decimal(
        "16.50"
    )


class DirectDriverRegistry:
    """In-process registry that calls the real driver MCP tools."""

    async def list_tools(self, role):
        listing = await driver_server.mcp.list_tools()
        return [
            {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description or tool.name,
                    "parameters": tool.inputSchema,
                },
            }
            for tool in listing
        ]

    async def invoke_tool(self, role, name, arguments, context):
        handler = getattr(driver_server, name)
        return handler(**arguments, auth_context=context)


def test_graph_confirmation_executes_real_booking_tool(
    client,
    db_session,
    session_factory,
    monkeypatch,
):
    from app.mcp import db as mcp_db

    monkeypatch.setattr(mcp_db, "mcp_session_factory", session_factory)

    owner_headers = make_owner_headers(db_session)
    station = create_station(client, owner_headers)
    _, driver = make_driver(db_session)

    driver_headers = {
        "Authorization": f"Bearer {create_access_token(str(driver.id), 'driver')}"
    }

    slot = align_up(
        datetime.now(timezone.utc) + timedelta(hours=4),
        30,
        "Asia/Kolkata",
    )

    proposal = client.post(
        "/api/v1/bookings/proposals",
        headers=driver_headers,
        json={
            "station_id": station["id"],
            "charger_id": station["chargers"][0]["id"],
            "start_at": slot.isoformat(),
        },
    ).json()

    pending = {
        "action": "confirm_booking",
        "proposal_id": proposal["confirmation_id"],
        "tool": "confirm_booking",
        "arguments": {"proposal_id": proposal["confirmation_id"]},
        "summary": proposal["summary"],
    }

    graph = build_agent_graph(
        role="driver",
        llm=FakeLLMClient(chat_replies=["Your booking is confirmed."]),
        tool_registry=DirectDriverRegistry(),
        retriever=None,
    )

    state = build_initial_state(
        user_id=str(driver.id),
        role="driver",
        current_request="Confirm my booking",
        pending_confirmation=pending,
        confirmation_action="confirm",
    )

    result = asyncio.run(graph.ainvoke(state))

    assert result["pending_confirmation"] is None
    assert result["tool_results"][0]["status"] == "ok"
    assert (
        result["tool_results"][0]["data"]["booking"]["status"] == "CONFIRMED"
    )

    assert db_session.query(ChargingBooking).count() == 1

    rejected_pending = {
        "action": "confirm_booking",
        "proposal_id": "none",
        "tool": "confirm_booking",
        "arguments": {},
        "summary": {},
    }

    reject_graph = build_agent_graph(
        role="driver",
        llm=FakeLLMClient(chat_replies=["Nothing was booked."]),
        tool_registry=DirectDriverRegistry(),
        retriever=None,
    )

    rejected = asyncio.run(
        reject_graph.ainvoke(
            build_initial_state(
                user_id=str(driver.id),
                role="driver",
                current_request="No, cancel that",
                pending_confirmation=rejected_pending,
                confirmation_action="reject",
            )
        )
    )

    assert rejected["pending_confirmation"] is None
    assert rejected["tool_results"][0]["status"] == "cancelled"
    assert db_session.query(ChargingBooking).count() == 1


def test_chat_persist_keeps_proposal_booking_payload(client, db_session):
    from app.services import booking_service, confirmation_service

    owner_headers = make_owner_headers(db_session)
    station = create_station(client, owner_headers)
    _, driver = make_driver(db_session)

    driver_headers = {
        "Authorization": (
            f"Bearer {create_access_token(str(driver.id), 'driver')}"
        )
    }

    slot = align_up(
        datetime.now(timezone.utc) + timedelta(hours=5),
        30,
        "Asia/Kolkata",
    )

    proposal = client.post(
        "/api/v1/bookings/proposals",
        headers=driver_headers,
        json={
            "station_id": station["id"],
            "charger_id": station["chargers"][0]["id"],
            "start_at": slot.isoformat(),
        },
    ).json()

    conversation = client.post(
        "/api/v1/conversations",
        headers=driver_headers,
        json={"title": "Booking chat"},
    ).json()

    row = confirmation_service.persist_pending(
        db_session,
        driver.id,
        UUID(conversation["id"]),
        {
            "action": "confirm_booking",
            "proposal_id": proposal["confirmation_id"],
            "tool": "confirm_booking",
            "arguments": {"proposal_id": proposal["confirmation_id"]},
            "summary": {},
        },
    )

    # The executable booking payload must survive the chat attaching the
    # proposal to a conversation.
    assert row.arguments["charger_id"] == station["chargers"][0]["id"]
    assert row.arguments["station_id"] == station["id"]
    assert row.conversation_id == UUID(conversation["id"])

    booking = booking_service.confirm_booking(
        db_session,
        driver.id,
        UUID(proposal["confirmation_id"]),
    )

    assert booking.status == "CONFIRMED"


def test_driver_cannot_use_owner_endpoints(client):
    driver, _ = register(client, "e2e-rbac-driver@example.com", "driver")

    response = client.get("/api/v1/owner/stations", headers=driver)

    assert response.status_code == 403
