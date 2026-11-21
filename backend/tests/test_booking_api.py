from datetime import datetime, timedelta, timezone
from uuid import UUID

from app.models.booking import ChargingBooking
from app.models.pending_confirmation import PendingConfirmation
from app.services.time_utils import align_up

from tests.helpers import (
    create_station,
    make_driver,
    make_owner_headers,
)


def future_slot(hours=3):
    return align_up(
        datetime.now(timezone.utc) + timedelta(hours=hours),
        30,
        "Asia/Kolkata",
    )


def setup_booking_world(client, db_session, connector_type="CCS2"):
    owner_headers = make_owner_headers(db_session)
    driver_headers, driver = make_driver(db_session)
    station = create_station(
        client,
        owner_headers,
        connector_type=connector_type,
    )
    charger = station["chargers"][0]

    return {
        "owner": owner_headers,
        "headers": driver_headers,
        "driver": driver,
        "station": station,
        "charger": charger,
    }


def proposal_payload(world, start_at, **overrides):
    payload = {
        "station_id": world["station"]["id"],
        "charger_id": world["charger"]["id"],
        "start_at": start_at.isoformat(),
        "duration_minutes": 30,
    }
    payload.update(overrides)
    return payload


def test_proposal_does_not_reserve_and_slot_stays_available(
    client,
    db_session,
):
    world = setup_booking_world(client, db_session)
    slot = future_slot()

    proposal = client.post(
        "/api/v1/bookings/proposals",
        headers=world["headers"],
        json=proposal_payload(world, slot),
    )

    assert proposal.status_code == 201, proposal.text
    body = proposal.json()

    assert body["status"] == "pending"
    assert body["confirmation_id"]
    assert body["summary"]["station_name"] == "ChargeMate Central"
    assert body["summary"]["charger_code"] == "CMC-DC-01"

    assert (
        db_session.query(ChargingBooking).count() == 0
    ), "A proposal must not create a booking"

    slots = client.get(
        f"/api/v1/stations/{world['station']['id']}/available-slots",
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


def test_confirm_creates_booking_with_reference(client, db_session):
    world = setup_booking_world(client, db_session)
    slot = future_slot()

    proposal = client.post(
        "/api/v1/bookings/proposals",
        headers=world["headers"],
        json=proposal_payload(world, slot),
    ).json()

    confirmed = client.post(
        f"/api/v1/bookings/{proposal['confirmation_id']}/confirm",
        headers=world["headers"],
    )

    assert confirmed.status_code == 201, confirmed.text
    booking = confirmed.json()

    assert booking["status"] == "CONFIRMED"
    assert booking["booking_reference"].startswith("CM-")
    assert booking["charger_code"] == "CMC-DC-01"
    assert booking["timezone"] == "Asia/Kolkata"
    assert booking["local_start"]

    fetched = client.get(
        f"/api/v1/bookings/{booking['booking_reference']}",
        headers=world["headers"],
    )
    assert fetched.status_code == 200
    assert fetched.json()["booking_reference"] == booking["booking_reference"]

    replay = client.post(
        f"/api/v1/bookings/{proposal['confirmation_id']}/confirm",
        headers=world["headers"],
    )
    assert replay.status_code == 409


def test_confirm_rejects_another_drivers_proposal(client, db_session):
    world = setup_booking_world(client, db_session)
    other_headers, _ = make_driver(db_session, "other-driver@example.com")
    slot = future_slot()

    proposal = client.post(
        "/api/v1/bookings/proposals",
        headers=world["headers"],
        json=proposal_payload(world, slot),
    ).json()

    response = client.post(
        f"/api/v1/bookings/{proposal['confirmation_id']}/confirm",
        headers=other_headers,
    )

    assert response.status_code == 404


def test_conflict_when_slot_is_already_booked(client, db_session):
    world = setup_booking_world(client, db_session)
    slot = future_slot()

    proposal = client.post(
        "/api/v1/bookings/proposals",
        headers=world["headers"],
        json=proposal_payload(world, slot),
    ).json()

    client.post(
        f"/api/v1/bookings/{proposal['confirmation_id']}/confirm",
        headers=world["headers"],
    )

    second = client.post(
        "/api/v1/bookings/proposals",
        headers=world["headers"],
        json=proposal_payload(world, slot),
    )

    assert second.status_code == 409


def test_expired_proposal_cannot_be_confirmed(client, db_session):
    world = setup_booking_world(client, db_session)
    slot = future_slot()

    proposal = client.post(
        "/api/v1/bookings/proposals",
        headers=world["headers"],
        json=proposal_payload(world, slot),
    ).json()

    row = db_session.get(
        PendingConfirmation,
        UUID(proposal["confirmation_id"]),
    )
    row.expires_at = datetime.now(timezone.utc) - timedelta(minutes=1)
    db_session.commit()

    response = client.post(
        f"/api/v1/bookings/{proposal['confirmation_id']}/confirm",
        headers=world["headers"],
    )

    assert response.status_code == 409
    assert "expired" in response.json()["detail"].lower()


def test_cancel_upcoming_booking(client, db_session):
    world = setup_booking_world(client, db_session)
    slot = future_slot(hours=5)

    proposal = client.post(
        "/api/v1/bookings/proposals",
        headers=world["headers"],
        json=proposal_payload(world, slot),
    ).json()

    booking = client.post(
        f"/api/v1/bookings/{proposal['confirmation_id']}/confirm",
        headers=world["headers"],
    ).json()

    cancelled = client.post(
        f"/api/v1/bookings/{booking['booking_reference']}/cancel",
        headers=world["headers"],
    )

    assert cancelled.status_code == 200
    assert cancelled.json()["status"] == "CANCELLED"
    assert cancelled.json()["cancelled_at"] is not None

    again = client.post(
        f"/api/v1/bookings/{booking['booking_reference']}/cancel",
        headers=world["headers"],
    )
    assert again.status_code == 409


def test_cancel_inside_cutoff_is_rejected(client, db_session):
    world = setup_booking_world(client, db_session)
    now = datetime.now(timezone.utc)

    db_session.add(
        ChargingBooking(
            booking_reference="CM-CUTOFF-0001",
            driver_id=world["driver"].id,
            station_id=UUID(world["station"]["id"]),
            charger_id=UUID(world["charger"]["id"]),
            connector_type="CCS2",
            start_at=now + timedelta(minutes=10),
            end_at=now + timedelta(minutes=40),
            status="CONFIRMED",
        )
    )
    db_session.commit()

    response = client.post(
        "/api/v1/bookings/CM-CUTOFF-0001/cancel",
        headers=world["headers"],
    )

    assert response.status_code == 409
    assert "30 minutes" in response.json()["detail"]


def test_cancel_another_drivers_booking_is_not_found(client, db_session):
    world = setup_booking_world(client, db_session)
    other_headers, _ = make_driver(db_session, "cancel-other@example.com")
    slot = future_slot(hours=5)

    proposal = client.post(
        "/api/v1/bookings/proposals",
        headers=world["headers"],
        json=proposal_payload(world, slot),
    ).json()

    booking = client.post(
        f"/api/v1/bookings/{proposal['confirmation_id']}/confirm",
        headers=world["headers"],
    ).json()

    response = client.post(
        f"/api/v1/bookings/{booking['booking_reference']}/cancel",
        headers=other_headers,
    )

    assert response.status_code == 404


def test_incompatible_vehicle_is_rejected(client, db_session):
    world = setup_booking_world(client, db_session)
    slot = future_slot()

    vehicle = client.post(
        "/api/v1/driver/vehicles",
        headers=world["headers"],
        json={
            "registration_number": "AP16 EV 9999",
            "connector_type": "Type 2",
        },
    ).json()

    response = client.post(
        "/api/v1/bookings/proposals",
        headers=world["headers"],
        json=proposal_payload(
            world,
            slot,
            vehicle_id=vehicle["id"],
        ),
    )

    assert response.status_code in {400, 409}


def test_booking_must_start_on_slot_boundary(client, db_session):
    world = setup_booking_world(client, db_session)
    slot = future_slot() + timedelta(minutes=7)

    response = client.post(
        "/api/v1/bookings/proposals",
        headers=world["headers"],
        json=proposal_payload(world, slot),
    )

    assert response.status_code == 400


def test_booking_in_past_is_rejected(client, db_session):
    world = setup_booking_world(client, db_session)
    slot = align_up(
        datetime.now(timezone.utc) - timedelta(hours=2),
        30,
        "Asia/Kolkata",
    )

    response = client.post(
        "/api/v1/bookings/proposals",
        headers=world["headers"],
        json=proposal_payload(world, slot),
    )

    assert response.status_code == 400


def test_inactive_charger_cannot_be_booked(client, db_session):
    world = setup_booking_world(client, db_session)
    slot = future_slot()

    client.patch(
        f"/api/v1/owner/chargers/{world['charger']['id']}/status",
        headers=world["owner"],
        json={"status": "maintenance"},
    )

    response = client.post(
        "/api/v1/bookings/proposals",
        headers=world["headers"],
        json=proposal_payload(world, slot),
    )

    assert response.status_code == 409


def test_booking_list_and_upcoming_filter(client, db_session):
    world = setup_booking_world(client, db_session)
    slot = future_slot(hours=4)

    proposal = client.post(
        "/api/v1/bookings/proposals",
        headers=world["headers"],
        json=proposal_payload(world, slot),
    ).json()

    booking = client.post(
        f"/api/v1/bookings/{proposal['confirmation_id']}/confirm",
        headers=world["headers"],
    ).json()

    listed = client.get("/api/v1/bookings", headers=world["headers"])
    assert listed.status_code == 200
    assert len(listed.json()) == 1

    upcoming = client.get(
        "/api/v1/bookings",
        params={"upcoming_only": True},
        headers=world["headers"],
    )
    assert [item["booking_reference"] for item in upcoming.json()] == [
        booking["booking_reference"]
    ]

    filtered = client.get(
        "/api/v1/bookings",
        params={"status": "CANCELLED"},
        headers=world["headers"],
    )
    assert filtered.json() == []


def test_owner_cannot_use_booking_routes(client, db_session):
    world = setup_booking_world(client, db_session)

    response = client.get(
        "/api/v1/bookings",
        headers=world["owner"],
    )

    assert response.status_code == 403
