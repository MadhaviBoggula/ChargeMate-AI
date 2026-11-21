from datetime import datetime, timedelta, timezone
from decimal import Decimal
from uuid import UUID

from app.models.charging_session import ChargingSession
from app.models.user import UserRole
from app.services.token import create_access_token

from tests.helpers import (
    auth_headers,
    create_user_directly,
)


def owner_headers(db_session, email="owner@example.com"):
    user = create_user_directly(
        db_session,
        name="Owner User",
        email=email,
        role=UserRole.OWNER,
    )
    token = create_access_token(str(user.id), "owner")
    return auth_headers(token), user


def station_payload(**overrides):
    payload = {
        "name": "Test Central",
        "description": "A test charging station.",
        "address_line1": "1 Main Road",
        "city": "Vijayawada",
        "state": "Andhra Pradesh",
        "pincode": "520010",
        "latitude": 16.5062,
        "longitude": 80.6480,
        "timezone": "Asia/Kolkata",
        "chargers": [
            {
                "charger_code": "TC-DC-01",
                "charging_type": "DC",
                "power_kw": "60.00",
                "price_per_kwh": "18.00",
                "connectors": [
                    {"connector_type": "CCS2", "power_kw": "60.00"},
                    {"connector_type": "CHAdeMO", "power_kw": "50.00"},
                ],
            }
        ],
    }
    payload.update(overrides)
    return payload


def test_owner_can_create_station_with_chargers(client, db_session):
    headers, _ = owner_headers(db_session)

    response = client.post(
        "/api/v1/owner/stations",
        json=station_payload(),
        headers=headers,
    )

    assert response.status_code == 201
    body = response.json()

    assert body["name"] == "Test Central"
    assert body["city"] == "Vijayawada"
    assert body["timezone"] == "Asia/Kolkata"
    assert body["total_chargers"] == 1
    assert body["available_chargers"] == 1
    assert body["connector_types"] == ["CCS2", "CHAdeMO"]
    assert Decimal(str(body["min_price_per_kwh"])) == Decimal("18.00")
    assert Decimal(str(body["max_power_kw"])) == Decimal("60.00")
    assert len(body["chargers"]) == 1
    assert len(body["chargers"][0]["connectors"]) == 2


def test_owner_station_listing_is_scoped_to_owner(client, db_session):
    owner_a_headers, _ = owner_headers(db_session, "owner-a@example.com")
    owner_b_headers, _ = owner_headers(db_session, "owner-b@example.com")

    created = client.post(
        "/api/v1/owner/stations",
        json=station_payload(),
        headers=owner_a_headers,
    )
    station_id = created.json()["id"]

    list_a = client.get(
        "/api/v1/owner/stations",
        headers=owner_a_headers,
    )
    list_b = client.get(
        "/api/v1/owner/stations",
        headers=owner_b_headers,
    )

    assert list_a.status_code == 200
    assert [item["id"] for item in list_a.json()] == [station_id]

    assert list_b.status_code == 200
    assert list_b.json() == []

    hidden = client.get(
        f"/api/v1/owner/stations/{station_id}",
        headers=owner_b_headers,
    )
    assert hidden.status_code == 404


def test_owner_can_update_and_deactivate_station(client, db_session):
    headers, _ = owner_headers(db_session)

    created = client.post(
        "/api/v1/owner/stations",
        json=station_payload(),
        headers=headers,
    )
    station_id = created.json()["id"]

    updated = client.patch(
        f"/api/v1/owner/stations/{station_id}",
        json={"name": "Renamed Central", "city": "Guntur"},
        headers=headers,
    )

    assert updated.status_code == 200
    assert updated.json()["name"] == "Renamed Central"
    assert updated.json()["city"] == "Guntur"

    deleted = client.delete(
        f"/api/v1/owner/stations/{station_id}",
        headers=headers,
    )
    assert deleted.status_code == 204

    fetched = client.get(
        f"/api/v1/owner/stations/{station_id}",
        headers=headers,
    )
    assert fetched.status_code == 200
    assert fetched.json()["is_active"] is False


def test_owner_can_add_and_configure_charger(client, db_session):
    headers, _ = owner_headers(db_session)

    created = client.post(
        "/api/v1/owner/stations",
        json=station_payload(),
        headers=headers,
    )
    station_id = created.json()["id"]

    added = client.post(
        f"/api/v1/owner/stations/{station_id}/chargers",
        json={
            "charger_code": "TC-AC-02",
            "charging_type": "AC",
            "power_kw": "22.00",
            "price_per_kwh": "11.00",
            "connectors": [
                {"connector_type": "Type 2", "power_kw": "22.00"}
            ],
        },
        headers=headers,
    )

    assert added.status_code == 201
    charger_id = added.json()["id"]
    assert added.json()["connectors"][0]["connector_type"] == "Type 2"

    status_update = client.patch(
        f"/api/v1/owner/chargers/{charger_id}/status",
        json={"status": "maintenance"},
        headers=headers,
    )
    assert status_update.status_code == 200
    assert status_update.json()["status"] == "maintenance"

    price_update = client.patch(
        f"/api/v1/owner/chargers/{charger_id}/price",
        json={"price_per_kwh": "13.50"},
        headers=headers,
    )
    assert price_update.status_code == 200
    assert Decimal(str(price_update.json()["price_per_kwh"])) == Decimal(
        "13.50"
    )

    station = client.get(
        f"/api/v1/owner/stations/{station_id}",
        headers=headers,
    )
    assert station.status_code == 200
    assert station.json()["total_chargers"] == 2
    assert station.json()["available_chargers"] == 1


def test_duplicate_charger_code_is_rejected(client, db_session):
    headers, _ = owner_headers(db_session)

    created = client.post(
        "/api/v1/owner/stations",
        json=station_payload(),
        headers=headers,
    )
    station_id = created.json()["id"]

    duplicate = client.post(
        f"/api/v1/owner/stations/{station_id}/chargers",
        json={
            "charger_code": "TC-DC-01",
            "charging_type": "DC",
            "power_kw": "50.00",
            "connectors": [
                {"connector_type": "CCS2", "power_kw": "50.00"}
            ],
        },
        headers=headers,
    )

    assert duplicate.status_code == 409


def test_owner_revenue_and_analytics_come_from_sessions(
    client,
    db_session,
):
    headers, owner = owner_headers(db_session)

    created = client.post(
        "/api/v1/owner/stations",
        json=station_payload(),
        headers=headers,
    )
    body = created.json()
    station_id = body["id"]
    charger_id = body["chargers"][0]["id"]
    station_uuid = UUID(station_id)
    charger_uuid = UUID(charger_id)

    now = datetime.now(timezone.utc)
    db_session.add_all(
        [
            ChargingSession(
                station_id=station_uuid,
                charger_id=charger_uuid,
                driver_id=None,
                started_at=now - timedelta(days=2),
                ended_at=now - timedelta(days=2, minutes=-30),
                energy_kwh=Decimal("30.000"),
                duration_minutes=30,
                price_per_kwh=Decimal("18.00"),
                revenue=Decimal("540.00"),
                status="completed",
            ),
            ChargingSession(
                station_id=station_uuid,
                charger_id=charger_uuid,
                driver_id=None,
                started_at=now - timedelta(days=1),
                ended_at=now - timedelta(days=1, minutes=-45),
                energy_kwh=Decimal("45.000"),
                duration_minutes=45,
                price_per_kwh=Decimal("18.00"),
                revenue=Decimal("810.00"),
                status="completed",
            ),
            ChargingSession(
                station_id=station_uuid,
                charger_id=charger_uuid,
                driver_id=None,
                started_at=now - timedelta(hours=2),
                ended_at=now - timedelta(hours=1),
                energy_kwh=Decimal("10.000"),
                duration_minutes=60,
                price_per_kwh=Decimal("18.00"),
                revenue=Decimal("180.00"),
                status="failed",
            ),
        ]
    )
    db_session.commit()

    revenue = client.get(
        f"/api/v1/owner/stations/{station_id}/revenue",
        headers=headers,
    )
    assert revenue.status_code == 200
    assert revenue.json()["session_count"] == 2
    assert Decimal(str(revenue.json()["total_revenue"])) == Decimal(
        "1350.00"
    )
    assert Decimal(
        str(revenue.json()["total_energy_kwh"])
    ) == Decimal("75.000")

    network_revenue = client.get(
        "/api/v1/owner/revenue",
        headers=headers,
    )
    assert network_revenue.status_code == 200
    assert Decimal(
        str(network_revenue.json()["total_revenue"])
    ) == Decimal("1350.00")

    analytics = client.get(
        "/api/v1/owner/analytics",
        headers=headers,
    )
    assert analytics.status_code == 200
    analytics_body = analytics.json()
    assert analytics_body["station_count"] == 1
    assert analytics_body["charger_count"] == 1
    assert analytics_body["session_count"] == 2
    assert Decimal(
        str(analytics_body["total_revenue"])
    ) == Decimal("1350.00")
    assert analytics_body["stations"][0]["station_id"] == station_id

    sessions = client.get(
        "/api/v1/owner/sessions",
        headers=headers,
    )
    assert sessions.status_code == 200
    assert len(sessions.json()) == 3

    completed = client.get(
        "/api/v1/owner/sessions?status=completed",
        headers=headers,
    )
    assert completed.status_code == 200
    assert len(completed.json()) == 2


def test_driver_cannot_access_owner_management(client, db_session):
    user = create_user_directly(
        db_session,
        name="Driver User",
        email="driver@example.com",
        role=UserRole.DRIVER,
    )
    token = create_access_token(str(user.id), "driver")
    headers = auth_headers(token)

    response = client.get(
        "/api/v1/owner/stations",
        headers=headers,
    )

    assert response.status_code == 403
