from uuid import UUID

from app.models.conversation import Message, MessageRole


def register_and_login(client, email):
    """Create a test user and return an authentication token."""

    registration = client.post(
        "/api/v1/auth/register",
        json={
            "name": "Test User",
            "email": email,
            "password": "TestPassword123",
            "role": "driver",
        },
    )

    assert registration.status_code == 201

    login = client.post(
        "/api/v1/auth/login",
        json={
            "email": email,
            "password": "TestPassword123",
        },
    )

    assert login.status_code == 200

    return login.json()["access_token"]


def test_create_conversation(client):
    token = register_and_login(
        client,
        "conversation1@example.com",
    )

    response = client.post(
        "/api/v1/conversations",
        headers={"Authorization": f"Bearer {token}"},
        json={"title": "My First Conversation"},
    )

    assert response.status_code == 201

    data = response.json()

    assert data["title"] == "My First Conversation"
    assert "id" in data


def test_list_conversations(client):
    token = register_and_login(
        client,
        "conversation2@example.com",
    )

    headers = {"Authorization": f"Bearer {token}"}

    client.post(
        "/api/v1/conversations",
        headers=headers,
        json={"title": "Conversation One"},
    )

    client.post(
        "/api/v1/conversations",
        headers=headers,
        json={"title": "Conversation Two"},
    )

    response = client.get(
        "/api/v1/conversations",
        headers=headers,
    )

    assert response.status_code == 200
    assert len(response.json()) == 2


def test_retrieve_conversation_history(client, db_session):
    token = register_and_login(
        client,
        "conversation4@example.com",
    )

    headers = {"Authorization": f"Bearer {token}"}

    conversation = client.post(
        "/api/v1/conversations",
        headers=headers,
        json={"title": "Charging Assistance"},
    )

    conversation_id = conversation.json()["id"]

    db_session.add(
        Message(
            conversation_id=UUID(conversation_id),
            role=MessageRole.USER,
            content="Hello, ChargeMate!",
        )
    )
    db_session.commit()

    response = client.get(
        f"/api/v1/conversations/{conversation_id}",
        headers=headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["title"] == "Charging Assistance"
    assert len(data["messages"]) == 1
    assert data["messages"][0]["content"] == "Hello, ChargeMate!"


def test_message_writer_route_is_removed(client):
    """Chat is the only writer of conversation messages."""

    token = register_and_login(
        client,
        "conversation3@example.com",
    )

    headers = {"Authorization": f"Bearer {token}"}

    conversation = client.post(
        "/api/v1/conversations",
        headers=headers,
        json={"title": "EV Charging Help"},
    )

    conversation_id = conversation.json()["id"]

    response = client.post(
        f"/api/v1/conversations/{conversation_id}/messages",
        headers=headers,
        json={
            "role": "user",
            "content": "Find nearby charging stations.",
            "message_type": "text",
        },
    )

    assert response.status_code in {404, 405}


def test_user_cannot_access_another_users_conversation(client):
    first_token = register_and_login(
        client,
        "owner1@example.com",
    )

    second_token = register_and_login(
        client,
        "owner2@example.com",
    )

    first_headers = {"Authorization": f"Bearer {first_token}"}

    second_headers = {"Authorization": f"Bearer {second_token}"}

    conversation = client.post(
        "/api/v1/conversations",
        headers=first_headers,
        json={"title": "Private Conversation"},
    )

    conversation_id = conversation.json()["id"]

    response = client.get(
        f"/api/v1/conversations/{conversation_id}",
        headers=second_headers,
    )

    assert response.status_code == 404


def test_conversation_endpoints_require_authentication(client):
    response = client.get("/api/v1/conversations")

    assert response.status_code == 401
