
def test_register_user(client):
    response = client.post(
        "/api/v1/auth/register",
        json={
            "name": "Test Owner",
            "email": "owner@example.com",
            "password": "TestPassword123",
            "role": "owner",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["name"] == "Test Owner"
    assert data["email"] == "owner@example.com"
    assert data["role"] == "owner"
    assert "password_hash" not in data


def test_duplicate_email_is_rejected(client):
    user_data = {
        "name": "Test Owner",
        "email": "owner@example.com",
        "password": "TestPassword123",
        "role": "owner",
    }

    first_response = client.post(
        "/api/v1/auth/register",
        json=user_data,
    )

    second_response = client.post(
        "/api/v1/auth/register",
        json=user_data,
    )

    assert first_response.status_code == 201
    assert second_response.status_code == 409


def test_login_user(client):
    client.post(
        "/api/v1/auth/register",
        json={
            "name": "Test Driver",
            "email": "driver@example.com",
            "password": "TestPassword123",
            "role": "driver",
        },
    )

    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "driver@example.com",
            "password": "TestPassword123",
        },
    )

    assert response.status_code == 200
    assert "access_token" in response.json()
    assert response.json()["token_type"] == "bearer"


def test_login_with_wrong_password_is_rejected(client):
    client.post(
        "/api/v1/auth/register",
        json={
            "name": "Test Driver",
            "email": "driver@example.com",
            "password": "TestPassword123",
            "role": "driver",
        },
    )

    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "driver@example.com",
            "password": "WrongPassword123",
        },
    )

    assert response.status_code == 401


def test_profile_requires_authentication(client):
    response = client.get("/api/v1/auth/me")

    assert response.status_code == 401


def test_authenticated_user_can_view_profile(client):
    client.post(
        "/api/v1/auth/register",
        json={
            "name": "Test Owner",
            "email": "owner@example.com",
            "password": "TestPassword123",
            "role": "owner",
        },
    )

    login_response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "owner@example.com",
            "password": "TestPassword123",
        },
    )

    token = login_response.json()["access_token"]

    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.json()["email"] == "owner@example.com"
    assert response.json()["role"] == "owner"
