from app.models.user import UserRole
from app.services.token import create_access_token

from tests.helpers import auth_headers, create_user_directly


def owner_headers(db_session):
    user = create_user_directly(
        db_session,
        name="Discovery Owner",
        email="discovery-owner@example.com",
        role=UserRole.OWNER,
    )
    token = create_access_token(str(user.id), "owner")
    return auth_headers(token)


def make_station(
    client,
    headers,
    *,
    name,
    city,
    charger_code,
    charging_type,
    power_kw,
    price_per_kwh,
    connector_type,
):
    return client.post(
        "/api/v1/owner/stations",
        json={
            "name": name,
            "city": city,
            "state": "Andhra Pradesh",
            "pincode": "520010",
            "latitude": 16.5,
            "longitude": 80.6,
            "chargers": [
                {
                    "charger_code": charger_code,
                    "charging_type": charging_type,
                    "power_kw": power_kw,
                    "price_per_kwh": price_per_kwh,
                    "connectors": [
                        {
                            "connector_type": connector_type,
                            "power_kw": power_kw,
                        }
                    ],
                }
            ],
        },
        headers=headers,
    )


def seed_discovery_stations(client, db_session):
    headers = owner_headers(db_session)

    fast = make_station(
        client,
        headers,
        name="Fast Vijayawada",
        city="Vijayawada",
        charger_code="DISC-DC-01",
        charging_type="DC",
        power_kw="60.00",
        price_per_kwh="18.00",
        connector_type="CCS2",
    )
    slow = make_station(
        client,
        headers,
        name="Slow Guntur",
        city="Guntur",
        charger_code="DISC-AC-01",
        charging_type="AC",
        power_kw="22.00",
        price_per_kwh="10.00",
        connector_type="Type 2",
    )
    hidden = make_station(
        client,
        headers,
        name="Hidden Station",
        city="Vijayawada",
        charger_code="DISC-DC-02",
        charging_type="DC",
        power_kw="90.00",
        price_per_kwh="25.00",
        connector_type="CCS2",
    )

    assert fast.status_code == 201
    assert slow.status_code == 201
    assert hidden.status_code == 201

    deactivated = client.delete(
        f"/api/v1/owner/stations/{hidden.json()['id']}",
        headers=headers,
    )
    assert deactivated.status_code == 204

    return headers, fast.json(), slow.json(), hidden.json()


def test_public_station_discovery_hides_inactive(client, db_session):
    _, fast, slow, _ = seed_discovery_stations(client, db_session)

    response = client.get("/api/v1/stations")

    assert response.status_code == 200
    names = {item["name"] for item in response.json()}
    assert names == {fast["name"], slow["name"]}


def test_public_station_filters(client, db_session):
    _, fast, slow, _ = seed_discovery_stations(client, db_session)

    by_city = client.get("/api/v1/stations?city=Vijayawada")
    assert [item["id"] for item in by_city.json()] == [fast["id"]]

    by_connector = client.get(
        "/api/v1/stations?connector_type=type%202"
    )
    assert [item["id"] for item in by_connector.json()] == [slow["id"]]

    by_charging = client.get("/api/v1/stations?charging_type=AC")
    assert [item["id"] for item in by_charging.json()] == [slow["id"]]

    by_power = client.get("/api/v1/stations?min_power_kw=50")
    assert [item["id"] for item in by_power.json()] == [fast["id"]]

    by_price = client.get("/api/v1/stations?max_price_per_kwh=12")
    assert [item["id"] for item in by_price.json()] == [slow["id"]]

    invalid = client.get("/api/v1/stations?charging_type=HYBRID")
    assert invalid.status_code == 422


def test_public_station_detail_includes_chargers(client, db_session):
    _, fast, _, hidden = seed_discovery_stations(client, db_session)

    detail = client.get(f"/api/v1/stations/{fast['id']}")

    assert detail.status_code == 200
    body = detail.json()
    assert body["id"] == fast["id"]
    assert body["chargers"][0]["charger_code"] == "DISC-DC-01"
    assert body["chargers"][0]["connectors"][0][
        "connector_type"
    ] == "CCS2"

    missing = client.get(f"/api/v1/stations/{hidden['id']}")
    assert missing.status_code == 404


def test_available_only_filter(client, db_session):
    headers, fast, slow, _ = seed_discovery_stations(client, db_session)

    charger_id = fast["chargers"][0]["id"]
    maintenance = client.patch(
        f"/api/v1/owner/chargers/{charger_id}/status",
        json={"status": "maintenance"},
        headers=headers,
    )
    assert maintenance.status_code == 200

    response = client.get("/api/v1/stations?available_only=true")

    assert response.status_code == 200
    ids = {item["id"] for item in response.json()}
    assert fast["id"] not in ids
    assert slow["id"] in ids
