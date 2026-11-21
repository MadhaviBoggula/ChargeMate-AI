from datetime import datetime, timedelta, timezone
from uuid import UUID

from app.models.booking import ChargingBooking
from app.services.time_utils import align_up

from tests.helpers import (
    create_station,
    make_driver,
    make_owner_headers,
)


def vehicle_payload(**overrides):
    payload = {
        "registration_number": "AP16 EV 1234",
        "nickname": "Daily driver",
        "vehicle_model": "Tata Nexon EV",
        "vehicle_type": "car",
        "manufacturing_year": 2024,
        "battery_capacity_kwh": "40.50",
        "connector_type": "CCS2",
    }
    payload.update(overrides)
    return payload


def test_driver_vehicle_crud(client, db_session):
    headers, _ = make_driver(db_session)

    created = client.post(
        "/api/v1/driver/vehicles",
        headers=headers,
        json=vehicle_payload(),
    )

    assert created.status_code == 201, created.text
    body = created.json()

    assert body["connector_type"] == "CCS2"
    assert body["is_primary"] is True

    listed = client.get("/api/v1/driver/vehicles", headers=headers)
    assert listed.status_code == 200
    assert len(listed.json()) == 1

    vehicle_id = body["id"]

    updated = client.patch(
        f"/api/v1/driver/vehicles/{vehicle_id}",
        headers=headers,
        json={"nickname": "Weekend car"},
    )
    assert updated.status_code == 200
    assert updated.json()["nickname"] == "Weekend car"

    deleted = client.delete(
        f"/api/v1/driver/vehicles/{vehicle_id}",
        headers=headers,
    )
    assert deleted.status_code == 204
    assert client.get("/api/v1/driver/vehicles", headers=headers).json() == []


def test_second_vehicle_can_become_primary(client, db_session):
    headers, _ = make_driver(db_session)

    first = client.post(
        "/api/v1/driver/vehicles",
        headers=headers,
        json=vehicle_payload(),
    ).json()

    second = client.post(
        "/api/v1/driver/vehicles",
        headers=headers,
        json=vehicle_payload(
            registration_number="AP16 EV 5678",
            connector_type="Type 2",
        ),
    ).json()

    assert first["is_primary"] is True
    assert second["is_primary"] is False

    promoted = client.patch(
        f"/api/v1/driver/vehicles/{second['id']}",
        headers=headers,
        json={"is_primary": True},
    ).json()

    assert promoted["is_primary"] is True

    vehicles = client.get("/api/v1/driver/vehicles", headers=headers).json()
    primaries = [item for item in vehicles if item["is_primary"]]

    assert len(primaries) == 1
    assert primaries[0]["id"] == second["id"]


def test_driver_cannot_access_another_drivers_vehicle(client, db_session):
    first_headers, _ = make_driver(db_session, "driver-a@example.com")
    second_headers, _ = make_driver(db_session, "driver-b@example.com")

    created = client.post(
        "/api/v1/driver/vehicles",
        headers=first_headers,
        json=vehicle_payload(),
    ).json()

    response = client.get(
        f"/api/v1/driver/vehicles/{created['id']}",
        headers=second_headers,
    )

    assert response.status_code == 404


def test_owner_cannot_use_driver_routes(client, db_session):
    owner_headers = make_owner_headers(db_session)

    response = client.get("/api/v1/driver/vehicles", headers=owner_headers)

    assert response.status_code == 403


def test_preferences_default_and_update(client, db_session):
    headers, _ = make_driver(db_session)

    default = client.get("/api/v1/driver/preferences", headers=headers)

    assert default.status_code == 200
    assert default.json()["preferred_connector_type"] is None

    updated = client.put(
        "/api/v1/driver/preferences",
        headers=headers,
        json={
            "preferred_connector_type": "CCS2",
            "preferred_charging_type": "DC",
            "max_price_per_kwh": "20.00",
            "preferred_city": "Vijayawada",
        },
    )

    assert updated.status_code == 200
    body = updated.json()

    assert body["preferred_connector_type"] == "CCS2"
    assert body["preferred_charging_type"] == "DC"


def test_favourites_add_list_duplicate_and_remove(client, db_session):
    owner_headers = make_owner_headers(db_session)
    driver_headers, _ = make_driver(db_session)
    station = create_station(client, owner_headers)

    added = client.post(
        f"/api/v1/driver/favourites/{station['id']}",
        headers=driver_headers,
    )

    assert added.status_code == 201, added.text
    assert added.json()["station"]["name"] == "ChargeMate Central"

    listed = client.get(
        "/api/v1/driver/favourites",
        headers=driver_headers,
    )
    assert listed.status_code == 200
    assert len(listed.json()) == 1

    duplicate = client.post(
        f"/api/v1/driver/favourites/{station['id']}",
        headers=driver_headers,
    )
    assert duplicate.status_code == 409

    removed = client.delete(
        f"/api/v1/driver/favourites/{station['id']}",
        headers=driver_headers,
    )
    assert removed.status_code == 204

    assert (
        client.get(
            "/api/v1/driver/favourites",
            headers=driver_headers,
        ).json()
        == []
    )


def test_favourite_requires_active_station(client, db_session):
    owner_headers = make_owner_headers(db_session)
    driver_headers, _ = make_driver(db_session)
    station = create_station(client, owner_headers)

    client.delete(
        f"/api/v1/owner/stations/{station['id']}",
        headers=owner_headers,
    )

    response = client.post(
        f"/api/v1/driver/favourites/{station['id']}",
        headers=driver_headers,
    )

    assert response.status_code == 404


def test_compatible_stations_filter_by_vehicle_connector(
    client,
    db_session,
):
    owner_headers = make_owner_headers(db_session)
    driver_headers, _ = make_driver(db_session)

    create_station(
        client,
        owner_headers,
        name="CCS2 Station",
        charger_code="COMP-DC-01",
        connector_type="CCS2",
    )
    create_station(
        client,
        owner_headers,
        name="Type 2 Station",
        charger_code="COMP-AC-01",
        charging_type="AC",
        power_kw="22.00",
        connector_type="Type 2",
    )

    client.post(
        "/api/v1/driver/vehicles",
        headers=driver_headers,
        json=vehicle_payload(),
    )

    response = client.get(
        "/api/v1/driver/compatible-stations",
        headers=driver_headers,
    )

    assert response.status_code == 200
    names = [item["name"] for item in response.json()]

    assert names == ["CCS2 Station"]
    assert response.json()[0]["matched_connector_type"] == "CCS2"


def test_availability_reflects_current_bookings(client, db_session):
    owner_headers = make_owner_headers(db_session)
    driver_headers, driver = make_driver(db_session)
    station = create_station(client, owner_headers)

    charger_id = UUID(station["chargers"][0]["id"])
    now = datetime.now(timezone.utc)

    db_session.add(
        ChargingBooking(
            booking_reference="CM-TEST-000001",
            driver_id=driver.id,
            station_id=UUID(station["id"]),
            charger_id=charger_id,
            connector_type="CCS2",
            start_at=now - timedelta(minutes=10),
            end_at=now + timedelta(minutes=20),
            status="CONFIRMED",
        )
    )
    db_session.commit()

    response = client.get(
        f"/api/v1/stations/{station['id']}/availability",
    )

    assert response.status_code == 200
    charger = response.json()["chargers"][0]

    assert charger["available_now"] is False
    assert charger["booked_until"] is not None


def test_available_slots_exclude_confirmed_bookings(client, db_session):
    owner_headers = make_owner_headers(db_session)
    driver_headers, driver = make_driver(db_session)
    station = create_station(client, owner_headers)

    charger_id = UUID(station["chargers"][0]["id"])
    slot_start = align_up(
        datetime.now(timezone.utc) + timedelta(hours=2),
        30,
        "Asia/Kolkata",
    )
    slot_end = slot_start + timedelta(minutes=30)

    db_session.add(
        ChargingBooking(
            booking_reference="CM-TEST-000002",
            driver_id=driver.id,
            station_id=UUID(station["id"]),
            charger_id=charger_id,
            connector_type="CCS2",
            start_at=slot_start,
            end_at=slot_end,
            status="CONFIRMED",
        )
    )
    db_session.commit()

    response = client.get(
        f"/api/v1/stations/{station['id']}/available-slots",
        params={
            "start_at": slot_start.isoformat(),
            "end_at": (slot_start + timedelta(hours=1)).isoformat(),
        },
    )

    assert response.status_code == 200
    starts = [
        datetime.fromisoformat(item["start_at"]) for item in response.json()
    ]

    assert slot_start not in starts
    assert slot_end in starts
