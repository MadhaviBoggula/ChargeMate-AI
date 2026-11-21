from app.models.user import UserRole
from app.services.password import hash_password
from app.services.token import create_access_token


TEST_PASSWORD = "TestPassword123!"


def register_and_login(client, email, role):
    registration = client.post(
        "/api/v1/auth/register",
        json={
            "name": "RBAC Test User",
            "email": email,
            "password": TEST_PASSWORD,
            "role": role,
        },
    )
    assert registration.status_code == 201

    login = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": TEST_PASSWORD},
    )
    assert login.status_code == 200

    return login.json()["access_token"]


def auth_headers(token):
    return {"Authorization": f"Bearer {token}"}


def create_user_directly(
    db_session,
    *,
    name,
    email,
    role: UserRole,
    password: str = TEST_PASSWORD,
):
    from app.models.user import User

    user = User(
        name=name,
        email=email,
        password_hash=hash_password(password),
        role=role,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def make_owner_headers(db_session, email="owner@example.com"):
    user = create_user_directly(
        db_session,
        name="Owner User",
        email=email,
        role=UserRole.OWNER,
    )
    return auth_headers(create_access_token(str(user.id), "owner"))


def make_driver(db_session, email="driver@example.com"):
    user = create_user_directly(
        db_session,
        name="Driver User",
        email=email,
        role=UserRole.DRIVER,
    )
    return auth_headers(create_access_token(str(user.id), "driver")), user


def create_station(
    client,
    headers,
    *,
    name="ChargeMate Central",
    city="Vijayawada",
    charger_code="CMC-DC-01",
    charging_type="DC",
    power_kw="60.00",
    price_per_kwh="18.00",
    connector_type="CCS2",
    timezone="Asia/Kolkata",
):
    response = client.post(
        "/api/v1/owner/stations",
        headers=headers,
        json={
            "name": name,
            "city": city,
            "state": "Andhra Pradesh",
            "pincode": "520010",
            "latitude": 16.5062,
            "longitude": 80.6480,
            "timezone": timezone,
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
    )
    assert response.status_code == 201, response.text
    return response.json()
