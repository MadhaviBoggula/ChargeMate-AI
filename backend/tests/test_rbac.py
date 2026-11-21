def register_and_login(client, email, role):
    registration = client.post(
        "/api/v1/auth/register",
        json={
            "name": "RBAC Test User",
            "email": email,
            "password": "TestPassword123",
            "role": role,
        },
    )
    assert registration.status_code == 201

    login = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "TestPassword123"},
    )
    assert login.status_code == 200

    return login.json()["access_token"]


def test_driver_cannot_access_owner_routes(client):
    token = register_and_login(client, "rbac-driver@example.com", "driver")

    response = client.get(
        "/api/v1/owner/stations",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 403


def test_owner_can_access_owner_routes(client):
    token = register_and_login(client, "rbac-owner@example.com", "owner")

    response = client.get(
        "/api/v1/owner/stations",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.json() == []


def test_role_claim_is_required_in_token(client):
    token = register_and_login(client, "rbac-claim@example.com", "owner")

    from app.services.token import decode_access_token

    payload = decode_access_token(token)

    assert payload is not None
    assert payload["role"] == "owner"


def test_token_role_must_match_database_role(client):
    token = register_and_login(client, "rbac-mismatch@example.com", "owner")

    from app.services.token import (
        create_access_token,
        decode_access_token,
    )

    payload = decode_access_token(token)
    forged = create_access_token(payload["sub"], "driver")

    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {forged}"},
    )

    assert response.status_code == 401
